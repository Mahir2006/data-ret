import yfinance as yf
import pandas as pd
import json
import time
import requests
import io
import datetime
import calendar
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
    "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
    "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
    "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS"
}

def get_live_nifty_500():
    print("Fetching live Nifty 500 constituents and metadata from NSE...")
    urls = [
        "https://niftyindices.com/Indexconstituent/ind_nifty500list.csv",
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    session = requests.Session()
    retry_strategy = Retry(total=3, backoff_factor=2, status_forcelist=[403, 429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(headers)
    
    csv_payload = None
    for url in urls:
        try:
            response = session.get(url, timeout=20)
            if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
                csv_payload = response.text
                break
        except requests.exceptions.RequestException:
            continue
            
    if not csv_payload: return [], {}

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

    print(f"Downloading 10-year historical data for {len(all_tickers)} symbols...")
    closes_dict = {}
    
    # 20 stocks at a time is the sweet spot for evading Azure IP limits
    chunk_size = 20 
    
    for i in range(0, len(all_tickers), chunk_size):
        chunk = all_tickers[i:i + chunk_size]
        
        try:
            # auto_adjust=True gives us clean Adjusted Close prices natively
            # threads=False prevents the parallel request burst that triggers the ban
            df = yf.download(chunk, period="10y", interval="1d", auto_adjust=True, threads=False, progress=False)
            
            if df.empty: 
                time.sleep(3)
                continue
            
            # Since auto_adjust is True, 'Close' is automatically the Adjusted Close
            if isinstance(df.columns, pd.MultiIndex):
                if 'Close' in df.columns.get_level_values(0):
                    c = df['Close']
                elif 'Close' in df.columns.get_level_values(1):
                    c = df.xs('Close', level=1, axis=1)
                else: continue
                
                if isinstance(c, pd.DataFrame):
                    for sym in c.columns: closes_dict[sym] = c[sym]
                elif isinstance(c, pd.Series):
                    closes_dict[c.name] = c
            else:
                if 'Close' in df.columns and len(chunk) == 1:
                    closes_dict[chunk[0]] = df['Close']
                    
        except Exception as e:
            print(f"⚠️ Error on chunk {i}: {e}")
            
        # A solid 3-second pause between chunks keeps the bot under the radar
        time.sleep(3)

    closes = pd.DataFrame(closes_dict)
    
    if closes.empty:
        print("❌ FATAL: No data was successfully downloaded. Exiting.")
        return

    if hasattr(closes.index, 'tz') and closes.index.tz is not None:
        closes.index = closes.index.tz_localize(None)
        
    closes.index = pd.to_datetime(closes.index)
    closes = closes.ffill().dropna(how='all')

    monthly_data = closes.resample('ME').last()
    monthly_returns = monthly_data.pct_change().dropna() * 100

    results = []
    valid_cols = list(closes.columns)
    
    print(f"Successfully downloaded {len(valid_cols)} symbols. Calculating seasonality...")
    
    for react_sym in universe_symbols:
        yahoo_sym = YAHOO_MAP.get(react_sym, react_sym)
        if yahoo_sym not in valid_cols: continue
        
        col_rets = monthly_returns[yahoo_sym].dropna()
        if len(col_rets) < 60: continue 
        
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
    print("✅ Seasonality JSON generated successfully.")

if __name__ == "__main__":
    generate_seasonality()
