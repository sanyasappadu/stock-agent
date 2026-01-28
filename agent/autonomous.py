# agent/autonomous.py
# Autonomous AI Investment Agent — hedge fund manager logic

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, math, uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# ── Helpers ───────────────────────────────────────────────────
def safe(val, default=0.0):
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except:
        return default

# ── Signal resolver ───────────────────────────────────────────
def resolve_signal(stock: dict) -> dict:
    """
    Multi-signal analysis with conflict resolution.
    Returns action, confidence, stop_loss, risk_level.
    """
    rsi        = safe(stock.get("rsi", 50))
    macd_bull  = bool(stock.get("macd_bull", False))
    above_ma   = bool(stock.get("above_ma200", False))
    momentum   = safe(stock.get("momentum", 0))
    vol_ratio  = safe(stock.get("vol_ratio", 1))
    sent_score = safe(stock.get("sent_score", 50))
    price      = safe(stock.get("price", 1))

    buy_signals  = []
    sell_signals = []

    # RSI signals
    if rsi < 35:
        buy_signals.append(("RSI oversold", 2))
    elif rsi > 72:
        sell_signals.append(("RSI overbought", 2))
    elif 38 <= rsi <= 55:
        buy_signals.append(("RSI in ideal range", 1))

    # MACD
    if macd_bull:
        buy_signals.append(("MACD bullish", 2))
    else:
        sell_signals.append(("MACD bearish", 1))

    # Trend
    if above_ma:
        buy_signals.append(("Above 200MA uptrend", 2))
    else:
        sell_signals.append(("Below 200MA downtrend", 2))

    # Momentum
    if momentum > 5:
        buy_signals.append(("Strong momentum", 1))
    elif momentum < -8:
        sell_signals.append(("Negative momentum", 2))

    # Volume
    if vol_ratio > 1.8 and macd_bull:
        buy_signals.append(("Volume spike + bull", 1))

    # Sentiment
    if sent_score > 65:
        buy_signals.append(("Positive sentiment", 1))
    elif sent_score < 35:
        sell_signals.append(("Negative sentiment", 1))

    buy_weight  = sum(w for _, w in buy_signals)
    sell_weight = sum(w for _, w in sell_signals)
    total       = max(buy_weight + sell_weight, 1)

    if buy_weight > sell_weight + 2:
        action     = "BUY"
        confidence = min(int((buy_weight / total) * 100) + 5, 92)
        color      = "green"
    elif sell_weight > buy_weight + 2:
        action     = "SELL"
        confidence = min(int((sell_weight / total) * 100) + 5, 90)
        color      = "red"
    else:
        action     = "HOLD"
        confidence = 40 + int((abs(buy_weight - sell_weight) / total) * 20)
        color      = "amber"

    # Stop loss — tighter for high volatility
    sl_pct     = 7 if safe(stock.get("vol_ratio", 1)) > 1.5 else 5
    stop_loss  = round(price * (1 - sl_pct / 100), 2)

    # Risk rating
    if rsi > 68 or momentum < -5 or not above_ma:
        risk = "HIGH"
    elif rsi < 42 and above_ma and macd_bull:
        risk = "LOW"
    else:
        risk = "MEDIUM"

    reason_parts = [s for s, _ in buy_signals[:3]] if action == "BUY" \
              else [s for s, _ in sell_signals[:3]] if action == "SELL" \
              else [s for s, _ in (buy_signals + sell_signals)[:3]]

    return {
        "action":     action,
        "confidence": confidence,
        "color":      color,
        "stop_loss":  stop_loss,
        "sl_pct":     sl_pct,
        "risk":       risk,
        "buy_score":  buy_weight,
        "sell_score": sell_weight,
        "reasons":    reason_parts
    }

