import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def safe_float(val, default=0.0) -> float:
    try:
        f = float(val)
        if pd.isna(f) or f != f:   # NaN check
            return default
        return f
    except:
        return default

def get_market_mood() -> dict:
    signals = {}

    # Nifty 50
    try:
        nifty = yf.download(
            "^NSEI", period="30d",
            progress=False, auto_adjust=True
        )
        if isinstance(nifty.columns, pd.MultiIndex):
            nifty.columns = nifty.columns.get_level_values(0)

        close = nifty['Close'].astype(float).dropna()

        if len(close) >= 5:
            current   = safe_float(close.iloc[-1])
            prev_week = safe_float(close.iloc[-5])
            ma20_val  = safe_float(close.rolling(20).mean().iloc[-1])

            week_change = round(((current - prev_week) / prev_week) * 100, 2) \
                          if prev_week > 0 else 0.0
            above_ma    = current > ma20_val if ma20_val > 0 else True

            signals["nifty_current"]     = round(current, 1)
            signals["nifty_week_change"] = week_change
            signals["nifty_above_ma20"]  = above_ma
        else:
            signals["nifty_current"]     = 0.0
            signals["nifty_week_change"] = 0.0
            signals["nifty_above_ma20"]  = True
    except Exception as e:
        print(f"Nifty error: {e}")
        signals["nifty_current"]     = 0.0
        signals["nifty_week_change"] = 0.0
        signals["nifty_above_ma20"]  = True

    # India VIX
    try:
        vix = yf.download(
            "^INDIAVIX", period="5d",
            progress=False, auto_adjust=True
        )
        if isinstance(vix.columns, pd.MultiIndex):
            vix.columns = vix.columns.get_level_values(0)

        vix_series = vix['Close'].astype(float).dropna()
        vix_val    = safe_float(vix_series.iloc[-1], 15.0) \
                     if len(vix_series) > 0 else 15.0

        signals["india_vix"] = round(vix_val, 2)
        signals["high_fear"] = vix_val > 20
    except Exception as e:
        print(f"VIX error: {e}")
        signals["india_vix"] = 15.0
        signals["high_fear"] = False

    # Determine mood
    vix_val     = signals.get("india_vix", 15.0)
    week_change = signals.get("nifty_week_change", 0.0)
    above_ma    = signals.get("nifty_above_ma20", True)

    if vix_val < 14 and above_ma and week_change > 0:
        mood   = "BULLISH"
        advice = "Good time to invest full budget"
        color  = "green"
    elif vix_val > 22 or week_change < -3:
        mood   = "BEARISH"
        advice = "Market fearful — split investment into 2 tranches"
        color  = "red"
    elif week_change < -1 or not above_ma:
        mood   = "CAUTIOUS"
        advice = "Uncertain market — increase LIQUIDBEES allocation"
        color  = "yellow"
    else:
        mood   = "NEUTRAL"
        advice = "Stable market — invest as planned"
        color  = "blue"

    return {
        "mood":         mood,
        "color":        color,
        "advice":       advice,
        "nifty":        signals.get("nifty_current", 0.0),
        "nifty_change": signals.get("nifty_week_change", 0.0),
        "india_vix":    signals.get("india_vix", 15.0),
        "high_fear":    signals.get("high_fear", False)
    }

if __name__ == "__main__":
    mood = get_market_mood()
    print(f"Market Mood : {mood['mood']}")
    print(f"Nifty50     : {mood['nifty']} ({mood['nifty_change']}%)")
    print(f"India VIX   : {mood['india_vix']}")
    print(f"Advice      : {mood['advice']}")