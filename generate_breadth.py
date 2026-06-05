import os
import json
import time
import requests
import io
import pandas as pd
import yfinance as yf

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

# ─── 2. BREADTH DATA CALCULATION ───────────────────────────────────────────────
def generate_breadth_data():
    universe_symbols = get_live_nifty_500()
    
    if not universe_symbols:
        print("Fatal Error: Could not fetch Nifty 500 list from NSE. Exiting.")
        return

    print("Starting TRUE market breadth calculation (Dynamic 500-stock universe)...")
    
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download)) + ["^NSEI"]

    try:
        print(f"Downloading data for {len(all_tickers)} individual tickers...\n")
        chunk_size = 50
        closes_dict = {}
        
        for i in range(0, len(all_tickers), chunk_size):
            chunk = all_tickers[i:i + chunk_size]
            print(f"Fetching batch {(i//chunk_size) + 1}/{(len(all_tickers)//chunk_size) + 1}...")
            
            # FIXED: Changed from 6mo to 1y. 6 months is only ~125 trading days.
            # You MUST have at least 200 trading days for the 200 SMA to not return NaN.
            df = yf.download(chunk, period="1y", interval="1d", progress=False, threads=False)
            
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
            
        closes = pd.DataFrame(closes_dict)
        closes.index = pd.to_datetime(closes.index).normalize()
        closes = closes.ffill().dropna(how='all')

    except Exception as e:
        print(f"Error downloading data from yfinance: {e}")
        return

    advancers = 0
    decliners = 0
    above_sma50 = 0
    above_sma200 = 0
    total_tracked = 0
    
    for react_symbol in universe_symbols:
        yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
        
        if yahoo_symbol not in closes.columns:
            continue
            
        series = closes[yahoo_symbol].dropna()
        
        if len(series) < 5: 
            continue
            
        total_tracked += 1
        current_price = series.iloc[-1]
        previous_price = series.iloc[-2]
        
        if current_price > previous_price:
            advancers += 1
        elif current_price < previous_price:
            decliners += 1
            
        if len(series) >= 50:
            sma50 = series.rolling(window=50).mean().iloc[-1]
            if current_price > sma50:
                above_sma50 += 1
                
        if len(series) >= 200:
            sma200 = series.rolling(window=200).mean().iloc[-1]
            if current_price > sma200:
                above_sma200 += 1

    if total_tracked == 0:
        print("Error: No valid ticker data processed.")
        return

    print(f"\nSuccessfully processed {total_tracked} active stocks for breadth.")

    pct_above_sma50 = round((above_sma50 / total_tracked) * 100, 2)
    pct_above_sma200 = round((above_sma200 / total_tracked) * 100, 2)

    overall = {
        "advancers": advancers,
        "decliners": decliners,
        "unchanged": total_tracked - advancers - decliners,
        "totalStocks": total_tracked,
        "pctAboveSMA50": pct_above_sma50,
        "pctAboveSMA200": pct_above_sma200,
    }

    # Benchmark Performance Calculations (Exact Calendar Dates)
    nifty = closes.get('^NSEI')
    if nifty is not None and not nifty.isna().all():
        nifty = nifty.dropna()
        n_curr = nifty.iloc[-1]        
        current_date = nifty.index[-1] 
        
        target_1w = current_date - pd.Timedelta(days=7)
        target_1m = current_date - pd.DateOffset(months=1)
        
        n_1w = nifty.asof(target_1w)
        n_1m = nifty.asof(target_1m)
        
        overall["nifty500Change1W"] = round(((n_curr - n_1w) / n_1w) * 100, 2)
        overall["nifty500Change1M"] = round(((n_curr - n_1m) / n_1m) * 100, 2)
        
        n_ema50 = nifty.ewm(span=50).mean().iloc[-1]
        n_ema200 = nifty.ewm(span=200).mean().iloc[-1]
        overall["goldenCross"] = bool(n_ema50 > n_ema200)
        overall["deathCross"] = bool(n_ema50 < n_ema200)
    else:
        overall["nifty500Change1W"] = 0
        overall["nifty500Change1M"] = 0
        overall["goldenCross"] = False
        overall["deathCross"] = False
        print("Warning: Benchmark Nifty 50 (^NSEI) data was missing.")

    output_filename = "breadth_data.json"
    try:
        with open(output_filename, "w") as f:
            json.dump(overall, f, indent=4)
        print(f"Success! Data saved to {output_filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    generate_breadth_data()
