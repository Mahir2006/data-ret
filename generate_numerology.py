import yfinance as yf
import pandas as pd
import json
import time
import requests
import io
import datetime

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
            
            # CRITICAL: Filter for 'EQ' series to drop bonds, ETFs, and suspended segments
            df = df[df['SERIES'].astype(str).str.strip() == 'EQ']
            
            for _, row in df.iterrows():
                sym = str(row['SYMBOL']).strip()
                metadata[sym] = {
                    "name": str(row.get('NAME OF COMPANY', sym)).strip(),
                    "sector": "Equity" # Master list lacks detailed sectors, so we default to Equity
                }
            track(f"Successfully loaded {len(metadata)} regular equities from NSE.")
    except Exception as e:
        track(f"⚠️ Error fetching master list: {e}")
            
    return metadata

def generate_numerology_data():
    metadata = get_all_nse_equities()
    if not metadata:
        track("Fatal Error: No symbols fetched from NSE.")
        return

    results = {}
    symbols = list(metadata.keys())
    track(f"Fetching Market Cap for {len(symbols)} unique NSE symbols. This will take ~10-15 minutes...")
    
    chunk_size = 50
    for i in range(0, len(symbols), chunk_size):
        chunk_symbols = symbols[i:i + chunk_size]
        track(f"--> Processing batch {(i//chunk_size) + 1} of {(len(symbols)//chunk_size) + 1}...")
        
        for react_sym in chunk_symbols:
            ns_sym = react_sym + ".NS"
            yahoo_sym = YAHOO_MAP.get(ns_sym, ns_sym)
            
            try:
                ticker = yf.Ticker(yahoo_sym)
                mcap_raw = ticker.info.get("marketCap", 0)
                mcap_crores = round(mcap_raw / 10000000, 2) if mcap_raw else 0
                
                results[react_sym] = {
                    "name": metadata[react_sym]["name"],
                    "sector": metadata[react_sym]["sector"],
                    "mcap": mcap_crores
                }
            except Exception as e:
                results[react_sym] = {
                    "name": metadata[react_sym]["name"],
                    "sector": metadata[react_sym]["sector"],
                    "mcap": 0
                }
        
        # 1.5-second pause between batches to respect Yahoo's rate limits for ~2200 tickers
        time.sleep(1.5)
        
    output = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stocks": results
    }

    with open("numerology_data.json", "w") as outfile:
        json.dump(output, outfile)
    track("🎉 DONE! numerology_data.json generated successfully.")

if __name__ == "__main__":
    generate_numerology_data()
