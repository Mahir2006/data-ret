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
    print("Fetching live Nifty 500 constituents from NSE...")
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
            print(f"Failed to fetch NSE data. Status: {response.status_code}")
            return []
            
        df = pd.read_csv(io.StringIO(response.text))
        
        # Filter out dummy demerger tickers
        df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
        
        # Append ".NS" to the NSE symbols so yfinance can read them
        return (df['Symbol'].astype(str) + ".NS").tolist()
        
    except Exception as e:
        print(f"Error fetching NSE list: {e}")
        return []

# ─── 2. DATA EXTRACTION & RETURN CALCULATION ───────────────────────────────────
def fetch_market_data():
    # Dynamically pull the symbol universe
    universe_symbols = get_live_nifty_500()
    
    if not universe_symbols:
        print("Fatal Error: Could not fetch Nifty 500 list from NSE. Exiting.")
        return

    results = {}
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download))

    try:
        print(f"Downloading data for {len(all_tickers)} individual tickers...\n")
        chunk_size = 50
        closes_dict = {}
        
        for i in range(0, len(all_tickers), chunk_size):
            chunk = all_tickers[i:i + chunk_size]
            print(f"Fetching batch {(i//chunk_size) + 1}/{(len(all_tickers)//chunk_size) + 1}...")
            
            # Period="4mo" is correct here for 3-month lookback
            df = yf.download(chunk, period="4mo", interval="1d", progress=False, threads=False)
            
            if df.empty:
                continue
                
            # Dictionary extraction bypasses MultiIndex column alignment bugs
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
            
        # Rebuild a perfectly clean DataFrame from the dictionary
        closes = pd.DataFrame(closes_dict)
        closes.index = pd.to_datetime(closes.index).normalize()
        closes = closes.ffill().dropna(how='all')
        valid_downloaded_symbols = set(closes.columns)

        print(f"\n{'Symbol':<18} | {'1-Week Return':<15} | {'3-Month Return':<15}")
        print("-" * 55)
        
        for react_symbol in universe_symbols:
            try:
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                if yahoo_symbol not in valid_downloaded_symbols:
                    print(f"{react_symbol:<18} | {'DROPPED (API Block / Delisted)':<28}")
                    continue
                
                col = closes[yahoo_symbol].dropna()
                
                if len(col) < 5:
                    print(f"{react_symbol:<18} | {'DROPPED (< 5 days of data)':<28}")
                    continue 
                    
                current_date = col.index[-1]
                current_price = col.iloc[-1]
                
                target_1w = current_date - pd.Timedelta(days=7) 
                target_3m = current_date - pd.DateOffset(months=3) 
                
                price_1w = col.asof(target_1w)
                price_3m = col.asof(target_3m)
                
                if pd.isna(price_1w) or pd.isna(price_3m):
                    print(f"{react_symbol:<18} | {'DROPPED (Not enough history)':<28}")
                    continue 
                
                ret1w = ((current_price - price_1w) / price_1w) * 100
                ret3m = ((current_price - price_3m) / price_3m) * 100
                
                results[react_symbol] = {
                    "ret1w": round(float(ret1w), 2),
                    "ret3m": round(float(ret3m), 2)
                }
                
                print(f"{react_symbol:<18} | {results[react_symbol]['ret1w']:>13} % | {results[react_symbol]['ret3m']:>13} %")
                
            except Exception as e:
                print(f"{react_symbol:<18} | ERROR: {str(e)}")
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile, indent=4)
            
        print(f"\nSuccessfully generated market_data.json with {len(results)} active symbols.")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
