import os, json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

url = os.getenv("DATABASE_URL", "sqlite:///./vra.db")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
engine = create_engine(url, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.utcnow)
    vehicle = Column(String(120))
    asking_price = Column(Float)
    risk_score = Column(Integer)
    risk_label = Column(String(30))
    payload = Column(Text)  # full JSON: vehicle, image notes, risk, price, report


Base.metadata.create_all(engine)


def save(result):
    with Session() as s:
        row = Analysis(vehicle=result["vehicle"]["name"], asking_price=result["vehicle"]["price"],
                       risk_score=result["risk"]["total"], risk_label=result["risk"]["label"],
                       payload=json.dumps(result, default=str))
        s.add(row); s.commit()
        return row.id


def get(i):
    with Session() as s:
        row = s.get(Analysis, i)
        return json.loads(row.payload) if row else None


def history(n=20):
    with Session() as s:
        return [{"id": r.id, "vehicle": r.vehicle, "score": r.risk_score, "label": r.risk_label,
                 "created": r.created.isoformat()}
                for r in s.query(Analysis).order_by(Analysis.id.desc()).limit(n)]
