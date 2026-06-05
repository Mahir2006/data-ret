import yfinance as yf
import pandas as pd
import json

UNIVERSE_SYMBOLS = [
    "^NSEI", "PIDILITIND.NS", "SRF.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "AARTIIND.NS", "ATUL.NS",
    "AAVAS.NS", "GHCL.NS", "TATACHEM.NS", "APCOTEXIND.NS", "UPL.NS", "PIIND.NS", "RALLIS.NS", 
    "COROMANDEL.NS", "CHAMBALFERT.NS", "GSFC.NS", "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", 
    "ACC.NS", "JKCEMENT.NS", "RAMCOCEM.NS", "SHREECEM.NS", "KAJARIACER.NS", 
    "ORIENTBELL.NS", "ASIANPAINT.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "SAIL.NS", 
    "JINDALSTEL.NS", "NMDC.NS", "HINDALCO.NS", "VEDL.NS", "NATIONALUM.NS", "HINDCOPPER.NS",
    "COALINDIA.NS", "MOIL.NS", "GMRINFRA.NS", "TNPL.NS", "JKPAPER.NS", "CENTURYPLY.NS", "GREENPLY.NS",
    "MARUTI.NS", "TMCV.NS", "M&M.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "TVSMOTORS.NS", 
    "EICHERMOT.NS", "ASHOKLEY.NS", "ESCORTS.NS", "FORCEMOT.NS", "MOTHERSON.NS", "BOSCHLTD.NS", 
    "BHARATFORG.NS", "APOLLOTYRE.NS", "MRF.NS", "BALKRISIND.NS", "EXIDEIND.NS", "SUNDRMFAST.NS",
    "VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS", "HAVELLS.NS", "CROMPTON.NS", "VGUARD.NS",
    "TITAN.NS", "KALYAN.NS", "SENCO.NS", "PCJEWELLER.NS", "KANSAINER.NS", "AKZOINDIA.NS",
    "PAGEIND.NS", "TRENT.NS", "RAYMOND.NS", "MANYAVAR.NS", "ARVIND.NS", "TRIDENT.NS", "KPR.NS", 
    "VARDHMAN.NS", "WELSPUNIND.NS", "ZEEL.NS", "SUNTV.NS", "NETWORK18.NS", "PVRINOX.NS", "NAZARA.NS", 
    "SAREGAMA.NS", "JAGRAN.NS", "DBCORP.NS", "HTMEDIA.NS", "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", 
    "PRESTIGE.NS", "SOBHA.NS", "BRIGADE.NS", "MAHLIFE.NS", "PHOENIXLTD.NS", "EMBASSY.NS", "MINDSPACE.NS",
    "INDHOTEL.NS", "LEMONTREE.NS", "CHALET.NS", "MAHINDRAHOLIDAYS.NS", "JUBLFOOD.NS", "DEVYANI.NS", 
    "WESTLIFE.NS", "SAPPHIRE.NS", "NYKAA.NS", "DMART.NS", "IRCTC.NS", "EASEMYTRIP.NS", 
    "THOMASCOOK.NS", "ONGC.NS", "OIL.NS", "RELIANCE.NS", "BPCL.NS", "IOC.NS", "HINDPETRO.NS",
    "IGL.NS", "MGL.NS", "GAIL.NS", "ATGL.NS", "GSPL.NS", "CASTROLIND.NS", "GUJARATGAS.NS",
    "HINDUNILVR.NS", "COLPAL.NS", "EMAMILTD.NS", "GILLETTE.NS", "BAJAJCON.NS", "GODREJCP.NS", 
    "JYOTHYLAB.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS", "BIKAJI.NS", "TATACONSUM.NS",
    "MCDOWELL-N.NS", "UBL.NS", "RADICO.NS", "GLOBUSSPR.NS", "ITC.NS", "GODFRYPHLP.NS", "VSTIND.NS",
    "HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS", 
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "RBLBANK.NS", "SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", 
    "UNIONBANK.NS", "INDIANB.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", 
    "MANAPPURAM.NS", "SHRIRAMFIN.NS", "LICHSGFIN.NS", "PNBHOUSING.NS", "CANFINHOME.NS", "HOMEFIRST.NS",
    "BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "KFINTECH.NS", "ANGELONE.NS", "360ONE.NS", "MOTILALOFS.NS", 
    "NUVAMA.NS", "SBILIFE.NS", "HDFCLIFE.NS", "LICI.NS", "MAXHEALTH.NS", "ICICIGI.NS", "NIACL.NS", 
    "GICRE.NS", "STARHEALTH.NS", "PAYTM.NS", "POLICYBZR.NS", "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", 
    "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS", "BIOCON.NS", "IPCA.NS", "ALKEM.NS", 
    "GRANULES.NS", "SUVEN.NS", "APOLLOHOSP.NS", "FORTIS.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "THYROCARE.NS",
    "HAL.NS", "BDL.NS", "BEML.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "PARAS.NS", "ABB.NS", "SIEMENS.NS", 
    "BHEL.NS", "CUMMINSIND.NS", "THERMAX.NS", "AIAENG.NS", "LT.NS", "NCC.NS", "KNRCON.NS", "PNCINFRA.NS", 
    "GRINFRA.NS", "POLYCAB.NS", "APLAPOLLO.NS", "SUPREMEIND.NS", "ASTRAL.NS", "FINOLEX.NS", "TCS.NS", 
    "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS",
    "FIRSTSOURCE.NS", "MASTEK.NS", "RATEGAIN.NS", "KPITTECH.NS", "INDIGO.NS", "BLUEDART.NS", 
    "DELHIVERY.NS", "MAHLOG.NS", "GESHIP.NS", "ADANIPORTS.NS", "CONCOR.NS", "BHARTIARTL.NS", "IDEA.NS", 
    "TATACOMM.NS", "RAILTEL.NS", "HFCL.NS", "TEJASNET.NS", "STLTECH.NS", "NTPC.NS", "TATAPOWER.NS", 
    "JSWENERGY.NS", "TORNTPOWER.NS", "CESC.NS", "POWERGRID.NS", "RECLTD.NS", "PFC.NS", "ADANIENSOL.NS"
]

YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS",
    "GUJARATGAS.NS": "GUJGASLTD.NS", "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS",
    "FINOLEX.NS": "FINCABLES.NS", "GMRINFRA.NS": "GMRAIRPORT.NS", 
    "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", "MAHINDRAHOLIDAYS.NS": "MHRIL.NS",
    "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", "IPCA.NS": "IPCALAB.NS"
}

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

def fetch_breadth_data():
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in UNIVERSE_SYMBOLS]
    symbols_space = " ".join(yahoo_symbols_to_download)
    
    try:
        print(f"Downloading 1-year data for Breadth dashboard ({len(UNIVERSE_SYMBOLS)} symbols)...")
        df = yf.download(symbols_space, period="1y", progress=False)
        
        # --- ROBUST DATA ALIGNMENT ---
        closes = df['Close'].ffill()                  
        closes = closes.dropna(how='all')             
        closes = closes.dropna(axis=1, how='all')     
        
        valid_cols = [c for c in closes.columns if c != '^NSEI']
        stocks_df = closes[valid_cols]
        total_tracked = len(valid_cols)
        
        if total_tracked == 0:
            print("Error: No valid stock data downloaded.")
            return

        print(f"Processing Breadth for {total_tracked} active stocks...\n")
        
        ema20 = stocks_df.ewm(span=20, adjust=False).mean()
        ema50 = stocks_df.ewm(span=50, adjust=False).mean()
        ema200 = stocks_df.ewm(span=200, adjust=False).mean()
        sma200 = stocks_df.rolling(window=200, min_periods=50).mean()
        high52 = stocks_df.rolling(window=252, min_periods=50).max()
        low52 = stocks_df.rolling(window=252, min_periods=50).min()
        
        curr_px = stocks_df.iloc[-1]
        px_1w = stocks_df.iloc[-5] if len(stocks_df) >= 5 else stocks_df.iloc[0]
        
        mul = 500 / total_tracked
        
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
        
        nifty = closes.get('^NSEI')
        if nifty is not None and not nifty.isna().all():
            nifty = nifty.dropna()
            n_curr = nifty.iloc[-1]
            n_1w = nifty.iloc[-5] if len(nifty) >= 5 else nifty.iloc[0]
            n_1m = nifty.iloc[-21] if len(nifty) >= 21 else nifty.iloc[0]
            
            overall["nifty500Change1W"] = round(((n_curr - n_1w) / n_1w) * 100, 2)
            overall["nifty500Change1M"] = round(((n_curr - n_1m) / n_1m) * 100, 2)
            
            n_ema50 = nifty.ewm(span=50).mean().iloc[-1]
            n_ema200 = nifty.ewm(span=200).mean().iloc[-1]
            golden_cross = bool(n_ema50 > n_ema200)
            death_cross = bool(n_ema50 < n_ema200)
        else:
            overall["nifty500Change1W"] = 0
            overall["nifty500Change1M"] = 0
            golden_cross = False
            death_cross = False
            print("Warning: Benchmark Nifty 50 (^NSEI) data was missing.")
            
        sectors_json = []
        print(f"{'Sector':<30} | {'Active/Target':<15} | {'% > EMA50':<12} | {'1W Change':<10}")
        print("-" * 75)
        
        for sec_name, sec_data in TARGET_SECTORS.items():
            sec_syms = [YAHOO_MAP.get(s, s) for s in sec_data["symbols"]]
            valid_sec_syms = [s for s in sec_syms if s in valid_cols]
            
            if valid_sec_syms:
                sec_df = stocks_df[valid_sec_syms]
                pct_above = (sec_df.iloc[-1] > ema50[valid_sec_syms].iloc[-1]).sum() / len(valid_sec_syms)
                
                sec_past_sum = sec_df.iloc[-5].sum() if len(sec_df) >= 5 else sec_df.iloc[0].sum()
                if sec_past_sum > 0:
                    sec_ret = ((sec_df.iloc[-1].sum() - sec_past_sum) / sec_past_sum) * 100
                else:
                    sec_ret = 0.0
                
                sectors_json.append({
                    "name": sec_name,
                    "total": sec_data["target_count"],
                    "aboveEma50": int(pct_above * sec_data["target_count"]),
                    "change1W": round(sec_ret, 2)
                })
                
                active_str = f"{len(valid_sec_syms)}/{len(sec_syms)}"
                pct_str = f"{round(pct_above * 100, 1)}%"
                ret_str = f"{round(sec_ret, 2)}%"
                print(f"{sec_name:<30} | {active_str:<15} | {pct_str:<12} | {ret_str:<10}")
                
        history_json = []
        for i in range(11, -1, -1):
            idx = -((i * 5) + 1)
            if abs(idx) <= len(stocks_df):
                h_pct = ((stocks_df.iloc[idx] > ema50.iloc[idx]).sum() / total_tracked) * 100
                history_json.append({"week": f"W{-i}" if i > 0 else "Curr", "breadth": round(h_pct, 1)})
                
        trend = "uptrend" if overall["nifty500Change1M"] > 2 else "downtrend" if overall["nifty500Change1M"] < -2 else "sideways"
        mom = int((overall["aboveEma20"] / 500) * 100)
        
        signals_json = {
            "goldenCross": golden_cross, 
            "deathCross": death_cross,
            "divergence": "none", 
            "trend": trend, 
            "momentumScore": mom,
            "breadthThrust": bool(mom > 70 and overall["nifty500Change1W"] > 2),
            "marketRegime": "risk-on" if trend == "uptrend" else "risk-off" if trend == "downtrend" else "neutral"
        }
        
        with open("breadth_data.json", "w") as outfile:
            json.dump({ 
                "overall": overall, 
                "sectors": sectors_json, 
                "history": history_json, 
                "signals": signals_json 
            }, outfile)
            
        print("\nSuccessfully generated breadth_data.json!")
            
    except Exception as e:
        print(f"\nBreadth Generator Error: {str(e)}")

if __name__ == "__main__":
    fetch_breadth_data()
