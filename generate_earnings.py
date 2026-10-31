import yfinance as yf
import pandas as pd
import json
import datetime
import numpy as np
import time
import requests
import io
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── HELPER: SAFE MEAN FOR JSON SERIALIZATION ──────────────────────────────────
def safe_mean(lst):
    clean = [x for x in lst if not pd.isna(x)]
    return round(float(np.mean(clean)), 1) if clean else 0.0

# ─── 1. FETCH LIVE NIFTY 500 FROM NSE ───────────────────────────────────────────
def get_live_nifty_500():
    print("Fetching live Nifty 500 constituents from NSE...")
    
    urls = [
        "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
        "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    ]
    
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
    
    for url in urls:
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200 and "<html" not in response.text.lower()[:500]:
                df = pd.read_csv(io.StringIO(response.text))
                # Clean trailing spaces in headers just in case
                df.columns = df.columns.str.strip()
                df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
                df['YF_Symbol'] = df['Symbol'].astype(str).str.strip() + ".NS"
                return df
        except Exception as e:
            print(f"Warning: Failed to fetch from {url} - {e}")
            
    print("Fatal Error: Could not fetch NSE data from any endpoint.")
    return pd.DataFrame()

# ─── 2. BUILD DYNAMIC HIERARCHY ────────────────────────────────────────────────
def build_dynamic_hierarchy():
    df = get_live_nifty_500()
    if df.empty:
        print("WARNING: Using empty hierarchy due to fetch failure.")
        return []

    hierarchy = []
    grouped = df.groupby('Industry')
    colors = ["#818cf8", "#38bdf8", "#fbbf24", "#f97316", "#4ade80", "#fb923c", "#a3e635", "#94a3b8", "#f472b6", "#e2e8f0", "#c084fc", "#60a5fa", "#34d399"]
    
    for i, (industry_name, group) in enumerate(grouped):
        stocks = group['YF_Symbol'].tolist()
        
        industry_node = {
            "name": str(industry_name).strip(),
            "color": colors[i % len(colors)],
            "weight": round((len(stocks) / 500) * 100, 2),
            "industries": [
                {
                    "name": "General Equities", 
                    "subIndustries": [
                        {
                            "name": "All Stocks",
                            "stocks": stocks
                        }
                    ]
                }
            ]
        }
        hierarchy.append(industry_node)
        
    return hierarchy

# ─── 3. DYNAMIC QUARTER CALCULATOR WITH DATE TRACKING ──────────────────────────
def get_dynamic_quarters():
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    if 4 <= month <= 6:
        # Apr-Jun (Reporting Jan-Mar of previous FY)
        curr_q, prev_q = f"Q4 FY{str(year-1)[2:]}", f"Q3 FY{str(year-1)[2:]}"
        curr_per, prev_per = "Jan–Mar", "Oct–Dec"
        expected_m, expected_y = 3, year
    elif 7 <= month <= 9:
        # Jul-Sep (Reporting Apr-Jun of current FY)
        curr_q, prev_q = f"Q1 FY{str(year)[2:]}", f"Q4 FY{str(year-1)[2:]}"
        curr_per, prev_per = "Apr–Jun", "Jan–Mar"
        expected_m, expected_y = 6, year
    elif 10 <= month <= 12:
        # Oct-Dec (Reporting Jul-Sep of current FY)
        curr_q, prev_q = f"Q2 FY{str(year)[2:]}", f"Q1 FY{str(year)[2:]}"
        curr_per, prev_per = "Jul–Sep", "Apr–Jun"
        expected_m, expected_y = 9, year
    else: # Jan to Mar
        # Jan-Mar (Reporting Oct-Dec of current FY, but year has rolled over)
        curr_q, prev_q = f"Q3 FY{str(year-1)[2:]}", f"Q2 FY{str(year-1)[2:]}"
        curr_per, prev_per = "Oct–Dec", "Jul–Sep"
        expected_m, expected_y = 12, year - 1
        
    return {
        "prev": prev_q,
        "curr": curr_q,
        "prevPeriod": prev_per,
        "currPeriod": curr_per,
        "expected_month": expected_m,
        "expected_year": expected_y
    }
def get_yf_sym(sym):
    fixes = {
        "VARDHMAN.NS": "VTL.NS", "FIRSTSOURCE.NS": "FSL.NS", "GUJARATGAS.NS": "GUJGASLTD.NS", 
        "KALYAN.NS": "KALYANKJIL.NS", "TVSMOTORS.NS": "TVSMOTOR.NS", "FINOLEX.NS": "FINCABLES.NS", 
        "GMRINFRA.NS": "GMRAIRPORT.NS", "WELSPUNIND.NS": "WELSPUNLIV.NS", "MCDOWELL-N.NS": "UNITDSPR.NS", 
        "MAHINDRAHOLIDAYS.NS": "MHRIL.NS", "CHAMBALFERT.NS": "CHAMBLFERT.NS", "KPR.NS": "KPRMILL.NS", 
        "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS",
        "BAGMANE.NS": "BAGMANE.RR", "ICICILIFE.NS": "ICICIPRULI.NS"
    }
    return fixes.get(sym, sym)

# ─── 4. AUTHENTIC DATA EXTRACTION WITH UNREPORTED DETECTION ───────────────────
def fetch_stock_data(symbol, expected_month, expected_year):
    yf_sym = get_yf_sym(symbol)
    ticker = yf.Ticker(yf_sym)
    time.sleep(0.1) # Reduced sleep to speed up extraction slightly
    
    try:
        q_income = ticker.quarterly_income_stmt
        if q_income is None or q_income.empty:
            q_income = ticker.quarterly_financials # Fallback
            
        info = ticker.info
        
        if q_income is None or q_income.empty or len(q_income.columns) < 2:
            return {"reported": False, "pat_q4": 0, "pat_q3": 0, "rev_q4": 0, "rev_q3": 0, "ebitda_q4": 0, "ebitda_q3": 0, "npm_q4": 0, "npm_q3": 0, "roe": 0}

        # Resilient date matching
        latest_date = pd.to_datetime(q_income.columns[0])
        if latest_date.tzinfo is not None:
            latest_date = latest_date.tz_localize(None) # Strip timezone for safe comparison
            
        expected_q_end = pd.Timestamp(year=expected_year, month=expected_month, day=1) + pd.offsets.MonthEnd(0)
        has_reported = abs((latest_date - expected_q_end).days) <= 15

        def get_row(df, possible_names):
            for name in possible_names:
                if name in df.index:
                    return df.loc[name].fillna(0).tolist()
            return [0] * len(df.columns)

        net_income = get_row(q_income, ["NetIncome", "Net Income", "Net Income Common Stockholders"])
        revenue = get_row(q_income, ["TotalRevenue", "Total Revenue", "Operating Revenue"])
        ebitda = get_row(q_income, ["EBITDA", "Ebitda", "Operating Income"])

        def calc_growth(curr, prev):
            if pd.isna(prev) or prev == 0 or prev is None: return 0
            if pd.isna(curr): return 0
            return ((curr - prev) / abs(prev)) * 100

        roe_raw = info.get('returnOnEquity', 0)
        roe_val = round(roe_raw * 100, 1) if roe_raw is not None else 0

        if has_reported:
            # Shift processing indices: 0 is current quarter, 1 is previous quarter
            pat_q4_gr = calc_growth(net_income[0], net_income[1])
            pat_q3_gr = calc_growth(net_income[1], net_income[2] if len(net_income) > 2 else net_income[1])
            rev_q4_gr = calc_growth(revenue[0], revenue[1])
            rev_q3_gr = calc_growth(revenue[1], revenue[2] if len(revenue) > 2 else revenue[1])
            ebitda_q4_gr = calc_growth(ebitda[0], ebitda[1])
            ebitda_q3_gr = calc_growth(ebitda[1], ebitda[2] if len(ebitda) > 2 else ebitda[1])
            
            npm_q4 = (net_income[0] / revenue[0] * 100) if revenue[0] != 0 else 0
            npm_q3 = (net_income[1] / revenue[1] * 100) if len(revenue) > 1 and revenue[1] != 0 else 0
            
            return {
                "reported": True,
                "pat_q4": round(pat_q4_gr, 1), "pat_q3": round(pat_q3_gr, 1),
                "rev_q4": round(rev_q4_gr, 1), "rev_q3": round(rev_q3_gr, 1),
                "ebitda_q4": round(ebitda_q4_gr, 1), "ebitda_q3": round(ebitda_q3_gr, 1),
                "npm_q4": round(npm_q4, 1), "npm_q3": round(npm_q3, 1), "roe": roe_val
            }
        else:
            # If unreported, current metrics remain blank, historical fields fall back to index 0 vs 1
            pat_q3_gr = calc_growth(net_income[0], net_income[1])
            rev_q3_gr = calc_growth(revenue[0], revenue[1])
            ebitda_q3_gr = calc_growth(ebitda[0], ebitda[1])
            npm_q3 = (net_income[0] / revenue[0] * 100) if revenue[0] != 0 else 0
            
            return {
                "reported": False,
                "pat_q4": 0, "pat_q3": round(pat_q3_gr, 1),
                "rev_q4": 0, "rev_q3": round(rev_q3_gr, 1),
                "ebitda_q4": 0, "ebitda_q3": round(ebitda_q3_gr, 1),
                "npm_q4": 0, "npm_q3": round(npm_q3, 1), "roe": roe_val
            }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return {"reported": False, "pat_q4": 0, "pat_q3": 0, "rev_q4": 0, "rev_q3": 0, "ebitda_q4": 0, "ebitda_q3": 0, "npm_q4": 0, "npm_q3": 0, "roe": 0}

# ─── 5. JSON GENERATION WITH LIVE METRIC COUNTERS ──────────────────────────────
def generate_earnings():
    HIERARCHY = build_dynamic_hierarchy()
    if not HIERARCHY: return
        
    quarter_info = get_dynamic_quarters()
    sectors_json = []
    global_tot, global_rpt, global_beat, global_miss, global_neu = 0, 0, 0, 0, 0
    
    for sec in HIERARCHY:
        print(f"Processing Sector: {sec['name']}...")
        sec_inds = []
        sec_tot_stocks, sec_reported, sec_beat, sec_miss, sec_neu = 0, 0, 0, 0, 0
        s_q3_pat, s_q4_pat, s_q3_rev, s_q4_rev, s_q3_ebitda, s_q4_ebitda, s_q3_npm, s_q4_npm, s_roe = [], [], [], [], [], [], [], [], []
        
        for ind in sec["industries"]:
            ind_subs = []
            i_tot_stocks, i_reported, i_beat, i_miss, i_neu = 0, 0, 0, 0, 0
            i_q3_pat, i_q4_pat, i_q3_rev, i_q4_rev = [], [], [], []
            
            for sub in ind["subIndustries"]:
                sub_tot = len(sub["stocks"])
                sub_reported, sub_beat, sub_miss, sub_neu = 0, 0, 0, 0
                sq3_pat, sq4_pat = [], []
                
                for sym in sub["stocks"]:
                    data = fetch_stock_data(sym, quarter_info["expected_month"], quarter_info["expected_year"])
                    
                    # Accumulate current metrics ONLY if company has released numbers
                    if data["reported"]:
                        sub_reported += 1
                        if data["pat_q4"] > 2: sub_beat += 1
                        elif data["pat_q4"] < -2: sub_miss += 1
                        else: sub_neu += 1
                        
                        sq4_pat.append(data["pat_q4"])
                        s_q4_pat.append(data["pat_q4"])
                        s_q4_rev.append(data["rev_q4"])
                        s_q4_ebitda.append(data["ebitda_q4"])
                        s_q4_npm.append(data["npm_q4"])
                        i_q4_pat.append(data["pat_q4"])
                        i_q4_rev.append(data["rev_q4"])
                    
                    # Historical reference sets remain filled regardless
                    sq3_pat.append(data["pat_q3"])
                    s_q3_pat.append(data["pat_q3"])
                    s_q3_rev.append(data["rev_q3"])
                    s_q3_ebitda.append(data["ebitda_q3"])
                    s_q3_npm.append(data["npm_q3"])
                    s_roe.append(data["roe"])
                    i_q3_pat.append(data["pat_q3"])
                    i_q3_rev.append(data["rev_q3"])

                avg_sq4 = safe_mean(sq4_pat)
                verdict = "Good" if avg_sq4 > 2 else "Bad" if avg_sq4 < -2 else "Neutral"
                if sub_reported == 0: verdict = "Neutral"
                
                ind_subs.append({
                    "name": sub["name"], "stocks": sub_tot, "reported": sub_reported,
                    "beat": sub_beat, "miss": sub_miss, "neutral": sub_neu,
                    "q3Pat": safe_mean(sq3_pat),
                    "q4Pat": avg_sq4, "verdict": verdict
                })
                
                i_tot_stocks += sub_tot; i_reported += sub_reported
                i_beat += sub_beat; i_miss += sub_miss; i_neu += sub_neu
            
            avg_iq4 = safe_mean(i_q4_pat)
            ind_verdict = "Good" if avg_iq4 > 2 else "Bad" if avg_iq4 < -2 else "Neutral"
            if i_reported == 0: ind_verdict = "Neutral"
            
            sec_inds.append({
                "name": ind["name"], "totalStocks": i_tot_stocks, "reported": i_reported,
                "beat": i_beat, "miss": i_miss, "neutral": i_neu,
                "q3Pat": safe_mean(i_q3_pat),
                "q4Pat": avg_iq4,
                "q3Rev": safe_mean(i_q3_rev),
                "q4Rev": safe_mean(i_q4_rev),
                "verdict": ind_verdict, "subIndustries": ind_subs
            })
            
            sec_tot_stocks += i_tot_stocks; sec_reported += i_reported
            sec_beat += i_beat; sec_miss += i_miss; sec_neu += i_neu

        avg_sq4 = safe_mean(s_q4_pat)
        sec_verdict = "Good" if avg_sq4 > 2 else "Bad" if avg_sq4 < -2 else "Neutral"
        if sec_reported == 0: sec_verdict = "Neutral"
        
        sectors_json.append({
            "name": sec["name"], "color": sec["color"], "weight": sec["weight"],
            "totalStocks": sec_tot_stocks, "reported": sec_reported,
            "beat": sec_beat, "miss": sec_miss, "neutral": sec_neu,
            "q3Pat": safe_mean(s_q3_pat),
            "q4Pat": avg_sq4,
            "q3Rev": safe_mean(s_q3_rev),
            "q4Rev": safe_mean(s_q4_rev),
            "q3Ebitda": safe_mean(s_q3_ebitda),
            "q4Ebitda": safe_mean(s_q4_ebitda),
            "q3Npm": safe_mean(s_q3_npm),
            "q4Npm": safe_mean(s_q4_npm),
            "q3Roe": safe_mean(s_roe),
            "q4Roe": safe_mean(s_roe),
            "verdict": sec_verdict, "industries": sec_inds
        })
        
        global_tot += sec_tot_stocks; global_rpt += sec_reported
        global_beat += sec_beat; global_miss += sec_miss; global_neu += sec_neu

    final_json = {
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "quarter": {
            "prev": quarter_info["prev"], "curr": quarter_info["curr"],
            "prevPeriod": quarter_info["prevPeriod"], "currPeriod": quarter_info["currPeriod"]
        },
        "totals": {
            "universe": global_tot, "reported": global_rpt, 
            "pending": max(0, global_tot - global_rpt),
            "beat": global_beat, "miss": global_miss, "neutral": global_neu
        },
        "sectors": sectors_json
    }
    
    with open("earnings_data.json", "w") as f:
        json.dump(final_json, f)
    print("✅ Done! JSON metrics generated successfully.")

if __name__ == "__main__":
    generate_earnings()
