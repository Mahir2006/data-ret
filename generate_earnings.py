import yfinance as yf
import pandas as pd
import json
import datetime
import numpy as np
import time
import requests
import io

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
            return pd.DataFrame()
            
        df = pd.read_csv(io.StringIO(response.text))
        df = df[~df['Symbol'].str.contains("DUMMY", case=False, na=False)]
        df['YF_Symbol'] = df['Symbol'].astype(str).str.strip() + ".NS"
        return df
    except Exception as e:
        print(f"Error fetching NSE list: {e}")
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
        curr_q, prev_q = f"Q4 FY{str(year)[2:]}", f"Q3 FY{str(year)[2:]}"
        curr_per, prev_per = "Jan–Mar", "Oct–Dec"
        expected_m, expected_y = 3, year
    elif 7 <= month <= 9:
        curr_q, prev_q = f"Q1 FY{str(year+1)[2:]}", f"Q4 FY{str(year)[2:]}"
        curr_per, prev_per = "Apr–Jun", "Jan–Mar"
        expected_m, expected_y = 6, year
    elif 10 <= month <= 12:
        curr_q, prev_q = f"Q2 FY{str(year+1)[2:]}", f"Q1 FY{str(year+1)[2:]}"
        curr_per, prev_per = "Jul–Sep", "Apr–Jun"
        expected_m, expected_y = 9, year
    else: # Jan to Mar
        curr_q, prev_q = f"Q3 FY{str(year)[2:]}", f"Q2 FY{str(year)[2:]}"
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
        "IPCA.NS": "IPCALAB.NS", "M&M.NS": "M&M.NS", "BAJAJ-AUTO.NS": "BAJAJ-AUTO.NS"
    }
    return fixes.get(sym, sym)

# ─── 4. AUTHENTIC DATA EXTRACTION WITH UNREPORTED DETECTION ───────────────────
def fetch_stock_data(symbol, expected_month, expected_year):
    yf_sym = get_yf_sym(symbol)
    ticker = yf.Ticker(yf_sym)
    time.sleep(0.5)
    
    try:
        q_income = ticker.quarterly_income_stmt
        info = ticker.info
        
        if q_income is None or q_income.empty or len(q_income.columns) < 2:
            return {"reported": False, "pat_q4": 0, "pat_q3": 0, "rev_q4": 0, "rev_q3": 0, "ebitda_q4": 0, "ebitda_q3": 0, "npm_q4": 0, "npm_q3": 0, "roe": 0}

        # Check column timestamp to verify if current season has been filed
        latest_date = q_income.columns[0]
        has_reported = (latest_date.month == expected_month and latest_date.year == expected_year)

        def get_row(df, possible_names):
            for name in possible_names:
                if name in df.index:
                    return df.loc[name].fillna(0).tolist()
            return [0] * len(df.columns)

        net_income = get_row(q_income, ["NetIncome", "Net Income", "Net Income Common Stockholders"])
        revenue = get_row(q_income, ["TotalRevenue", "Total Revenue", "Operating Revenue"])
        ebitda = get_row(q_income, ["EBITDA", "Ebitda", "Operating Income"])

        def calc_growth(curr, prev):
            if prev == 0 or prev is None: return 0
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
                    
                    # Historical reference sets remain filled regardless
                    sq3_pat.append(data["pat_q3"])
                    s_q3_pat.append(data["pat_q3"])
                    s_q3_rev.append(data["rev_q3"])
                    s_q3_ebitda.append(data["ebitda_q3"])
                    s_q3_npm.append(data["npm_q3"])
                    s_roe.append(data["roe"])
                    i_q3_pat.append(data["pat_q3"])
                    i_q3_rev.append(data["rev_q3"])

                avg_sq4 = np.mean(sq4_pat) if sq4_pat else 0
                verdict = "Good" if avg_sq4 > 2 else "Bad" if avg_sq4 < -2 else "Neutral"
                if sub_reported == 0: verdict = "Neutral"
                
                ind_subs.append({
                    "name": sub["name"], "stocks": sub_tot, "reported": sub_reported,
                    "beat": sub_beat, "miss": sub_miss, "neutral": sub_neu,
                    "q3Pat": round(np.mean(sq3_pat), 1) if sq3_pat else 0,
                    "q4Pat": round(avg_sq4, 1), "verdict": verdict
                })
                
                i_tot_stocks += sub_tot; i_reported += sub_reported
                i_beat += sub_beat; i_miss += sub_miss; i_neu += sub_neu
            
            avg_iq4 = np.mean(i_q4_pat) if i_q4_pat else 0
            ind_verdict = "Good" if avg_iq4 > 2 else "Bad" if avg_iq4 < -2 else "Neutral"
            if i_reported == 0: ind_verdict = "Neutral"
            
            sec_inds.append({
                "name": ind["name"], "totalStocks": i_tot_stocks, "reported": i_reported,
                "beat": i_beat, "miss": i_miss, "neutral": i_neu,
                "q3Pat": round(np.mean(i_q3_pat), 1) if i_q3_pat else 0,
                "q4Pat": round(avg_iq4, 1),
                "q3Rev": round(np.mean(i_q3_rev), 1) if i_q3_rev else 0,
                "q4Rev": round(np.mean(i_q4_rev), 1) if i_q4_rev else 0,
                "verdict": ind_verdict, "subIndustries": ind_subs
            })
            
            sec_tot_stocks += i_tot_stocks; sec_reported += i_reported
            sec_beat += i_beat; sec_miss += i_miss; sec_neu += i_neu

        avg_sq4 = np.mean(s_q4_pat) if s_q4_pat else 0
        sec_verdict = "Good" if avg_sq4 > 2 else "Bad" if avg_sq4 < -2 else "Neutral"
        if sec_reported == 0: sec_verdict = "Neutral"
        
        sectors_json.append({
            "name": sec["name"], "color": sec["color"], "weight": sec["weight"],
            "totalStocks": sec_tot_stocks, "reported": sec_reported,
            "beat": sec_beat, "miss": sec_miss, "neutral": sec_neu,
            "q3Pat": round(np.mean(s_q3_pat), 1) if s_q3_pat else 0,
            "q4Pat": round(avg_sq4, 1),
            "q3Rev": round(np.mean(s_q3_rev), 1) if s_q3_rev else 0,
            "q4Rev": round(np.mean(s_q4_rev), 1) if s_q4_rev else 0,
            "q3Ebitda": round(np.mean(s_q3_ebitda), 1) if s_q3_ebitda else 0,
            "q4Ebitda": round(np.mean(s_q4_ebitda), 1) if s_q4_ebitda else 0,
            "q3Npm": round(np.mean(s_q3_npm), 1) if s_q3_npm else 0,
            "q4Npm": round(np.mean(s_q4_npm), 1) if s_q4_npm else 0,
            "q3Roe": round(np.mean(s_roe), 1) if s_roe else 0,
            "q4Roe": round(np.mean(s_roe), 1) if s_roe else 0,
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
