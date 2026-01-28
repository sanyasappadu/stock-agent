import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
import pandas as pd
import math
from dotenv import load_dotenv
load_dotenv()

def safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if math.isnan(f) or math.isinf(f) else f
    except:
        return default

def get_stock_advice(symbol: str) -> dict:
    """
    Returns BUY / HOLD / SELL recommendation
    with reason for a given NSE stock.
    """
    try:
        df = yf.download(
            f"{symbol}.NS", period="6mo",
            interval="1d", progress=False,
            auto_adjust=True
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if df.empty or len(df) < 30:
            return {"symbol": symbol, "action": "HOLD",
                    "reason": "Insufficient data", "score": 50}

        close  = df['Close'].astype(float).dropna()
        volume = df['Volume'].astype(float).dropna()

        current = safe_float(close.iloc[-1])

        # RSI
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rsi   = safe_float(
            (100 - (100 / (1 + gain / loss))).iloc[-1], 50)

        # MACD
        ema12    = close.ewm(span=12, adjust=False).mean()
        ema26    = close.ewm(span=26, adjust=False).mean()
        macd     = safe_float((ema12 - ema26).iloc[-1])
        signal   = safe_float(
            (ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1])
        macd_bull = macd > signal

        # Price vs 52-week high/low
        high52 = safe_float(close.rolling(252).max().iloc[-1], current)
        low52  = safe_float(close.rolling(252).min().iloc[-1], current)
        pct_from_high = round(((current - high52) / high52) * 100, 1) \
                        if high52 > 0 else 0
        pct_from_low  = round(((current - low52)  / low52)  * 100, 1) \
                        if low52  > 0 else 0

        # 200-day MA
        ma200      = safe_float(close.rolling(200).mean().iloc[-1], current)
        above_ma200 = current > ma200

        # Volume
        vol_avg    = safe_float(volume.rolling(20).mean().iloc[-1], 1)
        vol_today  = safe_float(volume.iloc[-1])
        vol_spike  = (vol_today / vol_avg) > 1.5 if vol_avg > 0 else False

        # Decision logic
        buy_signals  = []
        sell_signals = []
        hold_signals = []

        if rsi < 35:
            buy_signals.append(f"RSI oversold at {rsi:.1f}")
        elif rsi > 70:
            sell_signals.append(f"RSI overbought at {rsi:.1f}")
        else:
            hold_signals.append(f"RSI neutral at {rsi:.1f}")

        if macd_bull:
            buy_signals.append("MACD bullish crossover")
        else:
            sell_signals.append("MACD bearish signal")

        if above_ma200:
            buy_signals.append("Price above 200-day MA (uptrend)")
        else:
            sell_signals.append("Price below 200-day MA (downtrend)")

        if pct_from_high < -25:
            buy_signals.append(
                f"Trading {abs(pct_from_high)}% below 52-week high")
        elif pct_from_high > -5:
            sell_signals.append("Near 52-week high — consider booking profit")

        if vol_spike and macd_bull:
            buy_signals.append("High volume with bullish momentum")

        # Final decision
        buy_count  = len(buy_signals)
        sell_count = len(sell_signals)

        if buy_count >= 3:
            action = "BUY"
            color  = "green"
            reason = " | ".join(buy_signals[:3])
        elif sell_count >= 3:
            action = "SELL"
            color  = "red"
            reason = " | ".join(sell_signals[:3])
        else:
            action = "HOLD"
            color  = "yellow"
            reason = "Mixed signals — " + " | ".join(
                (buy_signals + hold_signals)[:2])

        confidence = min(
            round((max(buy_count, sell_count) / 5) * 100), 95)

        return {
            "symbol":        symbol,
            "action":        action,
            "color":         color,
            "reason":        reason,
            "confidence":    confidence,
            "current_price": round(current, 2),
            "rsi":           round(rsi, 1),
            "macd_bull":     macd_bull,
            "above_ma200":   above_ma200,
            "pct_from_high": pct_from_high,
            "pct_from_low":  pct_from_low,
        }

    except Exception as e:
        return {
            "symbol":     symbol,
            "action":     "HOLD",
            "reason":     f"Analysis error: {str(e)}",
            "confidence": 0,
            "color":      "yellow"
        }

if __name__ == "__main__":
    symbols = ["RELIANCE", "TCS", "INFY", "WIPRO", "HDFCBANK"]
    print(f"{'SYMBOL':12} {'ACTION':6} {'CONF':6} REASON")
    print("-" * 70)
    for sym in symbols:
        r = get_stock_advice(sym)
        print(f"{r['symbol']:12} {r['action']:6} "
              f"{r.get('confidence',0):>4}%  {r['reason'][:50]}")