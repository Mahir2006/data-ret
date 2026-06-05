import os
import json
import pandas as pd
import yfinance as yf

def generate_breadth_data():
    print("Starting market breadth calculation...")
    
    # 1. Define your universe of tickers (Nifty 500 subset or full list)
    # For demonstration, a placeholder list is shown. Replace this with your actual list of tickers.
    tickers = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "BHARTIARTL.NS",
        "INFY.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS", "SBI-N.NS"
        # ... Add your full list of Nifty 500 tickers here ...
    ]
    
    # Clean tickers list
    tickers = [t.strip() for t in tickers if t.strip()]
    if not tickers:
        print("Error: Ticker list is empty.")
        return

    # 2. Download historical data (6 months to ensure enough data for 200 EMA)
    print(def_download_msg := f"Downloading data for {len(tickers)} tickers plus benchmark...")
    all_tickers = tickers + ["^NSEI"]
    
    try:
        data = yf.download(all_tickers, period="6m", interval="1d", progress=False)
    except Exception as e:
        print(f"Error downloading data from yfinance: {e}")
        return

    closes = data['Adj Close'] if 'Adj Close' in data else data['Close']
    
    # 3. Process individual stock metrics for breadth
    advancers = 0
    decliners = 0
    above_sma50 = 0
    above_sma200 = 0
    total_tracked = 0
    
    for ticker in tickers:
        if ticker not in closes.columns:
            continue
            
        series = closes[ticker].dropna()
        if len(series) < 2:
            continue
            
        total_tracked += 1
        current_price = series.iloc[-1]
        previous_price = series.iloc[-2]
        
        # Advance / Decline status (compared to previous trading day)
        if current_price > previous_price:
            advancers += 1
        else:
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

    # 4. Scale breadth metrics up to represent a full 500-stock universe
    multiplier = 500 / total_tracked
    scaled_advancers = round(advancers * multiplier)
    scaled_decliners = round(decliners * multiplier)
    
    pct_above_sma50 = round((above_sma50 / total_tracked) * 100, 2)
    pct_above_sma200 = round((above_sma200 / total_tracked) * 100, 2)

    # 5. Build the summary dictionary
    overall = {
        "advancers": scaled_advancers,
        "decliners": scaled_decliners,
        "pctAboveSMA50": pct_above_sma50,
        "pctAboveSMA200": pct_above_sma200,
    }

    # 6. Benchmark Performance Calculations using CALENDAR DATES (Matches Yahoo Finance)
    nifty = closes.get('^NSEI')
    if nifty is not None and not nifty.isna().all():
        nifty = nifty.dropna()
        n_curr = nifty.iloc[-1]        # Today's closing price
        current_date = nifty.index[-1] # Today's final timestamp
        
        # Look back by exact calendar intervals
        target_1w = current_date - pd.Timedelta(days=7)
        target_1m = current_date - pd.DateOffset(months=1)
        
        # .asof() handles weekends/holidays seamlessly by grabbing the last available session
        n_1w = nifty.asof(target_1w)
        n_1m = nifty.asof(target_1m)
        
        # Calculate matching percentage changes
        overall["nifty500Change1W"] = round(((n_curr - n_1w) / n_1w) * 100, 2)
        overall["nifty500Change1M"] = round(((n_curr - n_1m) / n_1m) * 100, 2)
        
        # Benchmark Trend Indicators (EMA)
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

    # 7. Export data to JSON file for your frontend dashboard
    output_filename = "breadth_data.json"
    try:
        with open(output_filename, "w") as f:
            json.dump(overall, f, indent=4)
        print(f"Success! Broad market data saved to {output_filename}")
        print(json.dumps(overall, indent=2))
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    generate_breadth_data()
