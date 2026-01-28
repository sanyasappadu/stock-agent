import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

import os, json, math
from openai          import OpenAI
from dotenv          import load_dotenv
from agent.tools.technical import get_technical_score
from agent.tools.sentiment import get_sentiment_score
from agent.allocator       import allocate

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

WATCHLIST = {
    "RELIANCE":   "Reliance Industries",
    "TCS":        "Tata Consultancy Services",
    "INFY":       "Infosys",
    "HDFCBANK":   "HDFC Bank",
    "WIPRO":      "Wipro",
    "ICICIBANK":  "ICICI Bank",
    "BAJFINANCE": "Bajaj Finance",
    "TITAN":      "Titan Company",
    "ITC":        "ITC Limited",
    "AXISBANK":   "Axis Bank",
    "SUNPHARMA":  "Sun Pharmaceutical",
    "KOTAKBANK":  "Kotak Mahindra Bank",
    "NESTLEIND":  "Nestle India",
    "HINDUNILVR": "Hindustan Unilever",
    "NTPC":       "NTPC Limited"
}

def safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except:
        return default

def analyze_all() -> list:
    results = []
    for symbol, name in WATCHLIST.items():
        print(f"  Analyzing {symbol}...")
        ta   = get_technical_score(symbol)
        sent = get_sentiment_score(symbol, name)

        if not ta:
            continue

        price = safe_float(ta.get("price"))
        if price <= 0:
            print(f"  Skipping {symbol} — invalid price")
            continue

        ta_score   = safe_float(ta.get("ta_score", 0))
        sent_score = safe_float(sent.get("score", 50))
        final      = round((ta_score * 0.60) + (sent_score * 0.40), 1)

        results.append({
            "symbol":       symbol,
            "company":      name,
            "price":        price,
            "rsi":          safe_float(ta.get("rsi", 50)),
            "macd_bull":    bool(ta.get("macd_bull", False)),
            "above_ma200":  bool(ta.get("above_ma200", False)),
            "vol_ratio":    safe_float(ta.get("vol_ratio", 1)),
            "momentum":     safe_float(ta.get("momentum", 0)),
            "pct_from_high":safe_float(ta.get("pct_from_high", 0)),
            "ta_score":     ta_score,
            "sentiment":    sent.get("sentiment", "neutral"),
            "sent_score":   sent_score,
            "sent_reason":  sent.get("reason", ""),
            "final_score":  final,
            "reason": (
                f"TA {ta_score}/100 | RSI {ta.get('rsi',50):.1f} | "
                f"MACD {'bullish' if ta.get('macd_bull') else 'bearish'} | "
                f"News: {sent.get('sentiment','neutral')}"
            )
        })

    return sorted(results, key=lambda x: x["final_score"], reverse=True)

def generate_advanced_explanation(
        budget: float, risk: str,
        scored: list, plan: dict,
        mood: dict = None) -> str:

    top5 = scored[:5]

    # Market regime detection
    avg_rsi      = sum(s["rsi"] for s in top5) / len(top5) if top5 else 50
    bull_count   = sum(1 for s in top5 if s["macd_bull"])
    above_ma_cnt = sum(1 for s in top5 if s["above_ma200"])

    if bull_count >= 3 and above_ma_cnt >= 3:
        regime = "BULL"
    elif bull_count <= 1 and above_ma_cnt <= 1:
        regime = "BEAR"
    else:
        regime = "SIDEWAYS"

    vix_val = mood.get("india_vix", 15) if mood else 15

    data_str = json.dumps({
        "budget":        budget,
        "risk_level":    risk,
        "market_regime": regime,
        "india_vix":     vix_val,
        "avg_rsi":       round(avg_rsi, 1),
        "top_picks": [{
            "symbol":      s["symbol"],
            "company":     s["company"],
            "price":       s["price"],
            "score":       s["final_score"],
            "rsi":         s["rsi"],
            "macd_bull":   s["macd_bull"],
            "above_ma200": s["above_ma200"],
            "momentum":    s["momentum"],
            "sentiment":   s["sentiment"],
            "sent_reason": s["sent_reason"]
        } for s in top5],
        "allocation": plan.get("holdings", [])
    }, indent=2)

    system_prompt = """You are an advanced AI Investment Agent for Indian markets.

Your objectives:
1. Maximize risk-adjusted returns (Sharpe Ratio)
2. Minimize downside risk
3. Adapt dynamically to market conditions

Given the market data and allocation plan, provide a structured report:

SECTION 1 — MARKET REGIME
- State: Bull / Bear / Sideways
- Key signals (VIX, RSI average, MACD trend)
- What this means for the investor

SECTION 2 — TOP STOCK PICKS (for each allocated stock)
- Action: BUY / HOLD
- Why chosen (2-3 specific technical/sentiment reasons)
- Stop-loss level (suggest % below current price)
- Confidence % (be realistic, vary between stocks)
- Risk: LOW / MEDIUM / HIGH

SECTION 3 — PORTFOLIO SUMMARY
- Expected return range (realistic, e.g. 8-12% over 6 months)
- Overall risk level
- Sector distribution (IT / Banking / Consumer / Energy)
- Cash reserve and why

SECTION 4 — BEHAVIORAL ALERT
- One personalized tip based on market regime
- What to watch next week

Rules:
- Use ₹ for amounts
- Be specific, not generic
- Never hallucinate data — use only provided signals
- Keep total under 350 words
- Use plain language, avoid jargon"""

    resp = client.chat.completions.create(
        model       = "gpt-4o-mini",
        temperature = 0.4,
        messages    = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": data_str}
        ]
    )
    return resp.choices[0].message.content

