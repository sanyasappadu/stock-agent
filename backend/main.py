import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi                  import FastAPI, HTTPException
from fastapi.middleware.cors  import CORSMiddleware
from pydantic                 import BaseModel
from dotenv                   import load_dotenv
from agent.orchestrator       import run_agent
from backend.database         import (save_trade, get_trade_history,
                                       init_db, Session, SIPSchedule)
from backend.scheduler        import start_scheduler, stop_scheduler
import uuid
import math

def sanitize(obj):
    """Recursively replace NaN/Inf with None so JSON serializes cleanly."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(i) for i in obj]
    return obj

load_dotenv()

app = FastAPI(title="Stock Agent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000",
                         "http://127.0.0.1:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"]
)

@app.on_event("startup")
def startup():
    try:
        init_db()
        print("Database ready")
    except Exception as e:
        print(f"DB warning: {e}")
    try:
        start_scheduler()
    except Exception as e:
        print(f"Scheduler warning: {e}")

@app.on_event("shutdown")
def shutdown():
    stop_scheduler()

# ── Models ──────────────────────────────────────────────
class InvestRequest(BaseModel):
    budget:     float
    risk_level: str = "moderate"
    user_id:    str = "demo_user"
    mode:       str = "paper"

class SIPRequest(BaseModel):
    user_id:     str
    monthly_amt: float
    risk_level:  str = "moderate"

# ── Routes ──────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "Stock Agent API running",
            "version": "2.0.0"}

@app.get("/health")
def health():
    return {
        "status":     "ok",
        "paper_mode": os.getenv("PAPER_MODE", "true"),
        "scheduler":  "running"
    }

@app.post("/invest")
def invest(req: InvestRequest):
    result = run_agent(req.budget, req.risk_level)
    result = sanitize(result)          
    try:
        trade_id = save_trade(
            user_id     = req.user_id,
            budget      = req.budget,
            risk_level  = req.risk_level,
            allocation  = result["allocation"],
            explanation = result["explanation"],
            top_stocks  = result["top_stocks"],
            mode        = result["mode"]
        )
        result["trade_id"] = trade_id
    except Exception as e:
        print(f"DB save warning: {e}")
        result["trade_id"] = None
    return result

@app.get("/history/{user_id}")
def get_history(user_id: str):
    try:
        return {"user_id": user_id,
                "trades":  get_trade_history(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/watchlist")
def get_watchlist():
    from agent.tools.market_data import get_all_prices
    prices = get_all_prices()
    return sanitize({"prices": prices})

@app.post("/sip/setup")
def setup_sip(req: SIPRequest):
    session = Session()
    try:
        # Remove old SIP for this user if exists
        session.query(SIPSchedule)\
               .filter_by(user_id=req.user_id)\
               .delete()

        sip = SIPSchedule(
            id          = str(uuid.uuid4()),
            user_id     = req.user_id,
            monthly_amt = req.monthly_amt,
            risk_level  = req.risk_level
        )
        session.add(sip)
        session.commit()
        return {
            "status":      "SIP created successfully",
            "user_id":     req.user_id,
            "monthly_amt": req.monthly_amt,
            "risk_level":  req.risk_level,
            "runs_on":     "1st of every month at 9:15 AM"
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

@app.get("/sip/{user_id}")
def get_sip(user_id: str):
    session = Session()
    try:
        sip = session.query(SIPSchedule)\
                     .filter_by(user_id=user_id,
                                active="true").first()
        if not sip:
            return {"active": False,
                    "message": "No active SIP found"}
        return {
            "active":      True,
            "monthly_amt": sip.monthly_amt,
            "risk_level":  sip.risk_level,
            "created_at":  sip.created_at.isoformat()
        }
    finally:
        session.close()

@app.delete("/sip/{user_id}")
def cancel_sip(user_id: str):
    session = Session()
    try:
        session.query(SIPSchedule)\
               .filter_by(user_id=user_id)\
               .update({"active": "false"})
        session.commit()
        return {"status": "SIP cancelled"}
    finally:
        session.close()
@app.get("/market-mood")
def market_mood():
    from agent.tools.market_mood import get_market_mood
    return sanitize(get_market_mood())

@app.get("/behavior/{user_id}")
def behavior(user_id: str):
    from agent.memory.behavior import get_user_behavior_profile
    return get_user_behavior_profile(user_id)
@app.get("/funds")
def get_funds_route():
    from agent.tools.broker import get_funds
    return get_funds()

@app.get("/portfolio")
def get_portfolio_route():
    from agent.tools.broker import get_portfolio
    return get_portfolio()

@app.get("/verify-broker")
def verify_broker_route():
    from agent.tools.broker import verify_token
    return verify_token()

@app.get("/advice/{symbol}")
def stock_advice(symbol: str):
    from agent.tools.advisor import get_stock_advice
    return sanitize(get_stock_advice(symbol.upper()))

@app.get("/advice-all")
def all_advice():
    from agent.tools.advisor  import get_stock_advice
    from agent.tools.market_data import WATCHLIST
    results = []
    for sym in list(WATCHLIST.keys())[:10]:
        results.append(get_stock_advice(sym))
    return sanitize({"advice": results})
@app.get("/scenarios/{user_id}")
def get_scenarios(user_id: str):
    from backend.database        import get_trade_history
    from agent.autonomous        import simulate_scenarios
    trades = get_trade_history(user_id)
    if not trades:
        return {"error": "No trades found"}
    last   = trades[0]
    sc     = simulate_scenarios(
        last["allocation"].get("holdings", []))
    return sanitize(sc)

@app.get("/performance/{user_id}")
def get_performance(user_id: str):
    from backend.database import get_trade_history
    from agent.autonomous import track_performance
    trades = get_trade_history(user_id)
    return sanitize(track_performance(trades))

@app.get("/rebalance-check/{user_id}")
def rebalance_check(user_id: str):
    from backend.database import get_trade_history
    from agent.autonomous import should_rebalance
    from agent.tools.market_mood import get_market_mood
    trades  = get_trade_history(user_id)
    mood    = get_market_mood()
    last_dt = trades[0]["created_at"] if trades else "2020-01-01"
    return sanitize(should_rebalance(last_dt, mood.get("mood","NEUTRAL")))