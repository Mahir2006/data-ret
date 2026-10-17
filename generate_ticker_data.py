import yfinance as yf
import pandas as pd
import json
import time
import random
import requests
import io
import datetime
import concurrent.futures
import csv # Added to safely parse messy NSE files

# Edge-case mappings for Yahoo Finance ticker mismatches
YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
    "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
    "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
    "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS",
    "3BBLACKBIO.NS": "KILPEST.NS"
}

def track(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def get_fo_symbols():
    track("Fetching official F&O symbols from NSE...")
    url = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    fo_symbols = set()
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
            # Use Python's native CSV reader instead of Pandas to prevent crashes on messy NSE rows
            reader = csv.reader(response.text.splitlines())
            headers_found = False
            sym_index = -1
            
            for row in reader:
                clean_row = [str(item).strip() for item in row]
                
                if not headers_found:
                    if 'SYMBOL' in clean_row:
                        headers_found = True
                        sym_index = clean_row.index('SYMBOL')
                elif headers_found and sym_index != -1 and len(clean_row) > sym_index:
                    sym = clean_row[sym_index]
                    if sym and sym != "SYMBOL":
                        fo_symbols.add(sym)
                        
        track(f"Successfully loaded {len(fo_symbols)} F&O symbols.")
    except Exception as e:
        track(f"⚠️ Error fetching F&O list: {e}")
        
    return fo_symbols

def get_all_nse_equities():
    track("Fetching master list of ALL active NSE equities (EQUITY_L.csv)...")
    
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    metadata = {}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
            df = pd.read_csv(io.StringIO(response.text))
            df.columns = df.columns.str.strip()
            
            df = df[df['SERIES'].astype(str).str.strip() == 'EQ']
            
            for _, row in df.iterrows():
                sym = str(row['SYMBOL']).strip()
                metadata[sym] = {
                    "name": str(row.get('NAME OF COMPANY', sym)).strip(),
                    "sector": "Equity"
                }
            track(f"Successfully loaded {len(metadata)} regular equities from NSE.")
    except Exception as e:
        track(f"⚠️ Error fetching master list: {e}")
            
    return metadata

def fetch_single_ticker(react_sym):
    # Stagger requests by randomly pausing to avoid Yahoo rate limits
    time.sleep(random.uniform(0.5, 2.0))
    
    ns_sym = react_sym + ".NS"
    yahoo_sym = YAHOO_MAP.get(ns_sym, ns_sym)
    
    mcap_val = 0
    pct_change = 0.0
    
    try:
        ticker = yf.Ticker(yahoo_sym)
        
        # 1. Try pulling fast_info for speed
        try:
            mcap_val = ticker.fast_info.get('marketCap', 0)
            prev_close = ticker.fast_info.get('previousClose', 0)
            last_price = ticker.fast_info.get('lastPrice', 0)
        except:
            prev_close = 0
            last_price = 0

        # 2. If fast_info is incomplete, fall back to heavy .info dictionary
        info = {}
        if not mcap_val or not prev_close or not last_price:
            try:
                info = ticker.info
                if not mcap_val: mcap_val = info.get("marketCap", 0)
                if not prev_close: prev_close = info.get("previousClose", 0)
                if not last_price: last_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
            except:
                pass

        # 3. MANUAL CALCULATION (Crucial for missing NSE SME stocks)
        if (not mcap_val or mcap_val == 0) and last_price:
            shares = info.get("sharesOutstanding", 0)
            if shares > 0:
                mcap_val = shares * last_price

        # Calculate the percentage gain
        if prev_close and last_price and prev_close > 0:
            pct_change = round(((last_price - prev_close) / prev_close) * 100, 2)
            
        mcap_crores = round(mcap_val / 10000000, 2) if mcap_val else 0
        return react_sym, mcap_crores, mcap_val, pct_change, None

    except Exception as e:
        return react_sym, 0, 0, 0.0, str(e)

def generate_ticker_data():
    metadata = get_all_nse_equities()
    if not metadata:
        track("Fatal Error: No symbols fetched from NSE.")
        return

    # Fetch official F&O List
    fo_symbols = get_fo_symbols()

    results = {}
    symbols = list(metadata.keys())
    track(f"Fetching Market Cap & EOD % Gain for {len(symbols)} unique NSE symbols...")
    
    fetch_errors = []
    missing_mcap_data = []
    
    completed = 0
    # Safe worker limit to prevent IP bans
    max_workers = 3 
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_sym = {executor.submit(fetch_single_ticker, sym): sym for sym in symbols}
        
        for future in concurrent.futures.as_completed(future_to_sym):
            react_sym, mcap_crores, mcap_raw, pct_change, error = future.result()
            
            if error:
                fetch_errors.append(f"{react_sym} ({error})")
            elif not mcap_raw or mcap_raw == 0:
                missing_mcap_data.append(react_sym)
                
            results[react_sym] = {
                "name": metadata[react_sym]["name"],
                "sector": metadata[react_sym]["sector"],
                "mcap": mcap_crores,
                "pctChange": pct_change,
                "isFNO": react_sym in fo_symbols # Flagging F&O Stocks
            }
            
            completed += 1
            if completed % 100 == 0:
                track(f"--> Processed {completed} / {len(symbols)} stocks...")
                
    output = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stocks": results
    }

    with open("ticker_data.json", "w") as outfile:
        json.dump(output, outfile)
        
    print("\n" + "="*50)
    print("📊 TICKER DATA EXTRACTION REPORT")
    print("="*50)
    print(f"✅ Total Processed: {len(results)} stocks")
    print(f"✅ Successful Fetches: {len(results) - len(missing_mcap_data) - len(fetch_errors)}")
    
    if missing_mcap_data:
        print(f"\n⚠️ Missing Market Data on Yahoo ({len(missing_mcap_data)}):")
        print(f"   {', '.join(missing_mcap_data[:15])}" + ("..." if len(missing_mcap_data) > 15 else ""))
        
    if fetch_errors:
        print(f"\n❌ Exception/Network Errors ({len(fetch_errors)}):")
        for err in fetch_errors[:5]: 
            print(f"   - {err}")
    print("="*50 + "\n")
    
    track("🎉 DONE! ticker_data.json generated successfully.")

if __name__ == "__main__":
    generate_ticker_data()