def run_agent(budget: float,
              risk_level: str = "moderate",
              execute:    bool = False) -> dict:
    print("\n=== Autonomous Stock Agent ===\n")

    print("Step 1: Analyzing stocks...")
    scored = analyze_all()

    if not scored:
        return {
            "allocation":   {"budget": budget, "holdings": [],
                             "total_spent": 0, "reserve": budget*0.1,
                             "investable": budget*0.9,
                             "leftover_cash": budget*0.9,
                             "positions_taken": 0},
            "top_stocks":   [],
            "explanation":  "No valid data. Market may be closed.",
            "order_results":[], "mode": "paper",
            "scenarios":    {}, "performance": {}
        }

    # Get market mood for allocation decisions
    mood_data = None
    mood_str  = "NEUTRAL"
    try:
        from agent.tools.market_mood import get_market_mood
        mood_data = get_market_mood()
        mood_str  = mood_data.get("mood", "NEUTRAL")
    except:
        pass

    print(f"\n  Market: {mood_str}")
    print(f"\nStep 2: Autonomous allocation...")

    from agent.autonomous import dynamic_allocate, simulate_scenarios, track_performance
    plan = dynamic_allocate(budget, scored, risk_level, mood_str)

    print(f"  {plan['positions_taken']} positions taken")
    for h in plan["holdings"]:
        print(f"  {h['symbol']:12} {h['shares']} × ₹{h['price']} "
              f"= ₹{h['spent']} | {h.get('action','BUY')} "
              f"{h.get('confidence',50)}%")

    print("\nStep 3: Scenario analysis...")
    scenarios = simulate_scenarios(plan["holdings"])
    print(f"  Bull: +{scenarios.get('bull_return',0)}% | "
          f"Base: +{scenarios.get('base_return',0)}% | "
          f"Bear: {scenarios.get('bear_return',0)}%")

    print("\nStep 4: Generating AI report...")
    explanation = generate_advanced_explanation(
        budget, risk_level, scored, plan, mood_data)

    # Execute
    order_results = []
    paper_mode    = os.getenv("PAPER_MODE", "true") == "true"
    if execute:
        from agent.tools.broker import place_all_orders
        order_results = place_all_orders(plan)

    # Performance tracking (from DB if available)
    performance = {}
    try:
        from backend.database import get_trade_history
        history     = get_trade_history("demo_user")
        performance = track_performance(history)
    except:
        pass

    print("\n=== Done ===\n")

    return {
        "allocation":   plan,
        "top_stocks":   scored[:6],
        "explanation":  explanation,
        "order_results":order_results,
        "mode":         "paper" if paper_mode else "live",
        "scenarios":    scenarios,
        "performance":  performance,
        "market_mood":  mood_str
    }

if __name__ == "__main__":
    result = run_agent(budget=5000, risk_level="moderate")
    print("\nAI Report:")
    print(result["explanation"])
    print("\nAllocation:")
    for h in result["allocation"]["holdings"]:
        print(f"  {h['symbol']}: {h['shares']} shares = ₹{h['spent']}")