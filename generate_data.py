import yfinance as yf
import pandas as pd
import json
import time
import requests
import io

# Edge-case mappings for Yahoo Finance ticker mismatches
YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
    "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
    "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
    "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS"
}

# ─── 1. FETCH LIVE NIFTY 500 FROM NSE ───────────────────────────────────────────
def get_live_nifty_500():
    url = "https://niftyindices.com/Indexconstituent/ind_nifty500list.csv"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return [], {}
            
        df = pd.read_csv(io.StringIO(response.text))
        df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
        
        symbols = (df['Symbol'].astype(str) + ".NS").tolist()
        
        # Build metadata map directly from the CSV
        metadata = {}
        for _, row in df.iterrows():
            sym = str(row['Symbol']) + ".NS"
            metadata[sym] = {
                "name": str(row.get('Company Name', sym)),
                "sector": str(row.get('Industry', 'Uncategorized')).strip()
            }
            
        return symbols, metadata
        
    except Exception as e:
        print(f"Error fetching live index data: {e}")
        return [], {}

# ─── 2. DATA EXTRACTION & EXACT JSON FORMATTING ─────────────────────────────────
def fetch_market_data():
    universe_symbols, metadata = get_live_nifty_500()
    
    if not universe_symbols:
        print("Fatal Error: Could not fetch Nifty 500 list from NSE. Exiting.")
        return
        
    # EXPLICITLY INJECT NIFTY 50 BENCHMARK FOR THE REACT DASHBOARD
    if "^NSEI" not in universe_symbols:
        universe_symbols.insert(0, "^NSEI")
        metadata["^NSEI"] = {"name": "NIFTY 50", "sector": "Benchmark"}

    results = {}
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download))

    try:
        print(f"Downloading data for {len(all_tickers)} symbols...")
        chunk_size = 50
        closes_dict = {}
        
        for i in range(0, len(all_tickers), chunk_size):
            chunk = all_tickers[i:i + chunk_size]
            
            # Period="4mo" to guarantee we have data exactly 3 calendar months back
            df = yf.download(chunk, period="4mo", interval="1d", progress=False, threads=False)
            
            if df.empty:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                if 'Close' in df.columns.get_level_values(0):
                    c = df['Close']
                else:
                    c = df.xs('Close', level=1, axis=1)
                
                for sym in c.columns:
                    closes_dict[sym] = c[sym]
            else:
                if 'Close' in df.columns and len(chunk) == 1:
                    closes_dict[chunk[0]] = df['Close']
            
            time.sleep(1.5) 
            
        if not closes_dict:
            print("\nFatal Error: All downloads were blocked or empty.")
            return
            
        closes = pd.DataFrame(closes_dict)
        closes.index = pd.to_datetime(closes.index).normalize()
        closes = closes.ffill().dropna(how='all')
        valid_downloaded_symbols = set(closes.columns)

        for react_symbol in universe_symbols:
            try:
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                if yahoo_symbol not in valid_downloaded_symbols:
                    continue
                
                col = closes[yahoo_symbol].dropna()
                
                if len(col) < 5:
                    continue 
                    
                current_date = col.index[-1]
                current_price = col.iloc[-1]
                
                target_1w = current_date - pd.Timedelta(days=7) 
                target_3m = current_date - pd.DateOffset(months=3) 
                
                price_1w = col.asof(target_1w)
                price_3m = col.asof(target_3m)
                
                if pd.isna(price_1w) or pd.isna(price_3m):
                    continue 
                
                ret1w = ((current_price - price_1w) / price_1w) * 100
                ret3m = ((current_price - price_3m) / price_3m) * 100
                
                # Fetch metadata to inject into JSON
                stock_meta = metadata.get(react_symbol, {"name": react_symbol, "sector": "Uncategorized"})
                
                # Save dynamically enriched JSON structure
                results[react_symbol] = {
                    "name": stock_meta["name"],
                    "sector": stock_meta["sector"],
                    "ret1w": round(float(ret1w), 2),
                    "ret3m": round(float(ret3m), 2)
                }
                
            except Exception:
                pass
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile)
            
        print(f"Successfully generated market_data.json with {len(results)} records.")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
