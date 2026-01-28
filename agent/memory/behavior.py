import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import Session, TradeLog
from sqlalchemy import func

def get_user_behavior_profile(user_id: str) -> dict:
    session = Session()
    try:
        trades = session.query(TradeLog)\
                        .filter_by(user_id=user_id)\
                        .order_by(TradeLog.created_at.desc())\
                        .limit(10).all()

        if not trades:
            return {"profile": "new_user", "insights": []}

        budgets    = [t.budget for t in trades]
        risk_levels = [t.risk_level for t in trades]
        avg_budget  = sum(budgets) / len(budgets)

        # Count how often user changed risk level
        risk_changes = len(set(risk_levels))

        # Most frequent symbols traded
        all_symbols = []
        for t in trades:
            holdings = t.allocation.get("holdings", [])
            all_symbols.extend([h["symbol"] for h in holdings])

        symbol_freq = {}
        for s in all_symbols:
            symbol_freq[s] = symbol_freq.get(s, 0) + 1
        fav_stocks = sorted(symbol_freq,
                            key=symbol_freq.get,
                            reverse=True)[:3]

        insights = []
        if avg_budget < 3000:
            insights.append(
                "You tend to invest small amounts — "
                "consider increasing SIP for better compounding")
        if risk_changes > 3:
            insights.append(
                "You frequently change risk level — "
                "this may indicate emotional decision making")
        if "LIQUIDBEES" in fav_stocks[:1]:
            insights.append(
                "Most of your money is going to LIQUIDBEES — "
                "market conditions have been unfavorable, "
                "consider waiting for a dip")

        return {
            "total_trades":  len(trades),
            "avg_budget":    round(avg_budget, 2),
            "fav_stocks":    fav_stocks,
            "risk_pattern":  max(set(risk_levels),
                                 key=risk_levels.count),
            "insights":      insights
        }
    finally:
        session.close()