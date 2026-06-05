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

    # Diagnostic Tracking Lists
    missing_from_yahoo = []
    not_enough_days = []
    missing_date_prices = []
    generic_errors = []

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
                
            # FIX 3: Cross-version robust parser for pandas multi-index mutations in yfinance
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
        
        # FIX 4: Strip localized timezones before processing date subtraction metrics
        if closes.index.tz is not None:
            closes.index = closes.index.tz_localize(None)
        closes.index = pd.to_datetime(closes.index).normalize()
        
        closes = closes.ffill().dropna(how='all')
        valid_downloaded_symbols = set(closes.columns)

        for react_symbol in universe_symbols:
            try:
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                # Check A: Missing completely from download
                if yahoo_symbol not in valid_downloaded_symbols:
                    missing_from_yahoo.append(react_symbol)
                    continue
                
                col = closes[yahoo_symbol].dropna()
                
                # Check B: Recent listings without historical reference bounds
                if len(col) < 5:
                    not_enough_days.append(react_symbol)
                    continue 
                    
                current_date = col.index[-1]
                current_price = col.iloc[-1]
                
                target_1w = current_date - pd.Timedelta(days=7) 
                target_3m = current_date - pd.DateOffset(months=3) 
                
                price_1w = col.asof(target_1w)
                price_3m = col.asof(target_3m)
                
                # Check C: Gaps in historical indexes causing NaN lookup
                if pd.isna(price_1w) or pd.isna(price_3m):
                    missing_date_prices.append(react_symbol)
                    continue 
                
                ret1w = ((current_price - price_1w) / price_1w) * 100
                ret3m = ((current_price - price_3m) / price_3m) * 100
                
                stock_meta = metadata.get(react_symbol, {"name": react_symbol, "sector": "Uncategorized"})
                
                results[react_symbol] = {
                    "name": stock_meta.get("name", react_symbol),
                    "sector": stock_meta.get("sector", "Uncategorized"),
                    "ret1w": round(float(ret1w), 2),
                    "ret3m": round(float(ret3m), 2)
                }
                
            except Exception as ex:
                generic_errors.append(f"{react_symbol} ({str(ex)})")
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile)
            
        # ─── PRINT DETAILED SUMMARY REPORT ───
        print("\n" + "="*50)
        print("📊 DATA EXTRACTION REPORT")
        print("="*50)
        print(f"✅ Successfully Processed: {len(results)} stocks")
        
        if missing_from_yahoo:
            print(f"\n❌ Missing from Yahoo entirely ({len(missing_from_yahoo)}):")
            print(f"   {', '.join(missing_from_yahoo[:12])}" + ("..." if len(missing_from_yahoo) > 12 else ""))
            
        if not_enough_days:
            print(f"\n⚠️ Recent IPO / Insufficient data history ({len(not_enough_days)}):")
            print(f"   {', '.join(not_enough_days)}")
            
        if missing_date_prices:
            print(f"\n📅 Missing historical milestone prices ({len(missing_date_prices)}):")
            print(f"   {', '.join(missing_date_prices[:12])}" + ("..." if len(missing_date_prices) > 12 else ""))
            
        if generic_errors:
            print(f"\n🐛 Formatting/Runtime Exceptions ({len(generic_errors)}):")
            for err in generic_errors[:5]: 
                print(f"   - {err}")
        print("="*50 + "\n")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
