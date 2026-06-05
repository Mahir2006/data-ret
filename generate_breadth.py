import os
import json
import pandas as pd
import yfinance as yf

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

def generate_breadth_data():
    print("Starting TRUE market breadth calculation (500-stock universe)...")
    
    # Map symbols for downloading
    yahoo_symbols_to_download = [YAHOO_MAP.get(sym, sym) for sym in UNIVERSE_SYMBOLS]
    
    # Remove duplicates, add benchmark
    all_tickers = list(set(yahoo_symbols_to_download)) + ["^NSEI"]

    print(f"Downloading data for {len(all_tickers)} tickers...")
    
    try:
        # Multi-threading automatically enabled by yfinance for large lists
        data = yf.download(all_tickers, period="6m", interval="1d", progress=False)
    except Exception as e:
        print(f"Error downloading data from yfinance: {e}")
        return

    # Handle yfinance multi-index response
    closes = data['Adj Close'] if 'Adj Close' in data else data['Close']
    
    # Clean global data (forward fill to bridge single-day suspensions, drop market holidays)
    closes = closes.ffill().dropna(how='all')
    
    advancers = 0
    decliners = 0
    above_sma50 = 0
    above_sma200 = 0
    total_tracked = 0
    
    for react_symbol in UNIVERSE_SYMBOLS:
        yahoo_symbol = YAHOO_MAP.get(react_symbol, react_symbol)
        
        # Safely skip if ticker was delisted or un-fetchable
        if yahoo_symbol not in closes.columns:
            continue
            
        series = closes[yahoo_symbol].dropna()
        
        if len(series) < 5:  # Need at least a few days of data
            continue
            
        total_tracked += 1
        current_price = series.iloc[-1]
        previous_price = series.iloc[-2]
        
        # Advance / Decline Status
        if current_price > previous_price:
            advancers += 1
        elif current_price < previous_price:
            decliners += 1
            
        # Moving Average Status
        if len(series) >= 50:
            sma50 = series.rolling(window=50).mean().iloc[-1]
            if current_price > sma50:
                above_sma50 += 1
                
        if len(series) >= 200:
            sma200 = series.rolling(window=200).mean().iloc[-1]
            if current_price > sma200:
                above_sma200 += 1

    if total_tracked == 0:
        print("Error: No valid ticker data processed.")
        return

    print(f"Successfully processed {total_tracked} active stocks for breadth.")

    # 1:1 Math (No Multipliers)
    pct_above_sma50 = round((above_sma50 / total_tracked) * 100, 2)
    pct_above_sma200 = round((above_sma200 / total_tracked) * 100, 2)

    overall = {
        "advancers": advancers,
        "decliners": decliners,
        "unchanged": total_tracked - advancers - decliners,
        "totalStocks": total_tracked,
        "pctAboveSMA50": pct_above_sma50,
        "pctAboveSMA200": pct_above_sma200,
    }

    # Benchmark Performance Calculations (Exact Calendar Dates)
    nifty = closes.get('^NSEI')
    if nifty is not None and not nifty.isna().all():
        nifty = nifty.dropna()
        n_curr = nifty.iloc[-1]        
        current_date = nifty.index[-1] 
        
        target_1w = current_date - pd.Timedelta(days=7)
        target_1m = current_date - pd.DateOffset(months=1)
        
        n_1w = nifty.asof(target_1w)
        n_1m = nifty.asof(target_1m)
        
        overall["nifty500Change1W"] = round(((n_curr - n_1w) / n_1w) * 100, 2)
        overall["nifty500Change1M"] = round(((n_curr - n_1m) / n_1m) * 100, 2)
        
        n_ema50 = nifty.ewm(span=50).mean().iloc[-1]
        n_ema200 = nifty.ewm(span=200).mean().iloc[-1]
        overall["goldenCross"] = bool(n_ema50 > n_ema200)
        overall["deathCross"] = bool(n_ema50 < n_ema200)
    else:
        overall["nifty500Change1W"] = 0
        overall["nifty500Change1M"] = 0
        overall["goldenCross"] = False
        overall["deathCross"] = False
        print("Warning: Benchmark Nifty 50 (^NSEI) data was missing.")

    # Export to JSON
    output_filename = "breadth_data.json"
    try:
        with open(output_filename, "w") as f:
            json.dump(overall, f, indent=4)
        print(f"Success! Data saved to {output_filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    generate_breadth_data()
