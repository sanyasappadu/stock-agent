import sys, os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from dotenv import load_dotenv
load_dotenv()

UPSTOX_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
PAPER_MODE   = os.getenv("PAPER_MODE", "true") == "true"
BASE_URL     = "https://api.upstox.com/v2"

HEADERS = {
    "Authorization": f"Bearer {UPSTOX_TOKEN}",
    "Content-Type":  "application/json",
    "Accept":        "application/json"
}

SYMBOL_TO_ISIN = {
    "RELIANCE":   "NSE_EQ|INE002A01018",
    "TCS":        "NSE_EQ|INE467B01029",
    "INFY":       "NSE_EQ|INE009A01021",
    "HDFCBANK":   "NSE_EQ|INE040A01034",
    "WIPRO":      "NSE_EQ|INE075A01022",
    "ICICIBANK":  "NSE_EQ|INE090A01021",
    "BAJFINANCE": "NSE_EQ|INE296A01024",
    "TITAN":      "NSE_EQ|INE280A01028",
    "MARUTI":     "NSE_EQ|INE585B01010",
    "ADANIENT":   "NSE_EQ|INE423A01024",
    "LIQUIDBEES": "NSE_EQ|INF204KB14I2"
}

# ─────────────────────────────────────────────
#  VERIFY TOKEN
# ─────────────────────────────────────────────
def verify_token() -> dict:
    try:
        resp = requests.get(
            f"{BASE_URL}/user/profile",
            headers=HEADERS, timeout=10
        )
        data = resp.json()
        if data.get("status") == "success":
            p = data["data"]
            return {
                "valid":   True,
                "name":    p.get("user_name"),
                "email":   p.get("email"),
                "broker":  p.get("broker"),
                "message": "Token valid"
            }
        return {"valid": False,
                "message": data.get("message", "Invalid token")}
    except Exception as e:
        return {"valid": False, "message": str(e)}

# ─────────────────────────────────────────────
#  GET FUNDS
# ─────────────────────────────────────────────
def get_funds() -> dict:
    if PAPER_MODE:
        return {
            "status":           "paper_mode",
            "available_margin": 0,
            "used_margin":      0,
            "message":          "Paper mode — no real funds"
        }
    try:
        resp = requests.get(
            f"{BASE_URL}/user/get-funds-and-margin",
            headers=HEADERS,
            params={"segment": "SEC"},
            timeout=10
        )
        data = resp.json()
        if data.get("status") == "success":
            eq = data["data"].get("equity", {})
            return {
                "status":           "success",
                "available_margin": eq.get("available_margin", 0),
                "used_margin":      eq.get("used_margin", 0),
                "total":            eq.get("notional_cash", 0)
            }
        return {"status": "error",
                "message": data.get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────
#  GET PORTFOLIO
# ─────────────────────────────────────────────
def get_portfolio() -> dict:
    if PAPER_MODE:
        return {
            "status":   "paper_mode",
            "holdings": [],
            "message":  "Paper mode — no real holdings"
        }
    try:
        resp = requests.get(
            f"{BASE_URL}/portfolio/long-term-holdings",
            headers=HEADERS, timeout=10
        )
        data = resp.json()
        if data.get("status") == "success":
            return {
                "status":   "success",
                "holdings": data.get("data", [])
            }
        return {"status": "error",
                "message": data.get("message")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────
#  PLACE SINGLE ORDER
# ─────────────────────────────────────────────
def place_order(symbol: str,
                shares: int,
                transaction_type: str = "BUY") -> dict:
    # ── PAPER MODE ──
    if PAPER_MODE:
        return {
            "status":           "PAPER_EXECUTED",
            "symbol":           symbol,
            "shares":           shares,
            "transaction_type": transaction_type,
            "order_id":         f"PAPER_{symbol}_{shares}",
            "message":          f"Paper trade: {transaction_type} "
                                f"{shares} shares of {symbol}"
        }

    # ── LIVE MODE ──
    instrument = SYMBOL_TO_ISIN.get(symbol)
    if not instrument:
        return {
            "status":  "error",
            "message": f"{symbol} not in instrument map"
        }

    try:
        payload = {
            "quantity":           shares,
            "product":            "D",
            "validity":           "DAY",
            "price":              0,
            "tag":                "stock-agent",
            "instrument_token":   instrument,
            "order_type":         "MARKET",
            "transaction_type":   transaction_type,
            "disclosed_quantity": 0,
            "trigger_price":      0,
            "is_amo":             False
        }
        resp = requests.post(
            f"{BASE_URL}/order/place",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        data = resp.json()
        if data.get("status") == "success":
            return {
                "status":   "EXECUTED",
                "symbol":   symbol,
                "shares":   shares,
                "order_id": data["data"]["order_id"],
                "message":  f"Real order: {transaction_type} "
                            f"{shares} {symbol}"
            }
        return {
            "status":  "FAILED",
            "symbol":  symbol,
            "message": data.get("message", "Unknown error")
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ─────────────────────────────────────────────
#  PLACE ALL ORDERS FROM ALLOCATION PLAN
# ─────────────────────────────────────────────
def place_all_orders(allocation: dict) -> list:
    results  = []
    holdings = allocation.get("holdings", [])

    for h in holdings:
        if h["symbol"] == "LIQUIDBEES":
            results.append({
                "symbol":  "LIQUIDBEES",
                "status":  "SKIPPED",
                "message": "Liquid ETF — handled separately"
            })
            continue

        result = place_order(
            symbol           = h["symbol"],
            shares           = h["shares"],
            transaction_type = "BUY"
        )
        results.append(result)
        status = result.get("status", "UNKNOWN")
        msg    = result.get("message", "")
        print(f"  [{status}] {h['symbol']} "
              f"x{h['shares']} — {msg}")

    return results

# ─────────────────────────────────────────────
#  TEST SCRIPT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 52)
    print("   UPSTOX BROKER — CONNECTION TEST")
    print("=" * 52)
    print(f"  Mode      : {'PAPER' if PAPER_MODE else 'LIVE'}")
    print(f"  Token set : {bool(UPSTOX_TOKEN)}")
    print()

    if PAPER_MODE:
        print("  Running in PAPER MODE")
        print("  To switch to LIVE: set PAPER_MODE=false in .env")
        print()
        # Simulate a paper order
        test = place_order("WIPRO", 2, "BUY")
        print(f"  Paper order test:")
        print(f"  Status   : {test['status']}")
        print(f"  Order ID : {test['order_id']}")
        print(f"  Message  : {test['message']}")
    else:
        print("  LIVE MODE — testing Upstox connection...")
        print()
        result = verify_token()
        if result["valid"]:
            print(f"  Connected : {result['name']}")
            print(f"  Email     : {result['email']}")
            print()
            funds = get_funds()
            if funds["status"] == "success":
                print(f"  Available : ₹{funds['available_margin']}")
                print(f"  Used      : ₹{funds['used_margin']}")
            else:
                print(f"  Funds err : {funds['message']}")
        else:
            print(f"  Token err : {result['message']}")
            print()
            print("  Run python refresh_token.py to get new token")

    print()
    print("=" * 52)