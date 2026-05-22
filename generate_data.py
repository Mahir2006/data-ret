import yfinance as yf
import json
import os

# The complete list of NSE symbols matching your React Dashboard
UNIVERSE_SYMBOLS = [
    "^NSEI", # Nifty 50 Benchmark
    
    # Chemicals
    "PIDILITIND.NS", "SRF.NS", "DEEPAKNTR.NS", "NAVINFLUOR.NS", "AARTIIND.NS", "ATUL.NS",
    "AAVAS.NS", "GHCL.NS", "TATACHEM.NS", "APCOTEXIND.NS", "UPL.NS", "PIIND.NS",
    "RALLIS.NS", "COROMANDEL.NS", "CHAMBALFERT.NS", "GSFC.NS",
    
    # Construction Materials
    "ULTRACEMCO.NS", "GRASIM.NS", "AMBUJACEM.NS", "ACC.NS", "JKCEMENT.NS",
    "RAMCOCEM.NS", "SHREECEM.NS", "KAJARIACER.NS", "ORIENTBELL.NS", "ASIANPAINT.NS",
    
    # Metals & Mining
    "TATASTEEL.NS", "JSWSTEEL.NS", "SAIL.NS", "JINDALSTEL.NS", "NMDC.NS",
    "HINDALCO.NS", "VEDL.NS", "NATIONALUM.NS", "HINDCOPPER.NS",
    "COALINDIA.NS", "MOIL.NS", "GMRINFRA.NS",
    
    # Forest & Paper
    "TNPL.NS", "JKPAPER.NS", "CENTURYPLY.NS", "GREENPLY.NS",
    
    # Automobiles
    "MARUTI.NS", "TMCV.NS", "M&M.NS",
    "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "TVSMOTORS.NS", "EICHERMOT.NS",
    "ASHOKLEY.NS", "ESCORTS.NS", "FORCEMOT.NS",
    "MOTHERSON.NS", "BOSCHLTD.NS", "BHARATFORG.NS", "APOLLOTYRE.NS", "MRF.NS", "BALKRISIND.NS", "EXIDEIND.NS", "SUNDRMFAST.NS",
    
    # Consumer Durables
    "VOLTAS.NS", "BLUESTARCO.NS", "WHIRLPOOL.NS", "HAVELLS.NS", "CROMPTON.NS", "VGUARD.NS",
    "TITAN.NS", "KALYAN.NS", "SENCO.NS", "PCJEWELLER.NS",
    "KANSAINER.NS", "AKZOINDIA.NS",
    
    # Textiles & Apparel
    "PAGEIND.NS", "TRENT.NS", "RAYMOND.NS", "MANYAVAR.NS",
    "ARVIND.NS", "TRIDENT.NS", "KPR.NS", "VARDHMAN.NS", "WELSPUNIND.NS",
    
    # Media & Entertainment
    "ZEEL.NS", "SUNTV.NS", "NETWORK18.NS",
    "PVRINOX.NS", "NAZARA.NS", "SAREGAMA.NS",
    "JAGRAN.NS", "DBCORP.NS", "HTMEDIA.NS",
    
    # Real Estate
    "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PRESTIGE.NS", "SOBHA.NS", "BRIGADE.NS", "MAHLIFE.NS",
    "PHOENIXLTD.NS", "EMBASSY.NS", "MINDSPACE.NS",
    
    # Consumer Services
    "INDHOTEL.NS", "LEMONTREE.NS", "CHALET.NS", "MAHINDRAHOLIDAYS.NS",
    "JUBLFOOD.NS", "DEVYANI.NS", "WESTLIFE.NS", "SAPPHIRE.NS",
    "NYKAA.NS", "DMART.NS",
    "IRCTC.NS", "EASEMYTRIP.NS", "THOMASCOOK.NS",
    
    # Energy
    "ONGC.NS", "OIL.NS",
    "RELIANCE.NS", "BPCL.NS", "IOC.NS", "HINDPETRO.NS",
    "IGL.NS", "MGL.NS", "GAIL.NS", "ATGL.NS", "GSPL.NS",
    "CASTROLIND.NS", "GUJARATGAS.NS",
    
    # FMCG
    "HINDUNILVR.NS", "COLPAL.NS", "EMAMILTD.NS", "GILLETTE.NS", "BAJAJCON.NS",
    "GODREJCP.NS", "JYOTHYLAB.NS",
    "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS", "MARICO.NS", "BIKAJI.NS", "TATACONSUM.NS",
    "MCDOWELL-N.NS", "UBL.NS", "RADICO.NS", "GLOBUSSPR.NS",
    "ITC.NS", "GODFRYPHLP.NS", "VSTIND.NS",
    
    # Financial Services
    "HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "BANDHANBNK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS", "RBLBANK.NS",
    "SBIN.NS", "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "UNIONBANK.NS", "INDIANB.NS",
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "CHOLAFIN.NS", "MUTHOOTFIN.NS", "MANAPPURAM.NS", "SHRIRAMFIN.NS",
    "LICHSGFIN.NS", "PNBHOUSING.NS", "CANFINHOME.NS", "HOMEFIRST.NS",
    "BSE.NS", "MCX.NS", "CDSL.NS", "CAMS.NS", "KFINTECH.NS",
    "ANGELONE.NS", "360ONE.NS", "MOTILALOFS.NS", "NUVAMA.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "LICI.NS", "MAXHEALTH.NS",
    "ICICIGI.NS", "NIACL.NS", "GICRE.NS", "STARHEALTH.NS",
    "PAYTM.NS", "POLICYBZR.NS",
    
    # Healthcare
    "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "LUPIN.NS", "AUROPHARMA.NS", "TORNTPHARM.NS",
    "BIOCON.NS", "IPCA.NS", "ALKEM.NS", "GRANULES.NS", "SUVEN.NS",
    "APOLLOHOSP.NS", "FORTIS.NS", "METROPOLIS.NS", "LALPATHLAB.NS", "THYROCARE.NS",
    
    # Industrials
    "HAL.NS", "BDL.NS", "BEML.NS", "COCHINSHIP.NS", "MAZDOCK.NS", "PARAS.NS",
    "ABB.NS", "SIEMENS.NS", "BHEL.NS", "CUMMINSIND.NS", "THERMAX.NS", "AIAENG.NS",
    "LT.NS", "NCC.NS", "KNRCON.NS", "PNCINFRA.NS", "GRINFRA.NS",
    "POLYCAB.NS", "APLAPOLLO.NS", "SUPREMEIND.NS", "ASTRAL.NS", "FINOLEX.NS",
    
    # Information Technology
    "TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS",
    "MPHASIS.NS", "PERSISTENT.NS", "COFORGE.NS",
    "FIRSTSOURCE.NS", "MASTEK.NS", "RATEGAIN.NS", "KPITTECH.NS",
    
    # Services
    "INDIGO.NS", 
    "BLUEDART.NS", "DELHIVERY.NS", "MAHLOG.NS", "GESHIP.NS",
    "ADANIPORTS.NS", "CONCOR.NS", 
    
    # Telecom
    "BHARTIARTL.NS", "IDEA.NS", "TATACOMM.NS", "RAILTEL.NS",
    "HFCL.NS", "TEJASNET.NS", "STLTECH.NS",
    
    # Utilities
    "NTPC.NS", "TATAPOWER.NS", "JSWENERGY.NS", "TORNTPOWER.NS", "CESC.NS",
    "POWERGRID.NS", "RECLTD.NS", "PFC.NS", "ADANIENSOL.NS"
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
    
    # Create a list of the actual Yahoo symbols to download
    yahoo_symbols_to_download = []
    for sym in UNIVERSE_SYMBOLS:
        yahoo_symbols_to_download.append(YAHOO_MAP.get(sym, sym))
        
    symbols_space = " ".join(yahoo_symbols_to_download)
    
    try:
        print(f"Downloading data for {len(UNIVERSE_SYMBOLS)} symbols...")
        # We download using the YAHOO symbols
        df = yf.download(symbols_space, period="3mo", progress=False)
        closes = df['Close']
        
        for react_symbol in UNIVERSE_SYMBOLS:
            try:
                # We look up the data using the YAHOO symbol
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                col = closes if len(UNIVERSE_SYMBOLS) == 1 else closes[yahoo_symbol]
                col = col.dropna()
                
                if len(col) < 5:
                    continue 
                    
                current_price = col.iloc[-1]
                price_1w = col.iloc[-5] 
                price_3m = col.iloc[0] 
                
                ret1w = ((current_price - price_1w) / price_1w) * 100
                ret3m = ((current_price - price_3m) / price_3m) * 100
                
                # But we SAVE the data under the original REACT symbol!
                results[react_symbol] = {
                    "ret1w": round(float(ret1w), 2),
                    "ret3m": round(float(ret3m), 2)
                }
            except Exception:
                pass 
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile)
        print("Successfully generated market_data.json")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
