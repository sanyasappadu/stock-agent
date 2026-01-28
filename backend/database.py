import os
import uuid
from datetime import datetime
from sqlalchemy import (create_engine, Column, String,
                        Float, JSON, DateTime, Text)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine       = create_engine(DATABASE_URL)
Session      = sessionmaker(bind=engine)
Base         = declarative_base()

class TradeLog(Base):
    __tablename__ = "trade_logs"
    id          = Column(String, primary_key=True,
                         default=lambda: str(uuid.uuid4()))
    user_id     = Column(String, nullable=False)
    budget      = Column(Float)
    risk_level  = Column(String)
    allocation  = Column(JSON)
    explanation = Column(Text)
    top_stocks  = Column(JSON)
    mode        = Column(String, default="paper")
    created_at  = Column(DateTime, default=datetime.utcnow)

class SIPSchedule(Base):
    __tablename__ = "sip_schedules"
    id            = Column(String, primary_key=True,
                           default=lambda: str(uuid.uuid4()))
    user_id       = Column(String, nullable=False)
    monthly_amt   = Column(Float)
    risk_level    = Column(String, default="moderate")
    active        = Column(String, default="true")
    created_at    = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(engine)
    print("Database tables created successfully")

def save_trade(user_id: str, budget: float, risk_level: str,
               allocation: dict, explanation: str,
               top_stocks: list, mode: str = "paper") -> str:
    session = Session()
    try:
        trade = TradeLog(
            id          = str(uuid.uuid4()),
            user_id     = user_id,
            budget      = budget,
            risk_level  = risk_level,
            allocation  = allocation,
            explanation = explanation,
            top_stocks  = top_stocks,
            mode        = mode
        )
        session.add(trade)
        session.commit()
        return trade.id
    finally:
        session.close()

def get_trade_history(user_id: str) -> list:
    session = Session()
    try:
        trades = session.query(TradeLog)\
                        .filter_by(user_id=user_id)\
                        .order_by(TradeLog.created_at.desc())\
                        .limit(20).all()
        return [{
            "id":          t.id,
            "budget":      t.budget,
            "risk_level":  t.risk_level,
            "allocation":  t.allocation,
            "explanation": t.explanation,
            "mode":        t.mode,
            "created_at":  t.created_at.isoformat()
        } for t in trades]
    finally:
        session.close()

def get_active_sips() -> list:
    session = Session()
    try:
        sips = session.query(SIPSchedule)\
                      .filter_by(active="true").all()
        return [{
            "user_id":    s.user_id,
            "monthly_amt": s.monthly_amt,
            "risk_level": s.risk_level
        } for s in sips]
    finally:
        session.close()

if __name__ == "__main__":
    init_db()