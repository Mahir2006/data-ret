import yfinance as yf
import pandas as pd
import json
import time

# True Nifty 500 Universe (500 Most Liquid NSE Stocks)
UNIVERSE_SYMBOLS = [
    "360ONE.NS", "3MINDIA.NS", "AARTIIND.NS", "AAVAS.NS", "ABB.NS", "ABBOTINDIA.NS", "ABCAPITAL.NS", 
    "ABFRL.NS", "ACC.NS", "ADANIENSOL.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", 
    "ADANIPOWER.NS", "AEGISCHEM.NS", "AETHER.NS", "AFFLE.NS", "AIAENG.NS", "AJANTPHARM.NS", 
    "ALKEM.NS", "ALKYLAMINE.NS", "AMBER.NS", "AMBUJACEM.NS", "ANANDRATHI.NS", "ANGELONE.NS", 
    "ANURAS.NS", "APARINDS.NS", "APCOTEXIND.NS", "APLAPOLLO.NS", "APLLTD.NS", "APOLLOHOSP.NS", 
    "APOLLOTYRE.NS", "APTUS.NS", "ARVINDFASN.NS", "ARVIND.NS", "ASAHIINDIA.NS", "ASHOKLEY.NS", 
    "ASIANPAINT.NS", "ASTERDM.NS", "ASTRAL.NS", "ATGL.NS", "ATUL.NS", "AUBANK.NS", "AUROPHARMA.NS", 
    "AVANTIFEED.NS", "AWL.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJAJCON.NS", "BAJAJELEC.NS", 
    "BAJAJFINSV.NS", "BAJAJHLDNG.NS", "BAJFINANCE.NS", "BALAMINES.NS", "BALKRISIND.NS", 
    "BALRAMCHIN.NS", "BANDHANBNK.NS", "BANKBARODA.NS", "BANKINDIA.NS", "BATAINDIA.NS", "BDL.NS", 
    "BEL.NS", "BEML.NS", "BERGEPAINT.NS", "BHARATFORG.NS", "BHARTIARTL.NS", "BHEL.NS", "BIKAJI.NS", 
    "BIOCON.NS", "BIRLACORPN.NS", "BLUEDART.NS", "BLUESTARCO.NS", "BOSCHLTD.NS", "BPCL.NS", 
    "BRIGADE.NS", "BRITANNIA.NS", "BSE.NS", "BSOFT.NS", "CAMS.NS", "CANBK.NS", "CANFINHOME.NS", 
    "CAPLIPOINT.NS", "CARBORUNIV.NS", "CASTROLIND.NS", "CCL.NS", "CDSL.NS", "CEATLTD.NS", 
    "CENTRALBK.NS", "CENTURYPLY.NS", "CENTURYTEX.NS", "CERA.NS", "CESC.NS", "CGPOWER.NS", 
    "CHALET.NS", "CHAMBALFERT.NS", "CHEMPLASTS.NS", "CHENNPETRO.NS", "CHOLAFIN.NS", "CHOLAHLDNG.NS", 
    "CIEINDIA.NS", "CIPLA.NS", "CLEAN.NS", "COALINDIA.NS", "COCHINSHIP.NS", "COFORGE.NS", 
    "COLPAL.NS", "CAMS.NS", "CONCOR.NS", "COROMANDEL.NS", "CRAFTSMAN.NS", "CREDITACC.NS", 
    "CRISIL.NS", "CROMPTON.NS", "CUB.NS", "CUMMINSIND.NS", "CYIENT.NS", "DABUR.NS", "DALBHARAT.NS", 
    "DATAPATTNS.NS", "DBCORP.NS", "DCMSHRIRAM.NS", "DEEPAKNTR.NS", "DELHIVERY.NS", "DEVYANI.NS", 
    "DIVISLAB.NS", "DIXON.NS", "DLF.NS", "DMART.NS", "DRREDDY.NS", "EASEMYTRIP.NS", "ECLERX.NS", 
    "EICHERMOT.NS", "EIDPARRY.NS", "EIHOTEL.NS", "ELGIEQUIP.NS", "EMAMILTD.NS", "EMBASSY.NS", 
    "ENDURANCE.NS", "ENGINERSIN.NS", "EPL.NS", "EQUITASBNK.NS", "ERIS.NS", "ESCORTS.NS", 
    "EXIDEIND.NS", "FACT.NS", "FDC.NS", "FEDERALBNK.NS", "FERMENTA.NS", "FINEORG.NS", "FINOLEX.NS", 
    "FINPIPE.NS", "FIRSTSOURCE.NS", "FIVESTAR.NS", "FLOURISH.NS", "FORCEMOT.NS", "FORTIS.NS", 
    "GAIL.NS", "GARFIBRES.NS", "GEPIL.NS", "GESHIP.NS", "GHCL.NS", "GICRE.NS", "GILLETTE.NS", 
    "GLAND.NS", "GLAXO.NS", "GLENMARK.NS", "GLOBUSSPR.NS", "GMMPFAUDLR.NS", "GMRINFRA.NS", 
    "GNFC.NS", "GODFRYPHLP.NS", "GODREJAGRO.NS", "GODREJCP.NS", "GODREJIND.NS", "GODREJPROP.NS", 
    "GOKEX.NS", "GPIL.NS", "GRANULES.NS", "GRAPHITE.NS", "GRASIM.NS", "GREENPANEL.NS", 
    "GREENPLY.NS", "GRINDWELL.NS", "GRINFRA.NS", "GSFC.NS", "GSPL.NS", "GUJARATGAS.NS", 
    "GUJGASLTD.NS", "GUJALKALI.NS", "HAL.NS", "HAPPSTMNDS.NS", "HAVELLS.NS", "HCLTECH.NS", 
    "HDFCAMC.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HEG.NS", "HEROMOTOCO.NS", "HFCL.NS", "HGS.NS", 
    "HIKAL.NS", "HINDALCO.NS", "HINDCOPPER.NS", "HINDPETRO.NS", "HINDUNILVR.NS", "HINDZINC.NS", 
    "HITACHIQIE.NS", "HLEGLAS.NS", "HOMEFIRST.NS", "HONAUT.NS", "HTMEDIA.NS", "HUDCO.NS", 
    "ICICIBANK.NS", "ICICIGI.NS", "ICICIPRULI.NS", "IDBI.NS", "IDEA.NS", "IDFCFIRSTB.NS", 
    "IDFC.NS", "IEX.NS", "IGL.NS", "IIFL.NS", "INDHOTEL.NS", "INDIACEM.NS", "INDIAMART.NS", 
    "INDIANB.NS", "INDIGO.NS", "INDIGOPNTS.NS", "INDOCO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", 
    "INFIBEAM.NS", "INFY.NS", "INGERRAND.NS", "INOXCVA.NS", "INTELLECT.NS", "IOC.NS", "IOB.NS", 
    "IPCA.NS", "IRB.NS", "IRCON.NS", "IRCTC.NS", "IRFC.NS", "ISEC.NS", "ISGEC.NS", "ITC.NS", 
    "ITI.NS", "J&KBANK.NS", "JAGRAN.NS", "JAICORPLTD.NS", "JBCHEPHARM.NS", "JBMAUTO.NS", 
    "JINDALPHOT.NS", "JINDALSAW.NS", "JINDALSTEL.NS", "JIOFIN.NS", "JKCEMENT.NS", "JKPAPER.NS", 
    "JKTYRE.NS", "JSL.NS", "JSWENERGY.NS", "JSWINFRA.NS", "JSWSTEEL.NS", "JUBLFOOD.NS", 
    "JUBLINGREA.NS", "JUBLPHARMA.NS", "JUSTDIAL.NS", "JYOTHYLAB.NS", "KAJARIACER.NS", "KALYAN.NS", 
    "KANSAINER.NS", "KARURVYSYA.NS", "KAYNES.NS", "KEC.NS", "KEI.NS", "KFINTECH.NS", 
    "KIMS.NS", "KOTAKBANK.NS", "KPITTECH.NS", "KPR.NS", "KRBL.NS", "KSB.NS", "LALPATHLAB.NS", 
    "LATENTVIEW.NS", "LAURUSLABS.NS", "LEMONTREE.NS", "LICHSGFIN.NS", "LICI.NS", "LINDEINDIA.NS", 
    "LODHA.NS", "LT.NS", "LTIM.NS", "LTTS.NS", "LUPIN.NS", "LXCHEM.NS", "M&M.NS", "M&MFIN.NS", 
    "MACPOWER.NS", "MAHABLESHW.NS", "MAHLIFE.NS", "MAHLOG.NS", "MAHSCOOTER.NS", "MAHSEAMLES.NS", 
    "MANAPPURAM.NS", "MANINFRA.NS", "MANYAVAR.NS", "MAPMYINDIA.NS", "MARICO.NS", "MARUTI.NS", 
    "MASTEK.NS", "MAXHEALTH.NS", "MAZDOCK.NS", "MCDOWELL-N.NS", "MCX.NS", "MEDPLUS.NS", 
    "METROBRAND.NS", "METROPOLIS.NS", "MFSL.NS", "MGL.NS", "MHRIL.NS", "MINDSPACE.NS", "MINDAIND.NS", 
    "MOIL.NS", "MOTHERSON.NS", "MOTILALOFS.NS", "MPHASIS.NS", "MRF.NS", "MTARTECH.NS", "MUTHOOTFIN.NS", 
    "NATCOPHARM.NS", "NATIONALUM.NS", "NAUKRI.NS", "NAVINFLUOR.NS", "NAZARA.NS", "NBCC.NS", 
    "NCC.NS", "NEOGEN.NS", "NESTLEIND.NS", "NETWORK18.NS", "NH.NS", "NHPC.NS", "NIACL.NS", 
    "NLCINDIA.NS", "NMDC.NS", "NOCIL.NS", "NTPC.NS", "NUVAMA.NS", "NUVOCO.NS", "NYKAA.NS", 
    "OBEROIRLTY.NS", "OIL.NS", "OLECTRA.NS", "ONGC.NS", "ORIENTBELL.NS", "ORIENTELEC.NS", 
    "PAGEIND.NS", "PARADEEP.NS", "PARAS.NS", "PATANJALI.NS", "PAYTM.NS", "PCBL.NS", "PCJEWELLER.NS", 
    "PEL.NS", "PERSISTENT.NS", "PETRONET.NS", "PFC.NS", "PFIZER.NS", "PGHL.NS", "PHOENIXLTD.NS", 
    "PIDILITIND.NS", "PIIND.NS", "PNB.NS", "PNBHOUSING.NS", "PNCINFRA.NS", "POLICYBZR.NS", 
    "POLYCAB.NS", "POONAWALLA.NS", "POWERGRID.NS", "PPLPHARMA.NS", "PRAJIND.NS", "PRESTIGE.NS", 
    "PRINCEPIPE.NS", "PRSMJOHNSN.NS", "PVRINOX.NS", "QUESS.NS", "RADICO.NS", "RAILTEL.NS", 
    "RAIN.NS", "RAJESHEXPO.NS", "RALLIS.NS", "RAMCOCEM.NS", "RATEGAIN.NS", "RATNAMANI.NS", 
    "RAYMOND.NS", "RBLBANK.NS", "RECLTD.NS", "REDINGTON.NS", "RELAXO.NS", "RELIANCE.NS", 
    "RITES.NS", "ROLEXRINGS.NS", "ROSSARI.NS", "ROUTE.NS", "RSYSTEMS.NS", "RUCHISOYA.NS", 
    "RVNL.NS", "SAFOE.NS", "SAIL.NS", "SANOFI.NS", "SAPPHIRE.NS", "SAREGAMA.NS", "SBICARD.NS", 
    "SBILIFE.NS", "SBIN.NS", "SCHAEFFLER.NS", "SEAMEC.NS", "SENCO.NS", "SEQUENT.NS", "SFL.NS", 
    "SHARDACROP.NS", "SHOPERSTOP.NS", "SHREEPUSHK.NS", "SHREECEM.NS", "SHRIRAMFIN.NS", 
    "SHYAMMETL.NS", "SIEMENS.NS", "SIS.NS", "SJVN.NS", "SKFINDIA.NS", "SOBHA.NS", "SOLARINDS.NS", 
    "SONACOMS.NS", "SONATSOFTW.NS", "SOUTHBANK.NS", "SPANDANA.NS", "SRF.NS", "STAR.NS", 
    "STARHEALTH.NS", "STLTECH.NS", "SUMICHEM.NS", "SUNDARMFIN.NS", "SUNDRMFAST.NS", "SUNPHARMA.NS", 
    "SUNTV.NS", "SUPRAJIT.NS", "SUPREMEIND.NS", "SUVEN.NS", "SUVENPHAR.NS", "SWANENERGY.NS", 
    "SYMPHONY.NS", "SYNGENE.NS", "TATACHEM.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAELXSI.NS", 
    "TATAINVEST.NS", "TATAMOTORS.NS", "TATAMTRDVR.NS", "TATAPOWER.NS", "TATASTEEL.NS", "TCI.NS", 
    "TCIEXP.NS", "TCNSBRANDS.NS", "TCS.NS", "TEAMLEASE.NS", "TECHM.NS", "TEJASNET.NS", "THERMAX.NS", 
    "THOMASCOOK.NS", "THYROCARE.NS", "TIMKEN.NS", "TITAN.NS", "TMB.NS", "TMCV.NS", "TNPL.NS", 
    "TORNTPHARM.NS", "TORNTPOWER.NS", "TRENT.NS", "TRIDENT.NS", "TRITURBINE.NS", "TRIVENI.NS", 
    "TTKPRESTIG.NS", "TV18BRDCST.NS", "TVSMOTORS.NS", "UBL.NS", "UCOBANK.NS", "UJJIVANSFB.NS", 
    "ULTRACEMCO.NS", "UNIONBANK.NS", "UNOINDA.NS", "UPL.NS", "USHAMART.NS", "UTIAMC.NS", 
    "VAIBHAVGBL.NS", "VAKRANGEE.NS", "VARDHMAN.NS", "VARROC.NS", "VBL.NS", "VEDL.NS", "VENKEYS.NS", 
    "VESUVIUS.NS", "VGUARD.NS", "VINATIORGA.NS", "VIPIND.NS", "VOLTAS.NS", "VRLLOG.NS", 
    "VSTIND.NS", "WABAG.NS", "WELCORP.NS", "WELENT.NS", "WELSPUNIND.NS", "WESTLIFE.NS", 
    "WHIRLPOOL.NS", "WIPRO.NS", "WOCKPHARMA.NS", "YESBANK.NS", "YATHARTH.NS", "ZAXY.NS", 
    "ZEEL.NS", "ZENSARTECH.NS", "ZFCVINDIA.NS", "ZYDUSLIFE.NS", "ZYDUSWELL.NS"
]

