import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
import pandas as pd
import numpy as np
import math
from dotenv import load_dotenv
load_dotenv()

def safe_float(val, default=0.0) -> float:
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except:
        return default

def get_technical_score(symbol: str) -> dict:
    try:
        df = yf.download(
            f"{symbol}.NS",
            period      = "6mo",
            interval    = "1d",
            progress    = False,
            auto_adjust = True
        )

        if df.empty or len(df) < 30:
            print(f"  Not enough data for {symbol}")
            return None

        # Flatten MultiIndex — THIS IS THE KEY FIX
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        # Force float and drop NaN rows
        df = df[['Close', 'Volume']].copy()
        df['Close']  = pd.to_numeric(df['Close'],  errors='coerce')
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        df = df.dropna()

        if len(df) < 20:
            return None

        close  = df['Close']
        volume = df['Volume']

        # Get current price safely
        current_price = safe_float(close.iloc[-1])
        if current_price <= 0:
            return None

        # RSI (14-day)
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi_series = 100 - (100 / (1 + gain / loss))
        rsi   = safe_float(rsi_series.iloc[-1], 50.0)

        # MACD
        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal    = macd_line.ewm(span=9, adjust=False).mean()
        macd_val  = safe_float(macd_line.iloc[-1])
        sig_val   = safe_float(signal.iloc[-1])
        macd_bull = macd_val > sig_val

        # 200-day MA
        ma200       = close.rolling(min(200, len(close))).mean()
        ma200_val   = safe_float(ma200.iloc[-1], current_price)
        above_ma200 = current_price > ma200_val

        # Volume spike
        vol_ma    = safe_float(volume.rolling(20).mean().iloc[-1], 1)
        vol_today = safe_float(volume.iloc[-1])
        vol_ratio = round(vol_today / vol_ma, 2) if vol_ma > 0 else 1.0

        # 52-week range
        high52 = safe_float(close.rolling(min(252,len(close))).max().iloc[-1], current_price)
        low52  = safe_float(close.rolling(min(252,len(close))).min().iloc[-1], current_price)
        pct_from_high = round(((current_price - high52) / high52) * 100, 1) if high52 > 0 else 0

        # Momentum (20-day return)
        price_20d = safe_float(close.iloc[-20] if len(close) >= 20 else close.iloc[0])
        momentum  = round(((current_price - price_20d) / price_20d) * 100, 2) if price_20d > 0 else 0

        # Composite TA score (0-100)
        score = 0
        if 40 <= rsi <= 60:
            score += 30
        elif rsi < 40:
            score += 22   # oversold = buy opportunity
        elif rsi > 70:
            score += 5    # overbought = risky

        score += 25 if macd_bull   else 0
        score += 25 if above_ma200 else 0

        if vol_ratio >= 1.5:
            score += 20
        elif vol_ratio >= 1.0:
            score += 10

        return {
            "symbol":        symbol,
            "price":         round(current_price, 2),
            "rsi":           round(rsi, 1),
            "macd_bull":     bool(macd_bull),
            "above_ma200":   bool(above_ma200),
            "vol_ratio":     vol_ratio,
            "pct_from_high": pct_from_high,
            "momentum":      momentum,
            "ta_score":      score
        }

    except Exception as e:
        print(f"  Error in technical analysis for {symbol}: {e}")
        return None

if __name__ == "__main__":
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "WIPRO",
               "ITC", "TITAN", "AXISBANK"]
    print(f"\n{'SYMBOL':12} {'PRICE':>10} {'RSI':>6} "
          f"{'MACD':>6} {'MA200':>6} {'SCORE':>6}")
    print("-" * 55)
    for sym in symbols:
        r = get_technical_score(sym)
        if r:
            print(f"{r['symbol']:12} "
                  f"₹{r['price']:>9.2f} "
                  f"{r['rsi']:>6.1f} "
                  f"{'YES' if r['macd_bull'] else 'NO':>6} "
                  f"{'YES' if r['above_ma200'] else 'NO':>6} "
                  f"{r['ta_score']:>6}/100")
        else:
            print(f"{sym:12} -- skipped")