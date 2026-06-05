import yfinance as yf
import pandas as pd
import json
import time
import requests
import io
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Edge-case mappings for Yahoo Finance ticker mismatches
YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
    "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
    "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
    "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS"
}

def get_live_nifty_500():
    print("Fetching live Nifty 500 constituents and metadata from NSE...")
    
    # We use two endpoints. If the primary blocks us with HTML, we fall back to the archive.
    urls = [
        "https://niftyindices.com/Indexconstituent/ind_nifty500list.csv",
        "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    ]
    
    # Modern browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/csv,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
    
    session = requests.Session()
    retry_strategy = Retry(
        total=3, 
        backoff_factor=2, 
        status_forcelist=[403, 429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(headers)
    
    csv_payload = None
    
    for url in urls:
        try:
            # Extract base domain to fetch fresh cookies before requesting the file
            base_domain = url.split('/')[2]
            print(f"Establishing secure session with {base_domain}...")
            
            # Ping base domain to get Cloudflare/Akamai session cookies
            session.get(f"https://{base_domain}", timeout=15)
            time.sleep(1.5) 
            
            print(f"Downloading CSV payload from {url}...")
            response = session.get(url, timeout=20)
            
            # CRITICAL FIX: Ensure the response isn't an HTML bot-challenge page
            if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
                csv_payload = response.text
                print("✅ Successfully downloaded clean CSV data.")
                break
            else:
                print(f"⚠️ {base_domain} returned an HTML block page or non-200 status. Trying fallback...")
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Connection error with {base_domain}: {e}")
            
    if not csv_payload:
        print("\nFATAL: Both NSE servers blocked the request or timed out.")
        return [], {}

    try:
        # Load the validated payload into Pandas
        df = pd.read_csv(io.StringIO(csv_payload))
        
        # Clean hidden trailing whitespaces from CSV column headers
        df.columns = df.columns.str.strip()
        
        df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
        
        # --- NOTE: Keep your existing file-specific metadata parsing logic below this line ---
        # (generate_data.py uses dictionary metadata formatting, while generate_breadth.py uses string formatting)

# ─── 2. BREADTH DATA CALCULATION & FORMATTING ─────────────────────────────────
def generate_breadth_data():
    universe_symbols, metadata = get_live_nifty_500()
    
    if not universe_symbols:
        print("Fatal Error: Could not fetch Nifty 500 list from NSE. Exiting.")
        return

    if "^NSEI" not in universe_symbols:
        universe_symbols.insert(0, "^NSEI")
        metadata["^NSEI"] = "Benchmark"

    print("Starting TRUE market breadth calculation (Dynamic 500-stock universe)...")
    
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download))

    # Diagnostic Tracking Lists
    missing_from_yahoo = []
    not_enough_days = []
    missing_date_prices = []
    generic_errors = []

    try:
        print(f"Downloading 1-year data for {len(all_tickers)} individual tickers...\n")
        chunk_size = 50
        closes_dict = {}
        
        for i in range(0, len(all_tickers), chunk_size):
            chunk = all_tickers[i:i + chunk_size]
            print(f"Fetching batch {(i//chunk_size) + 1}/{(len(all_tickers)//chunk_size) + 1}...")
            
            df = yf.download(chunk, period="1y", interval="1d", progress=False, threads=False)
            
            if df.empty:
                continue
                
            # CRITICAL FIX 2: Multi-Index yfinance parsing
            if isinstance(df.columns, pd.MultiIndex):
                if 'Close' in df.columns.get_level_values(0):
                    c = df['Close']
                elif 'Close' in df.columns.get_level_values(1):
                    c = df.xs('Close', level=1, axis=1)
                else:
                    continue
                
                if isinstance(c, pd.DataFrame):
                    for sym in c.columns:
                        closes_dict[sym] = c[sym]
                elif isinstance(c, pd.Series):
                    closes_dict[c.name] = c
            else:
                if 'Close' in df.columns and len(chunk) == 1:
                    closes_dict[chunk[0]] = df['Close']
            
            time.sleep(1.5) 
            
        if not closes_dict:
            print("\nFatal Error: All downloads were blocked or empty.")
            return
            
        closes = pd.DataFrame(closes_dict)
        
        # CRITICAL FIX 3: Strip timezones before calculating exact date offsets
        if closes.index.tz is not None:
            closes.index = closes.index.tz_localize(None)
        closes.index = pd.to_datetime(closes.index).normalize()
        
        closes = closes.ffill().dropna(how='all')

        valid_cols = [c for c in closes.columns if c != '^NSEI']
        stocks_df = closes[valid_cols].dropna(how='all')
        
        # Calculate moving averages over entire year
        ema20 = stocks_df.ewm(span=20, adjust=False).mean()
        ema50 = stocks_df.ewm(span=50, adjust=False).mean()
        ema200 = stocks_df.ewm(span=200, adjust=False).mean()
        sma200 = stocks_df.rolling(window=200, min_periods=50).mean()
        high52 = stocks_df.rolling(window=252, min_periods=50).max()
        low52 = stocks_df.rolling(window=252, min_periods=50).min()
        
        curr_date = stocks_df.index[-1]
        target_1w = curr_date - pd.Timedelta(days=7)
        target_1m = curr_date - pd.DateOffset(months=1)
        
        curr_px = stocks_df.iloc[-1]
        px_1w = stocks_df.asof(target_1w)
        
        total_tracked = len(valid_cols)
        mul = 500 / total_tracked if total_tracked > 0 else 1
        
        # Pre-flight error checks for diagnostics
        for react_symbol in universe_symbols:
            if react_symbol == "^NSEI": continue
            yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
            if yahoo_symbol not in valid_cols:
                missing_from_yahoo.append(react_symbol)
            else:
                col = closes[yahoo_symbol].dropna()
                if len(col) < 50: # Using 50 because we calculate 50EMA
                    not_enough_days.append(react_symbol)
        
        overall = {
            "aboveEma50": int((curr_px > ema50.iloc[-1]).sum() * mul),
            "totalStocks": 500,
            "advancers": int((curr_px > px_1w).sum() * mul),
            "decliners": int((curr_px < px_1w).sum() * mul),
            "unchanged": max(0, 500 - int((curr_px > px_1w).sum() * mul) - int((curr_px < px_1w).sum() * mul)),
            "newHighs52W": int((curr_px >= high52.iloc[-1] * 0.98).sum() * mul),
            "newLows52W": int((curr_px <= low52.iloc[-1] * 1.02).sum() * mul),
            "aboveEma20": int((curr_px > ema20.iloc[-1]).sum() * mul),
            "aboveEma200": int((curr_px > ema200.iloc[-1]).sum() * mul),
            "aboveSma200": int((curr_px > sma200.iloc[-1]).sum() * mul)
        }
        
        # Benchmark Calculations 
        nifty = closes.get('^NSEI')
        if nifty is not None and not nifty.isna().all():
            nifty = nifty.dropna()
            n_curr = nifty.iloc[-1]
            n_1w = nifty.asof(target_1w)
            n_1m = nifty.asof(target_1m)
            
            overall["nifty500Change1W"] = round(((n_curr - n_1w) / n_1w) * 100, 2)
            overall["nifty500Change1M"] = round(((n_curr - n_1m) / n_1m) * 100, 2)
            n_ema50, n_ema200 = nifty.ewm(span=50).mean().iloc[-1], nifty.ewm(span=200).mean().iloc[-1]
            golden_cross = bool(n_ema50 > n_ema200)
            death_cross = bool(n_ema50 < n_ema200)
        else:
            overall["nifty500Change1W"] = 0; overall["nifty500Change1M"] = 0
            golden_cross = False; death_cross = False
            print("Warning: Benchmark Nifty 50 (^NSEI) data was missing.")
            
        # Sectors logic (DYNAMICALLY GROUPED)
        sectors_json = []
        sectors_map = {}
        
        # Map successfully downloaded symbols back to their dynamic sectors
        for react_sym in universe_symbols:
            if react_sym == "^NSEI": continue
            yahoo_sym = YAHOO_MAP.get(react_sym, react_sym)
            
            if yahoo_sym in valid_cols:
                sec_name = metadata.get(react_sym, "Uncategorized")
                sectors_map.setdefault(sec_name, []).append(yahoo_sym)
                
        for sec_name, valid_sec_syms in sectors_map.items():
            if not valid_sec_syms: continue
            
            sec_df = stocks_df[valid_sec_syms]
            target_count = len(valid_sec_syms)
            
            above_count = (sec_df.iloc[-1] > ema50[valid_sec_syms].iloc[-1]).sum()
            
            sec_curr_sum = sec_df.iloc[-1].sum()
            sec_1w_sum = sec_df.asof(target_1w).sum()
            sec_ret = ((sec_curr_sum - sec_1w_sum) / sec_1w_sum) * 100 if sec_1w_sum != 0 else 0
            
            sectors_json.append({
                "name": sec_name,
                "total": target_count,
                "aboveEma50": int(above_count),
                "change1W": round(sec_ret, 2)
            })
                
        # History logic (Date-based 11-week loop)
        history_json = []
        for i in range(11, -1, -1):
            target_date_h = curr_date - pd.Timedelta(days=7 * i)
            h_px = stocks_df.asof(target_date_h)
            h_ema50 = ema50.asof(target_date_h)
            
            if not pd.isna(h_px).all():
                h_pct = ((h_px > h_ema50).sum() / total_tracked) * 100
                history_json.append({"week": f"W{-i}" if i > 0 else "Curr", "breadth": round(h_pct, 1)})
                
        # Signals Generation
        trend = "uptrend" if overall["nifty500Change1M"] > 2 else "downtrend" if overall["nifty500Change1M"] < -2 else "sideways"
        mom = int((overall["aboveEma20"] / 500) * 100)
        
        signals_json = {
            "goldenCross": golden_cross, "deathCross": death_cross,
            "divergence": "none", "trend": trend, "momentumScore": mom,
            "breadthThrust": bool(mom > 70 and overall["nifty500Change1W"] > 2),
            "marketRegime": "risk-on" if trend == "uptrend" else "risk-off" if trend == "downtrend" else "neutral"
        }
        
        # Save output
        with open("breadth_data.json", "w") as outfile:
            json.dump({ "overall": overall, "sectors": sectors_json, "history": history_json, "signals": signals_json }, outfile)
            
        # ─── PRINT DIAGNOSTIC REPORT ───
        print("\n" + "="*50)
        print("📊 BREADTH EXTRACTION REPORT")
        print("="*50)
        print(f"✅ Successfully Processed: {total_tracked} stocks")
        
        if missing_from_yahoo:
            print(f"\n❌ Missing from Yahoo entirely ({len(missing_from_yahoo)}):")
            print(f"   {', '.join(missing_from_yahoo[:10])}" + ("..." if len(missing_from_yahoo) > 10 else ""))
            
        if not_enough_days:
            print(f"\n⚠️ Recent IPO / Less than 50 days of history ({len(not_enough_days)}):")
            print(f"   {', '.join(not_enough_days)}")
            
        if missing_date_prices:
            print(f"\n📅 Missing historical milestone dates ({len(missing_date_prices)}):")
            print(f"   {', '.join(missing_date_prices[:10])}" + ("..." if len(missing_date_prices) > 10 else ""))
        print("="*50 + "\n")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    generate_breadth_data()
