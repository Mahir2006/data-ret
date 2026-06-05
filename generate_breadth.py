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

# Target sectors dictionary mapping for sector breadth
TARGET_SECTORS = {
    "Financial Services": {"target_count": 82, "symbols": ["HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "RBLBANK.NS", "SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "INDIANB.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS", "SHRIRAMFIN.NS", "LICHSGFIN.NS", "PNBHOUSING.NS", "CANFINHOME.NS", "HOMEFIRST.NS", "BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "KFINTECH.NS", "ANGELONE.NS", "360ONE.NS", "MOTILALOFS.NS", "NUVAMA.NS", "SBILIFE.NS", "HDFCLIFE.NS", "LICI.NS", "MAXHEALTH.NS", "ICICIGI.NS", "NIACL.NS", "GICRE.NS", "STARHEALTH.NS", "PAYTM.NS", "POLICYBZR.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "SOBHA.NS", "BRIGADE.NS", "MAHLIFE.NS", "PHOENIXLTD.NS", "EMBASSY.NS", "MINDSPACE.NS"]},
    "Information Technology": {"target_count": 54, "symbols": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS", "FIRSTSOURCE.NS", "MASTEK.NS", "RATEGAIN.NS", "KPITTECH.NS"]},
    "Consumer Discretionary": {"target_count": 68, "symbols": ["VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS", "HAVELLS.NS", "CROMPTON.NS", "VGUARD.NS", "TITAN.NS", "KALYAN.NS", "SENCO.NS", "PCJEWELLER.NS", "KANSAINER.NS", "AKZOINDIA.NS", "PAGEIND.NS", "TRENT.NS", "RAYMOND.NS", "MANYAVAR.NS", "ARVIND.NS", "TRIDENT.NS", "KPR.NS", "VARDHMAN.NS", "WELSPUNIND.NS", "INDHOTEL.NS", "LEMONTREE.NS", "CHALET.NS", "MAHINDRAHOLIDAYS.NS", "JUBLFOOD.NS", "DEVYANI.NS", "WESTLIFE.NS", "SAPPHIRE.NS", "NYKAA.NS", "DMART.NS", "IRCTC.NS", "EASEMYTRIP.NS", "THOMASCOOK.NS"]},
    "Healthcare": {"target_count": 45, "symbols": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS", "BIOCON.NS", "IPCA.NS", "ALKEM.NS", "GRANULES.NS", "SUVEN.NS", "APOLLOHOSP.NS", "FORTIS.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "THYROCARE.NS"]},
    "Industrials & Capital Goods": {"target_count": 62, "symbols": ["HAL.NS", "BDL.NS", "BEML.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "PARAS.NS", "ABB.NS", "SIEMENS.NS", "BHEL.NS", "CUMMINSIND.NS", "THERMAX.NS", "AIAENG.NS", "LT.NS", "NCC.NS", "KNRCON.NS", "PNCINFRA.NS", "GRINFRA.NS", "POLYCAB.NS", "APLAPOLLO.NS", "SUPREMEIND.NS", "ASTRAL.NS", "FINOLEX.NS", "INDIGO.NS", "BLUEDART.NS", "DELHIVERY.NS", "MAHLOG.NS", "GESHIP.NS", "ADANIPORTS.NS", "CONCOR.NS", "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", "ACC.NS", "JKCEMENT.NS", "RAMCOCEM.NS", "SHREECEM.NS", "KAJARIACER.NS", "ORIENTBELL.NS", "ASIANPAINT.NS", "TNPL.NS", "JKPAPER.NS", "CENTURYPLY.NS", "GREENPLY.NS", "GMRINFRA.NS"]},
    "FMCG": {"target_count": 38, "symbols": ["HINDUNILVR.NS", "COLPAL.NS", "EMAMILTD.NS", "GILLETTE.NS", "BAJAJCON.NS", "GODREJCP.NS", "JYOTHYLAB.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS", "BIKAJI.NS", "TATACONSUM.NS", "MCDOWELL-N.NS", "UBL.NS", "RADICO.NS", "GLOBUSSPR.NS", "ITC.NS", "GODFRYPHLP.NS", "VSTIND.NS"]},
    "Energy & Oil/Gas": {"target_count": 32, "symbols": ["ONGC.NS", "OIL.NS", "RELIANCE.NS", "BPCL.NS", "IOC.NS", "HINDPETRO.NS", "IGL.NS", "MGL.NS", "GAIL.NS", "ATGL.NS", "GSPL.NS", "CASTROLIND.NS", "GUJARATGAS.NS"]},
    "Metals & Mining": {"target_count": 28, "symbols": ["TATASTEEL.NS", "JSWSTEEL.NS", "SAIL.NS", "JINDALSTEL.NS", "NMDC.NS", "HINDALCO.NS", "VEDL.NS", "NATIONALUM.NS", "HINDCOPPER.NS", "COALINDIA.NS", "MOIL.NS"]},
    "Automobiles": {"target_count": 35, "symbols": ["MARUTI.NS", "TMCV.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "TVSMOTORS.NS", "EICHERMOT.NS", "ASHOKLEY.NS", "ESCORTS.NS", "FORCEMOT.NS", "MOTHERSON.NS", "BOSCHLTD.NS", "BHARATFORG.NS", "APOLLOTYRE.NS", "MRF.NS", "BALKRISIND.NS", "EXIDEIND.NS", "SUNDRMFAST.NS"]},
    "Utilities & Power": {"target_count": 26, "symbols": ["NTPC.NS", "TATAPOWER.NS", "JSWENERGY.NS", "TORNTPOWER.NS", "CESC.NS", "POWERGRID.NS", "RECLTD.NS", "PFC.NS", "ADANIENSOL.NS"]},
    "Chemicals": {"target_count": 22, "symbols": ["PIDILITIND.NS", "SRF.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "AARTIIND.NS", "ATUL.NS", "AAVAS.NS", "GHCL.NS", "TATACHEM.NS", "APCOTEXIND.NS", "UPL.NS", "PIIND.NS", "RALLIS.NS", "COROMANDEL.NS", "CHAMBALFERT.NS", "GSFC.NS"]},
    "Telecom & Media": {"target_count": 8, "symbols": ["ZEEL.NS", "SUNTV.NS", "NETWORK18.NS", "PVRINOX.NS", "NAZARA.NS", "SAREGAMA.NS", "JAGRAN.NS", "DBCORP.NS", "HTMEDIA.NS", "BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS", "RAILTEL.NS", "HFCL.NS", "TEJASNET.NS", "STLTECH.NS"]}
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
        df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
        return (df['Symbol'].astype(str) + ".NS").tolist()
        
    except Exception as e:
        print(f"Error fetching NSE list: {e}")
        return []

# ─── 2. BREADTH DATA CALCULATION & FORMATTING ─────────────────────────────────
def generate_breadth_data():
    universe_symbols = get_live_nifty_500()
    
    if not universe_symbols:
        print("Fatal Error: Could not fetch Nifty 500 list from NSE. Exiting.")
        return

    # EXPLICITLY INJECT NIFTY 50 BENCHMARK FOR THE DASHBOARD
    if "^NSEI" not in universe_symbols:
        universe_symbols.insert(0, "^NSEI")

    print("Starting TRUE market breadth calculation (Dynamic 500-stock universe)...")
    
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in universe_symbols]
    all_tickers = list(set(yahoo_symbols_to_download))

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

        valid_cols = [c for c in closes.columns if c != '^NSEI']
        stocks_df = closes[valid_cols].dropna(how='all')
        
        # Calculate moving averages over entire year
        ema20 = stocks_df.ewm(span=20, adjust=False).mean()
        ema50 = stocks_df.ewm(span=50, adjust=False).mean()
        ema200 = stocks_df.ewm(span=200, adjust=False).mean()
        sma200 = stocks_df.rolling(window=200, min_periods=50).mean()
        high52 = stocks_df.rolling(window=252, min_periods=50).max()
        low52 = stocks_df.rolling(window=252, min_periods=50).min()
        
        # --- DATE BASED LOGIC IMPLEMENTATION ---
        curr_date = stocks_df.index[-1]
        target_1w = curr_date - pd.Timedelta(days=7)
        target_1m = curr_date - pd.DateOffset(months=1)
        
        curr_px = stocks_df.iloc[-1]
        px_1w = stocks_df.asof(target_1w)
        
        total_tracked = len(valid_cols)
        mul = 500 / total_tracked if total_tracked > 0 else 1
        
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
        
        # Benchmark Calculations (Date-based)
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
            
        # Sectors logic (Date-based)
        sectors_json = []
        for sec_name, sec_data in TARGET_SECTORS.items():
            sec_syms = [YAHOO_MAP.get(s, s) for s in sec_data["symbols"]]
            valid_sec_syms = [s for s in sec_syms if s in valid_cols]
            if valid_sec_syms:
                sec_df = stocks_df[valid_sec_syms]
                pct_above = (sec_df.iloc[-1] > ema50[valid_sec_syms].iloc[-1]).sum() / len(valid_sec_syms)
                
                sec_curr_sum = sec_df.iloc[-1].sum()
                sec_1w_sum = sec_df.asof(target_1w).sum()
                sec_ret = ((sec_curr_sum - sec_1w_sum) / sec_1w_sum) * 100
                
                sectors_json.append({
                    "name": sec_name,
                    "total": sec_data["target_count"],
                    "aboveEma50": int(pct_above * sec_data["target_count"]),
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
            
        print("\nSuccessfully generated breadth_data.json in the required format.")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    generate_breadth_data()
