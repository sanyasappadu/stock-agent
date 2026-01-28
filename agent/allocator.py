import math

LIQUID_ETF = {"symbol": "LIQUIDBEES", "price": 1000.0}

def is_valid(val) -> bool:
    try:
        f = float(val)
        return not math.isnan(f) and not math.isinf(f) and f > 0
    except:
        return False

def allocate(budget: float, scored_stocks: list) -> dict:
    RESERVE_PCT   = 0.10
    MAX_STOCK_PCT = 0.40
    MAX_STOCKS    = 5

    reserve    = round(budget * RESERVE_PCT, 2)
    investable = round(budget - reserve, 2)

    # Filter out any stocks with invalid price or score
    valid_picks = [
        p for p in scored_stocks
        if is_valid(p.get("price")) and is_valid(p.get("final_score"))
    ]

    picks = sorted(
        valid_picks,
        key=lambda x: x["final_score"],
        reverse=True
    )[:MAX_STOCKS]

    if not picks:
        return {
            "budget":        budget,
            "reserve":       reserve,
            "investable":    investable,
            "total_spent":   0.0,
            "leftover_cash": investable,
            "holdings":      []
        }

    total_score = sum(float(p["final_score"]) for p in picks)
    if total_score == 0:
        total_score = 1

    allocation  = []
    total_spent = 0.0

    for pick in picks:
        price = float(pick["price"])
        score = float(pick["final_score"])

        weight     = score / total_score
        raw_amount = investable * weight
        capped     = min(raw_amount, budget * MAX_STOCK_PCT)
        shares     = int(capped // price)

        if shares >= 1:
            spent = round(shares * price, 2)
            total_spent += spent
            allocation.append({
                "symbol":  pick["symbol"],
                "shares":  shares,
                "price":   round(price, 2),
                "spent":   spent,
                "pct":     round(spent / budget * 100, 1),
                "score":   round(score, 1),
                "reason":  pick.get("reason", "")
            })

    leftover  = round(investable - total_spent, 2)

    # Park leftover in LIQUIDBEES
    etf_units = int(leftover // LIQUID_ETF["price"])
    if etf_units >= 1:
        etf_spent = etf_units * LIQUID_ETF["price"]
        allocation.append({
            "symbol": LIQUID_ETF["symbol"],
            "shares": etf_units,
            "price":  LIQUID_ETF["price"],
            "spent":  etf_spent,
            "pct":    round(etf_spent / budget * 100, 1),
            "score":  0,
            "reason": "Idle cash parked in liquid ETF"
        })
        leftover = round(leftover - etf_spent, 2)

    return {
        "budget":        budget,
        "reserve":       reserve,
        "investable":    investable,
        "total_spent":   round(total_spent, 2),
        "leftover_cash": round(leftover, 2),
        "holdings":      allocation
    }

if __name__ == "__main__":
    test = [
        {"symbol": "INFY",     "price": 1346.0, "final_score": 75},
        {"symbol": "HDFCBANK", "price": 797.0,  "final_score": 68},
        {"symbol": "WIPRO",    "price": 202.0,  "final_score": 55},
        {"symbol": "ITC",      "price": 420.0,  "final_score": 61},
    ]
    plan = allocate(5000, test)
    print(f"Budget: ₹{plan['budget']}")
    for h in plan["holdings"]:
        print(f"  {h['symbol']:12} {h['shares']} shares "
              f"× ₹{h['price']} = ₹{h['spent']} ({h['pct']}%)")
    print(f"Leftover: ₹{plan['leftover_cash']}")