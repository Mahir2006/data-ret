import yfinance as yf
import pandas as pd
import json
import time
import requests
import io
import datetime
import calendar

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

    all_tickers = list(set([YAHOO_MAP.get(sym, sym) for sym in universe_symbols]))
    end_date = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(days=365 * 10)

    track(f"Downloading historical data for {len(all_tickers)} symbols...")
    closes_dict = {}
    volumes_dict = {}
    chunk_size = 20 
    
    for i in range(0, len(all_tickers), chunk_size):
        chunk = all_tickers[i:i + chunk_size]
        track(f"--> Fetching chunk {i} to {i + len(chunk)}...")
        try:
            df = yf.download(chunk, start=start_date, end=end_date, interval="1d", threads=False, progress=False)
            if df.empty: 
                time.sleep(3)
                continue
            
            price_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
            
            if isinstance(df.columns, pd.MultiIndex):
                if price_col in df.columns.get_level_values(0):
                    c_df = df[price_col]
                elif price_col in df.columns.get_level_values(1):
                    c_df = df.xs(price_col, level=1, axis=1)
                else: continue
                
                if 'Volume' in df.columns.get_level_values(0):
                    v_df = df['Volume']
                elif 'Volume' in df.columns.get_level_values(1):
                    v_df = df.xs('Volume', level=1, axis=1)
                else: v_df = pd.DataFrame()

                for sym in chunk:
                    if sym in c_df.columns: closes_dict[sym] = c_df[sym]
                    if sym in v_df.columns: volumes_dict[sym] = v_df[sym]
            else:
                if len(chunk) == 1:
                    if price_col in df.columns: closes_dict[chunk[0]] = df[price_col]
                    if 'Volume' in df.columns: volumes_dict[chunk[0]] = df['Volume']
                    
        except Exception as e:
            track(f"⚠️ Error on chunk {i}: {e}")
        time.sleep(2)

    closes = pd.DataFrame(closes_dict).ffill().dropna(how='all')
    volumes = pd.DataFrame(volumes_dict).ffill().dropna(how='all')
    
    if closes.empty:
        track("❌ FATAL: No data was downloaded.")
        return

    if hasattr(closes.index, 'tz') and closes.index.tz is not None:
        closes.index = closes.index.tz_localize(None)
    closes.index = pd.to_datetime(closes.index).normalize()

    monthly_data = closes.resample('ME').last()
    monthly_returns = monthly_data.pct_change() * 100
    rolling_3m_returns = monthly_data.pct_change(periods=3) * 100

    results = []
    labels_3m = {
        1: "Nov-Jan", 2: "Dec-Feb", 3: "Jan-Mar", 4: "Feb-Apr",
        5: "Mar-May", 6: "Apr-Jun", 7: "May-Jul", 8: "Jun-Aug",
        9: "Jul-Sep", 10: "Aug-Oct", 11: "Sep-Nov", 12: "Oct-Dec"
    }

    track("Processing metrics and flagging volume breakouts...")
    for react_sym in universe_symbols:
        yahoo_sym = YAHOO_MAP.get(react_sym, react_sym)
        if yahoo_sym not in closes.columns: continue
        
        # --- Volume Breakout Logic (Flagging only, no filtering here) ---
        vol_series = volumes[yahoo_sym].dropna() if yahoo_sym in volumes.columns else pd.Series()
        volume_breakout = False
        
        if len(vol_series) >= 4:
            today_volume = float(vol_series.iloc[-1])
            last_3_days_avg = float(vol_series.iloc[-4:-1].mean())
            if last_3_days_avg > 0 and today_volume > last_3_days_avg:
                volume_breakout = True

        col_rets = monthly_returns[yahoo_sym].dropna()
        col_rets_3m = rolling_3m_returns[yahoo_sym].dropna()
        if len(col_rets) < 60 or len(col_rets_3m) < 60: continue 
        
        # --- 1-Month Seasonality ---
        df_months = pd.DataFrame({'Return': col_rets})
        df_months['Month'] = df_months.index.month
        seasonality = df_months.groupby('Month').agg(
            avgReturn=('Return', 'mean'), winRate=('Return', lambda x: (x > 0).mean() * 100)
        )
        seasonality.index = [calendar.month_abbr[i] for i in seasonality.index]
        
        # --- 3-Month Seasonality ---
        df_3m = pd.DataFrame({'Return': col_rets_3m})
        df_3m['Month'] = df_3m.index.month
        seasonality_3m = df_3m.groupby('Month').agg(
            avgReturn=('Return', 'mean'), winRate=('Return', lambda x: (x > 0).mean() * 100)
        )
        seasonality_3m.index = [labels_3m[i] for i in seasonality_3m.index]
        
        meta = metadata.get(react_sym, {"name": react_sym, "sector": "Uncategorized"})
        
        results.append({
            "symbol": react_sym.replace(".NS", ""),
            "name": meta["name"],
            "sector": meta["sector"],
            "volumeBreakout": volume_breakout,  # Attach the flag!
            "months": {
                k: {"winRate": round(v['winRate'], 1), "avgReturn": round(v['avgReturn'], 2)} 
                for k, v in seasonality.to_dict('index').items()
            },
            "threeMonths": {
                k: {"winRate": round(v['winRate'], 1), "avgReturn": round(v['avgReturn'], 2)} 
                for k, v in seasonality_3m.to_dict('index').items()
            }
        })

    output = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stocks": results
    }

    with open("seasonality_data.json", "w") as outfile:
        json.dump(output, outfile)
    track("🎉 DONE! JSON generated successfully.")

if __name__ == "__main__":
    generate_seasonality()