# Translation mapping for specific Yahoo Finance eccentricities
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
    
    # Map symbols for downloading
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in UNIVERSE_SYMBOLS]
    
    # Remove duplicates
    all_tickers = list(set(yahoo_symbols_to_download))

    try:
        print(f"Downloading data for {len(all_tickers)} individual tickers (Chunked to prevent rate-limiting)...\n")
        
        chunk_size = 50
        closes_list = []
        
        for i in range(0, len(all_tickers), chunk_size):
            chunk = all_tickers[i:i + chunk_size]
            print(f"Fetching batch {(i//chunk_size) + 1}/{(len(all_tickers)//chunk_size) + 1}...")
            
            # Download chunk with threads=False to stay under API limits
            df = yf.download(chunk, period="4mo", interval="1d", progress=False, threads=False)
            
            if df.empty:
                print(f"  -> Warning: Batch {(i//chunk_size) + 1} returned completely empty data.")
                continue
                
            # --- ROBUST MULTI-INDEX HANDLING ---
            # yfinance alters its column structure frequently. This guarantees we isolate the correct price level.
            if isinstance(df.columns, pd.MultiIndex):
                if 'Adj Close' in df.columns.get_level_values(0) or 'Close' in df.columns.get_level_values(0):
                    c = df['Adj Close'] if 'Adj Close' in df.columns.get_level_values(0) else df['Close']
                else:
                    c = df.xs('Adj Close', level=1, axis=1) if 'Adj Close' in df.columns.get_level_values(1) else df.xs('Close', level=1, axis=1)
            else:
                c = df[['Adj Close']] if 'Adj Close' in df.columns else df[['Close']]
                if len(chunk) == 1:
                    c.columns = [chunk[0]]
            
            closes_list.append(c)
            time.sleep(1.5)  # Breathe to prevent Yahoo IP Ban
            
        if not closes_list:
            print("\nFatal Error: All downloads were blocked by Yahoo API.")
            return
            
        # Combine all successful chunks into one global dataframe
        closes = pd.concat(closes_list, axis=1)
        
        # --- DATA ALIGNMENT & CLEANUP ---
        closes = closes.ffill()
        closes = closes.dropna(how='all')
        
        if isinstance(closes, pd.DataFrame):
            # Drop duplicated columns if any chunks overlapped
            closes = closes.loc[:, ~closes.columns.duplicated()]
            closes = closes.dropna(axis=1, how='all')
            valid_downloaded_symbols = set(closes.columns)
        else:
            valid_downloaded_symbols = {closes.name}
            closes = closes.to_frame()

        print(f"\n{'Symbol':<18} | {'1-Week Return':<15} | {'3-Month Return':<15}")
        print("-" * 55)
        
        for react_symbol in UNIVERSE_SYMBOLS:
            try:
                yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
                
                # If a symbol is completely un-fetchable or actively delisted
                if yahoo_symbol not in valid_downloaded_symbols:
                    print(f"{react_symbol:<18} | {'DROPPED (API Block / Delisted)':<28}")
                    continue
                
                col = closes[yahoo_symbol].dropna()
                
                # If a symbol just IPO'd within the last week
                if len(col) < 5:
                    print(f"{react_symbol:<18} | {'DROPPED (< 5 days of data)':<28}")
                    continue 
                    
                current_date = col.index[-1]
                current_price = col.iloc[-1]
                
                # Using Exact Calendar Dates to match Yahoo Web
                target_1w = current_date - pd.Timedelta(days=7) 
                target_3m = current_date - pd.DateOffset(months=3) 
                
                price_1w = col.asof(target_1w)
                price_3m = col.asof(target_3m)
                
                # If a symbol IPO'd within the last 3 months
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
                print(f"{react_symbol:<18} | ERROR: {str(e)}")
                
        with open("market_data.json", "w") as outfile:
            json.dump(results, outfile, indent=4)
            
        print(f"\nSuccessfully generated market_data.json with {len(results)} active symbols.")
            
    except Exception as e:
        print(f"Global Error: {str(e)}")

if __name__ == "__main__":
    fetch_market_data()
