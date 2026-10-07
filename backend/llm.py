"""Vision + report generation via any OpenAI-compatible API, with offline fallbacks."""
import base64, io, json, os, re
from PIL import Image

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


def _client():
    key = os.getenv("LLM_API_KEY")
    if not key or OpenAI is None:
        return None
    return OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))


def _json(text):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


def _b64(path):
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


VISION_PROMPT = """You are assisting a used-vehicle buyer. Look at the photos and list VISUAL observations only.
Never give a definitive mechanical diagnosis. Use cautious wording ("possible", "signs of").
Return ONLY JSON: {"observations":[{"area":str,"observation":str,"severity":"none|minor|possible_concern"}]}
Cover: bumpers/panels (repaint, gaps, mismatch), scratches/dents, rust, lights, tyres, interior wear if visible."""


def analyze_images(paths):
    c = _client()
    if not c or not paths:
        why = "no photos uploaded" if not paths else "LLM_API_KEY not set"
        return [], f"Image analysis skipped ({why})."
    content = [{"type": "text", "text": VISION_PROMPT}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_b64(p)}"}} for p in paths[:5]]
    try:
        r = c.chat.completions.create(model=os.getenv("VISION_MODEL", "gpt-4o-mini"),
                                      messages=[{"role": "user", "content": content}], max_tokens=900)
        return _json(r.choices[0].message.content).get("observations", []), "ok"
    except Exception as e:
        return [], f"Image analysis failed: {e}"


REPORT_PROMPT = """You are a cautious used-vehicle advisor for an Indian buyer. Using ONLY the data below,
write a report. Visual notes are possibilities, not diagnoses. Return ONLY JSON:
{"summary":str,"concerns":[str],"positives":[str],"seller_questions":[str],"checklist":[str]}
Give 4-6 personalised seller questions and 8 checklist items.

DATA:
%s

REFERENCE KNOWLEDGE:
%s"""


def _fallback(d):
    p, r, pr = d["vehicle"], d["risk"], d["price"]
    parts, mx = r["parts"], r["max"]
    concerns, positives, qs = [], [], []
    if parts["Mileage"] / mx["Mileage"] > .4:
        concerns.append(f"Mileage ({p['km']:,} km) is high for a {p['age']}-year-old vehicle.")
        qs.append("How was the vehicle used (city/highway/commercial)?")
    if parts["Service"] / mx["Service"] > .4:
        concerns.append(f"Service history is '{p['service']}'.")
        qs += ["Can you share all service invoices?", "When was the last major service?"]
    else:
        positives.append("Service history is available.")
    if p["accident"] != "No":
        concerns.append(f"Accident history is '{p['accident']}'.")
        qs.append("Has there been any insurance claim or accident repair?")
    else:
        positives.append("Seller reports no accident history.")
    for o in d["vision"]:
        if o.get("severity") in ("minor", "possible_concern"):
            concerns.append(f"{o['area']}: {o['observation']}")
            qs.append(f"Can you explain the condition of the {o['area'].lower()}?")
    if pr["label"] in ("HIGH", "SLIGHTLY HIGH"):
        concerns.append(f"Asking price is above the estimated fair range (₹{pr['fair_low']:,} – ₹{pr['fair_high']:,}).")
        qs.append("Is there room to negotiate on price?")
    elif pr["label"] == "FAIR / GOOD":
        positives.append("Asking price is within or below the estimated fair range.")
    if p["owners"] <= 1:
        positives.append("Single owner.")
    qs.append("When were the tyres and battery last replaced?")
    checklist = ["Engine cold-start check", "Brake inspection", "Suspension check", "Tyre condition",
                 "Odometer verification", "Service records", "Chassis/VIN verification",
                 "Independent mechanic inspection"]
    return {"summary": f"Overall {r['label']} ({r['total']}/100). Verify the flagged points before paying.",
            "concerns": concerns or ["No major concerns from the provided data."],
            "positives": positives or ["—"], "seller_questions": qs, "checklist": checklist}


def generate_report(d, context):
    c = _client()
    if not c:
        return _fallback(d)
    try:
        r = c.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"), max_tokens=1200,
            messages=[{"role": "user", "content": REPORT_PROMPT % (json.dumps(d, default=str), context)}])
        return _json(r.choices[0].message.content)
    except Exception:
        return _fallback(d)


def answer(question, d, context):
    c = _client()
    if not c:
        return "LLM_API_KEY set karo to get AI answers. Relevant guideline:\n\n" + context[:700]
    r = c.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"), max_tokens=500,
        messages=[{"role": "system", "content": "Answer using the reference knowledge and the analysis. Be concise and cautious."},
                  {"role": "user", "content": f"ANALYSIS:\n{json.dumps(d, default=str)}\n\nKNOWLEDGE:\n{context}\n\nQ: {question}"}])
    return r.choices[0].message.content
