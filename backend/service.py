from datetime import datetime
from . import price_model, risk_engine, llm, rag, db
from .catalog import CATALOG


def analyze(name, year, km, owners, price, service, accident, image_paths):
    kind = CATALOG[name][1]
    age = max(0, datetime.now().year - int(year))
    vehicle = {"name": name, "kind": kind, "year": int(year), "age": age, "km": int(km),
               "owners": int(owners), "price": float(price), "service": service, "accident": accident}
    pr = price_model.estimate(name, age, km, owners, service, accident, float(price))
    obs, vstatus = llm.analyze_images(image_paths)
    risk = risk_engine.compute(kind, age, km, owners, service, accident, pr["points"], obs)
    result = {"vehicle": vehicle, "price": pr, "vision": obs, "vision_status": vstatus, "risk": risk}
    ctx = rag.retrieve(f"{name} inspection {service} service {accident} accident paint tyres odometer")
    result["report"] = llm.generate_report(result, ctx)
    result["id"] = db.save(result)
    return result


def ask(question, result):
    return llm.answer(question, result, rag.retrieve(question))
