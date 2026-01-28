import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron          import CronTrigger
from dotenv                             import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler()

def run_sip_for_user(user_id: str, budget: float,
                     risk_level: str = "moderate"):
    from agent.orchestrator  import run_agent
    from backend.database    import save_trade
    print(f"\n[SIP] Running for {user_id} — ₹{budget}")
    try:
        result = run_agent(budget, risk_level)
        save_trade(
            user_id     = user_id,
            budget      = budget,
            risk_level  = risk_level,
            allocation  = result["allocation"],
            explanation = result["explanation"],
            top_stocks  = result["top_stocks"],
            mode        = "paper"
        )
        print(f"[SIP] Done for {user_id}")
    except Exception as e:
        print(f"[SIP] Error for {user_id}: {e}")

def trigger_all_sips():
    from backend.database import get_active_sips
    sips = get_active_sips()
    print(f"[SIP] Triggering {len(sips)} active SIPs")
    for sip in sips:
        run_sip_for_user(
            sip["user_id"],
            sip["monthly_amt"],
            sip["risk_level"]
        )

def start_scheduler():
    # Runs on 1st of every month at 9:15 AM (NSE open)
    scheduler.add_job(
        func    = trigger_all_sips,
        trigger = CronTrigger(day=1, hour=9, minute=15),
        id      = "monthly_sip",
        name    = "Monthly SIP Runner",
        replace_existing = True
    )
    scheduler.start()
    print("[Scheduler] Started — SIP runs on 1st of every month at 9:15 AM")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")