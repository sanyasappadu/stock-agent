import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

WATCHLIST = {
    "RELIANCE":   "Reliance Industries",
    "TCS":        "Tata Consultancy Services",
    "INFY":       "Infosys",
    "HDFCBANK":   "HDFC Bank",
    "WIPRO":      "Wipro",
    "ICICIBANK":  "ICICI Bank",
    "BAJFINANCE": "Bajaj Finance",
    "TITAN":      "Titan Company",
    "MARUTI":     "Maruti Suzuki",
    "ADANIENT":   "Adani Enterprises",
    "SUNPHARMA":  "Sun Pharmaceutical",
    "LTIM":       "LTIMindtree",
    "AXISBANK":   "Axis Bank",
    "KOTAKBANK":  "Kotak Mahindra Bank",
    "NESTLEIND":  "Nestle India",
    "HINDUNILVR": "Hindustan Unilever",
    "ITC":        "ITC Limited",
    "POWERGRID":  "Power Grid Corporation",
    "NTPC":       "NTPC Limited",
    "ONGC":       "Oil and Natural Gas"
}

def get_stock_price(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist   = ticker.history(period="5d")

        if hist.empty or len(hist) < 2:
            return None

        # Flatten MultiIndex if present
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        close_series = hist['Close'].dropna()
        if len(close_series) < 2:
            return None

        price  = float(close_series.iloc[-1])
        prev   = float(close_series.iloc[-2])

        # Skip if NaN
        if pd.isna(price) or pd.isna(prev) or price <= 0:
            return None

        change = round(((price - prev) / prev) * 100, 2)

        return {
            "symbol":     symbol,
            "price":      round(price, 2),
            "prev_close": round(prev, 2),
            "change_pct": change
        }
    except Exception as e:
        print(f"  Error fetching {symbol}: {e}")
        return None

def get_all_prices() -> list:
    results = []
    for symbol in WATCHLIST:
        data = get_stock_price(symbol)
        if data and data["price"] > 0:
            arrow = "▲" if data['change_pct'] >= 0 else "▼"
            print(f"  {symbol:12} ₹{data['price']:>10.2f}  "
                  f"{arrow} {abs(data['change_pct'])}%")
            results.append(data)
        else:
            print(f"  {symbol:12} skipped (no data)")
    return results

if __name__ == "__main__":
    print("Fetching live NSE prices...\n")
    prices = get_all_prices()
    print(f"\nFetched {len(prices)} stocks")