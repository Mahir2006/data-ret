import yfinance as yf
import pandas as pd
import json
import time
import requests
import io
import datetime
import calendar

# Edge-case mappings for Yahoo Finance ticker mismatches
YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
    "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
    "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
    "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS"
}

def track(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_live_nifty_500():
    track("Fetching live Nifty 500 constituents and metadata from NSE...")
    urls = [
        "https://niftyindices.com/Indexconstituent/ind_nifty500list.csv",
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    csv_payload = None
    
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
                csv_payload = response.text
                break
        except requests.exceptions.RequestException:
            continue
            
    if not csv_payload: 
        track("❌ FATAL: Could not fetch Nifty 500 list.")
        return [], {}

    df = pd.read_csv(io.StringIO(csv_payload))
    df.columns = df.columns.str.strip()
    df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
    symbols = (df['Symbol'].astype(str) + ".NS").tolist()
    
    metadata = {}
    for _, row in df.iterrows():
        sym = str(row['Symbol']).strip() + ".NS"
        metadata[sym] = {
            "name": str(row.get('Company Name', sym)).strip(),
            "sector": str(row.get('Industry', 'Uncategorized')).strip()
        }
    return symbols, metadata

def generate_seasonality():
    universe_symbols, metadata = get_live_nifty_500()
    if not universe_symbols: return

    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download))

    # Explicit 10-year date range is more stable than period="10y"
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365 * 10)

    track(f"Downloading historical data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    closes_dict = {}
    chunk_size = 20 
    
    for i in range(0, len(all_tickers), chunk_size):
        chunk = all_tickers[i:i + chunk_size]
        track(f"--> Fetching chunk {i} to {i + len(chunk)}...")
        
        try:
            # Removed custom session. Let yfinance handle its own authentication/cookies.
            df = yf.download(chunk, start=start_date, end=end_date, interval="1d", threads=False, progress=False)
            
            if df.empty: 
                track(f"⚠️ Chunk returned empty. Sleeping...")
                time.sleep(3)
                continue
            
            # Robust extraction of Adj Close (or Close as fallback)
            target_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
            
            if isinstance(df.columns, pd.MultiIndex):
                if target_col in df.columns.get_level_values(0):
                    c = df[target_col]
                elif target_col in df.columns.get_level_values(1):
                    c = df.xs(target_col, level=1, axis=1)
                else: continue
                
                if isinstance(c, pd.DataFrame):
                    for sym in c.columns: 
                        closes_dict[sym] = c[sym]
                elif isinstance(c, pd.Series):
                    closes_dict[c.name] = c
            else:
                if target_col in df.columns and len(chunk) == 1:
                    closes_dict[chunk[0]] = df[target_col]
                    
        except Exception as e:
            track(f"⚠️ Error on chunk {i}: {e}")
            
        time.sleep(3) # Let Yahoo breathe

    closes = pd.DataFrame(closes_dict)
    
    if closes.empty:
        track("❌ FATAL: No data was successfully downloaded.")
        return

    # Print shape to verify we actually got 10 years (~2500 rows)
    track(f"✅ Data downloaded! Closes DataFrame Shape: {closes.shape} (Rows, Columns)")

    if hasattr(closes.index, 'tz') and closes.index.tz is not None:
        closes.index = closes.index.tz_localize(None)
        
    closes.index = pd.to_datetime(closes.index).normalize()
    closes = closes.ffill().dropna(how='all')

    monthly_data = closes.resample('ME').last()
    monthly_returns = monthly_data.pct_change().dropna() * 100

    results = []
    valid_cols = list(closes.columns)
    
    track(f"Calculating seasonality metrics for {len(valid_cols)} symbols...")
    
    for react_sym in universe_symbols:
        yahoo_sym = YAHOO_MAP.get(react_sym, react_sym)
        if yahoo_sym not in valid_cols: continue
        
        col_rets = monthly_returns[yahoo_sym].dropna()
        # Require at least 5 years (60 months) of history
        if len(col_rets) < 60: 
            continue 
        
        df_months = pd.DataFrame({'Return': col_rets})
        df_months['Month'] = df_months.index.month
        
        seasonality = df_months.groupby('Month').agg(
            avgReturn=('Return', 'mean'),
            winRate=('Return', lambda x: (x > 0).mean() * 100)
        )
        seasonality.index = [calendar.month_abbr[i] for i in seasonality.index]
        
        meta = metadata.get(react_sym, {"name": react_sym, "sector": "Uncategorized"})
        
        results.append({
            "symbol": react_sym.replace(".NS", ""),
            "name": meta["name"],
            "sector": meta["sector"],
            "months": {
                k: {
                    "winRate": round(v['winRate'], 1), 
                    "avgReturn": round(v['avgReturn'], 2)
                } for k, v in seasonality.to_dict('index').items()
            }
        })

    output = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stocks": results
    }

    with open("seasonality_data.json", "w") as outfile:
        json.dump(output, outfile)
    track("🎉 DONE! Seasonality JSON generated successfully.")

if __name__ == "__main__":
    generate_seasonality()
