import yfinance as yf
import pandas as pd
import json

# The complete list of NSE symbols matching your React Dashboard
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

# The Translation Dictionary for Yahoo's weird spellings
YAHOO_MAP = {
    "VARDHMAN.NS": "VTL.NS",
    "FIRSTSOURCE.NS": "FSL.NS",
    "GUJARATGAS.NS": "GUJGASLTD.NS",
    "KALYAN.NS": "KALYANKJIL.NS",
    "TVSMOTORS.NS": "TVSMOTOR.NS",
    "FINOLEX.NS": "FINCABLES.NS",
    "GMRINFRA.NS": "GMRAIRPORT.NS",
    "WELSPUNIND.NS": "WELSPUNLIV.NS",
    "MCDOWELL-N.NS": "UNITDSPR.NS",
    "MAHINDRAHOLIDAYS.NS": "MHRIL.NS",
    "CHAMBALFERT.NS": "CHAMBLFERT.NS",
    "KPR.NS": "KPRMILL.NS",
    "IPCA.NS": "IPCALAB.NS"
}

def fetch_market_data():
    results = {}
    
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in UNIVERSE_SYMBOLS]
    symbols_space = " ".join(yahoo_symbols_to_download)
    
    try:
        print(f"Downloading data for {len(UNIVERSE_SYMBOLS)} symbols...\n")
        
        # Download data using the YAHOO symbols (4 months to ensure we have exactly 3 full months backward)
        df = yf.download(symbols_space, period="4mo", progress=False)
        closes = df['Close']
        
        # --- DATA ALIGNMENT & CLEANUP ---
        closes = closes.ffill()
        closes = closes.dropna(how='all')
        
        # Drop columns (symbols) that returned absolutely no data
        if isinstance(closes, pd.DataFrame):
            closes = closes.dropna(axis=1, how='all')
            valid_downloaded_symbols = set(closes.columns)
        else:
            valid_downloaded_symbols = {closes.name}
            closes = closes.to_frame()

        print(f"{'Symbol':<18} | {'1-Week Return':<15} | {'3-Month Return':<15}")
        print("-" * 55)
        
        for react_symbol in UNIVERSE_SYMBOLS:
            try:
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                if yahoo_symbol not in valid_downloaded_symbols:
                    print(f"{react_symbol:<18} | {'DROPPED (No Data)':<15} | {'-':<15}")
                    continue
                
                col = closes[yahoo_symbol].dropna()
                
                if len(col) < 5:
                    print(f"{react_symbol:<18} | {'DROPPED (< 5 days)':<15} | {'-':<15}")
                    continue 
                    
                current_date = col.index[-1]
                current_price = col.iloc[-1]
                
                # Using Exact Calendar Dates to match Yahoo Web
                target_1w = current_date - pd.Timedelta(days=7) 
                target_3m = current_date - pd.DateOffset(months=3) 
                
                price_1w = col.asof(target_1w)
                price_3m = col.asof(target_3m)
                
                if pd.isna(price_1w) or pd.isna(price_3m):
                    print(f"{react_symbol:<18} | {'DROPPED (Not enough history)':<28}")
                    continue 
                
                ret1w = ((current_price - price_1w) / price_1w) * 100
                ret3m = ((current_price - price_3m) / price_3m) * 100
                
                results[react_symbol] = {
                    "ret1w": round(float(ret1w), 2),
                    "ret3m": round(float(ret3m), 2)
                }
                
                print(f"{react_symbol:<18} | {results[react_symbol]['ret1w']:>13} % | {results[react_symbol]['ret3m']:>13} %")
                
            except Exception as e:
                print(f"{react_symbol:<18} | {'ERROR: ' + str(e):<15}")
                pass 
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile)
            
        print(f"\nSuccessfully generated market_data.json with {len(results)} active symbols.")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
