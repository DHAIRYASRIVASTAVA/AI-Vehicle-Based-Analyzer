import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from . import price_model, risk_engine, llm, rag, db
from .catalog import resolve


def analyze(name, kind, year, km, owners, price, service, accident, image_paths, new_price=None):
    now = datetime.now().year
    name = (name or "").strip()
    if not name: raise ValueError("Vehicle ka naam daalo.")
    if not (1980 <= int(year) <= now): raise ValueError(f"Year 1980 se {now} ke beech hona chahiye.")
    if km is None or km < 0: raise ValueError("Mileage galat hai.")
    if price is None or price < 1000: raise ValueError("Asking price kam se kam ₹1,000 hona chahiye.")
    base, kind = resolve(name, kind, new_price)
    age = max(0, now - int(year))
    vehicle = {"name": name, "kind": kind, "year": int(year), "age": age, "km": int(km), "owners": int(owners),
               "price": float(price), "service": service, "accident": accident, "base_price": base}
    t0, tm = time.time(), {}
    with ThreadPoolExecutor(2) as ex:  # photos + knowledge retrieval run in parallel with price model
        fv = ex.submit(llm.analyze_images, image_paths)
        fr = ex.submit(rag.retrieve, f"{name} {kind} inspection {service} service {accident} accident paint tyres odometer")
        pr = price_model.estimate(base, kind, age, km, owners, service, accident, float(price)); tm["price"] = time.time() - t0
        obs, vstatus = fv.result(); tm["vision"] = time.time() - t0
        try: ctx = fr.result(timeout=15)
        except Exception: ctx = ""
        tm["rag"] = time.time() - t0
    risk = risk_engine.compute(kind, age, km, owners, service, accident, pr["points"], obs)
    result = {"vehicle": vehicle, "price": pr, "vision": obs, "vision_status": vstatus, "risk": risk}
    result["report"] = llm.generate_report(result, ctx); tm["report"] = time.time() - t0
    try: result["id"] = db.save(result)
    except Exception as ex: print("[db] save failed:", ex); result["id"] = None
    result["timings"] = {k: round(v, 1) for k, v in tm.items()}
    print("[analyze]", name, result["timings"], flush=True)
    return result


def ask(question, result):
    return llm.answer(question, result, rag.retrieve(question))