# ── Dynamic allocator ─────────────────────────────────────────
def dynamic_allocate(budget: float,
                     scored: list,
                     risk_level: str = "moderate",
                     market_mood: str = "NEUTRAL") -> dict:
    """
    Risk-adjusted portfolio allocation.
    Always tries to allocate to at least 2-3 stocks.
    """
    LIQUID_ETF  = {"symbol": "LIQUIDBEES", "price": 1000.0}

    # Cash reserve based on market + risk
    if market_mood == "BEARISH":
        reserve_pct = 0.20
    elif market_mood == "CAUTIOUS":
        reserve_pct = 0.15
    elif risk_level == "aggressive":
        reserve_pct = 0.05
    elif risk_level == "conservative":
        reserve_pct = 0.20
    else:
        reserve_pct = 0.10

    reserve    = round(budget * reserve_pct, 2)
    investable = round(budget - reserve, 2)

    # Filter — only valid prices, take top 6 by score
    valid = [
        s for s in scored
        if safe(s.get("price")) > 10
        and safe(s.get("final_score")) > 0
    ]
    picks = sorted(valid, key=lambda x: x["final_score"], reverse=True)[:6]

    if not picks:
        return {
            "budget": budget, "reserve": reserve,
            "investable": investable, "total_spent": 0,
            "leftover_cash": investable, "holdings": [],
            "cash_reserve_pct": reserve_pct,
            "market_mood": market_mood
        }

    # Confidence-weighted allocation
    signals     = {p["symbol"]: resolve_signal(p) for p in picks}
    conf_scores = {
        p["symbol"]: signals[p["symbol"]]["confidence"] * safe(p["final_score"])
        for p in picks
    }
    total_conf  = max(sum(conf_scores.values()), 1)

    # Max position: aggressive=50%, moderate=35%, conservative=25%
    max_pct = {"aggressive": 0.50, "moderate": 0.35, "conservative": 0.25}
    max_pos = budget * max_pct.get(risk_level, 0.35)

    allocation  = []
    total_spent = 0.0

    for pick in picks:
        sym    = pick["symbol"]
        price  = safe(pick["price"])
        sig    = signals[sym]

        # Skip SELL signals in allocation
        if sig["action"] == "SELL":
            continue

        weight     = conf_scores[sym] / total_conf
        raw_amount = investable * weight
        capped     = min(raw_amount, max_pos)
        shares     = int(capped // price)

        if shares >= 1:
            spent = round(shares * price, 2)
            total_spent += spent
            allocation.append({
                "symbol":      sym,
                "shares":      shares,
                "price":       round(price, 2),
                "spent":       spent,
                "pct":         round(spent / budget * 100, 1),
                "score":       round(safe(pick["final_score"]), 1),
                "action":      sig["action"],
                "confidence":  sig["confidence"],
                "stop_loss":   sig["stop_loss"],
                "risk":        sig["risk"],
                "reason":      " | ".join(sig["reasons"])
            })

    leftover  = round(investable - total_spent, 2)

    # Park leftover
    etf_units = int(leftover // LIQUID_ETF["price"])
    if etf_units >= 1:
        etf_spent = etf_units * LIQUID_ETF["price"]
        allocation.append({
            "symbol":     "LIQUIDBEES",
            "shares":     etf_units,
            "price":      LIQUID_ETF["price"],
            "spent":      etf_spent,
            "pct":        round(etf_spent / budget * 100, 1),
            "score":      0,
            "action":     "HOLD",
            "confidence": 99,
            "stop_loss":  LIQUID_ETF["price"] * 0.99,
            "risk":       "LOW",
            "reason":     "Idle cash earning ~6% in liquid ETF"
        })
        leftover = round(leftover - etf_spent, 2)

    return {
        "budget":           budget,
        "reserve":          reserve,
        "investable":       investable,
        "total_spent":      round(total_spent, 2),
        "leftover_cash":    round(leftover, 2),
        "holdings":         allocation,
        "cash_reserve_pct": reserve_pct,
        "market_mood":      market_mood,
        "positions_taken":  len([h for h in allocation
                                 if h["symbol"] != "LIQUIDBEES"])
    }

# ── Scenario simulator ────────────────────────────────────────
def simulate_scenarios(holdings: list) -> dict:
    """
    Bull / Base / Bear scenario for the portfolio.
    """
    scenarios = {"bull": 0, "base": 0, "bear": 0}
    total_invested = sum(h["spent"] for h in holdings)

    if total_invested == 0:
        return scenarios

    for h in holdings:
        if h["symbol"] == "LIQUIDBEES":
            scenarios["bull"] += h["spent"] * 1.005
            scenarios["base"] += h["spent"] * 1.005
            scenarios["bear"] += h["spent"] * 1.005
            continue

        risk = h.get("risk", "MEDIUM")
        if risk == "LOW":
            bull, base, bear = 1.15, 1.08, 0.96
        elif risk == "HIGH":
            bull, base, bear = 1.28, 1.05, 0.82
        else:
            bull, base, bear = 1.20, 1.06, 0.90

        scenarios["bull"] += h["spent"] * bull
        scenarios["base"] += h["spent"] * base
        scenarios["bear"] += h["spent"] * bear

    return {
        "invested":      round(total_invested, 2),
        "bull_value":    round(scenarios["bull"], 2),
        "base_value":    round(scenarios["base"], 2),
        "bear_value":    round(scenarios["bear"], 2),
        "bull_return":   round(((scenarios["bull"] - total_invested) / total_invested) * 100, 1),
        "base_return":   round(((scenarios["base"] - total_invested) / total_invested) * 100, 1),
        "bear_return":   round(((scenarios["bear"] - total_invested) / total_invested) * 100, 1),
    }

# ── Performance tracker ───────────────────────────────────────
def track_performance(trade_history: list) -> dict:
    """
    Analyze past trades to measure agent accuracy.
    """
    if not trade_history:
        return {
            "total_trades":   0,
            "accuracy":       0,
            "avg_return":     0,
            "best_trade":     None,
            "worst_trade":    None,
            "improvement_tip": "Make your first trade to start tracking!"
        }

    total   = len(trade_history)
    budgets = [t.get("budget", 0) for t in trade_history]
    avg_b   = round(sum(budgets) / total, 2) if total > 0 else 0

    # Count unique stocks used
    all_syms = []
    for t in trade_history:
        holdings = t.get("allocation", {}).get("holdings", [])
        all_syms.extend([h["symbol"] for h in holdings
                         if h["symbol"] != "LIQUIDBEES"])

    sym_freq = {}
    for s in all_syms:
        sym_freq[s] = sym_freq.get(s, 0) + 1

    most_traded = max(sym_freq, key=sym_freq.get) if sym_freq else "N/A"

    liq_heavy = sum(
        1 for t in trade_history
        if any(h["symbol"] == "LIQUIDBEES" and h.get("pct", 0) > 60
               for h in t.get("allocation", {}).get("holdings", []))
    )
    liq_pct = round((liq_heavy / total) * 100) if total > 0 else 0

    tips = []
    if liq_pct > 50:
        tips.append("Agent sent >60% to LIQUIDBEES in half your trades — "
                    "market has been bearish. Consider waiting for VIX < 17.")
    if len(sym_freq) < 3:
        tips.append("Portfolio lacks diversity — try including "
                    "different sectors (IT, Banking, FMCG).")
    if total < 5:
        tips.append("More trades = better learning. Run analysis "
                    "daily for 2 weeks to build performance data.")

    return {
        "total_trades":    total,
        "avg_budget":      avg_b,
        "most_traded":     most_traded,
        "liquid_heavy_pct": liq_pct,
        "unique_stocks":   len(sym_freq),
        "improvement_tips": tips[:2],
        "stock_frequency": sym_freq
    }

# ── Rebalance checker ─────────────────────────────────────────
def should_rebalance(last_trade_date: str,
                     current_mood: str,
                     last_mood: str = "NEUTRAL") -> dict:
    """
    Determines if portfolio needs rebalancing.
    """
    triggers = []
    should   = False

    try:
        last = datetime.fromisoformat(last_trade_date)
        days_since = (datetime.utcnow() - last).days

        if days_since >= 30:
            triggers.append(f"Monthly rebalance due ({days_since} days)")
            should = True

        if current_mood == "BEARISH" and last_mood != "BEARISH":
            triggers.append("Market turned bearish — reduce equity exposure")
            should = True

        if current_mood == "BULLISH" and last_mood == "BEARISH":
            triggers.append("Market recovery — increase equity allocation")
            should = True

    except:
        triggers.append("First trade — initial allocation")
        should = True

    return {
        "should_rebalance": should,
        "triggers":         triggers,
        "recommendation":   triggers[0] if triggers else "Portfolio balanced"
    }

if __name__ == "__main__":
    # Quick test
    test_stocks = [
        {"symbol": "TITAN",    "price": 4439, "final_score": 65,
         "rsi": 62, "macd_bull": True,  "above_ma200": True,
         "momentum": 5.2,  "vol_ratio": 1.8, "sent_score": 72},
        {"symbol": "NESTLEIND","price": 1228, "final_score": 61,
         "rsi": 58, "macd_bull": True,  "above_ma200": True,
         "momentum": 3.1,  "vol_ratio": 1.2, "sent_score": 65},
        {"symbol": "ICICIBANK","price": 1281, "final_score": 52,
         "rsi": 48, "macd_bull": True,  "above_ma200": False,
         "momentum": -1.2, "vol_ratio": 0.9, "sent_score": 55},
        {"symbol": "WIPRO",    "price": 202,  "final_score": 45,
         "rsi": 63, "macd_bull": False, "above_ma200": False,
         "momentum": 0.5,  "vol_ratio": 1.1, "sent_score": 48},
    ]

    plan = dynamic_allocate(5000, test_stocks,
                            risk_level="moderate",
                            market_mood="NEUTRAL")

    print("\n=== AUTONOMOUS ALLOCATION ===")
    for h in plan["holdings"]:
        print(f"  {h['symbol']:12} {h['shares']:>3} shares "
              f"× ₹{h['price']:>8} = ₹{h['spent']:>8} "
              f"| {h['action']:4} {h['confidence']}% "
              f"| SL ₹{h['stop_loss']} | {h['risk']}")
    print(f"\n  Total invested : ₹{plan['total_spent']}")
    print(f"  Reserve        : ₹{plan['reserve']} ({plan['cash_reserve_pct']*100:.0f}%)")
    print(f"  Positions      : {plan['positions_taken']} stocks")

    sc = simulate_scenarios(plan["holdings"])
    print(f"\n=== SCENARIO ANALYSIS ===")
    print(f"  Bull case : ₹{sc['bull_value']} (+{sc['bull_return']}%)")
    print(f"  Base case : ₹{sc['base_value']} (+{sc['base_return']}%)")
    print(f"  Bear case : ₹{sc['bear_value']} ({sc['bear_return']}%)")