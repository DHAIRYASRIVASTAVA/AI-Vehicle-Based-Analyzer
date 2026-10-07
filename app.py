"""FastAPI backend (/api/*) + interactive Gradio dashboard at /. Run: uvicorn app:app --reload"""
from dotenv import load_dotenv
load_dotenv()

import os, shutil, tempfile
from typing import Optional
import gradio as gr
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from backend import service, db, dashboard
from backend.catalog import CATALOG, KINDS, names_for

api = FastAPI(title="Used Vehicle Risk Analyzer")


@api.get("/api/health")
def health():
    return {"ok": True}


@api.post("/api/analyze")
async def analyze_endpoint(name: str = Form(...), kind: str = Form("car"), year: int = Form(...),
                           km: int = Form(...), owners: int = Form(...), price: float = Form(...),
                           service_history: str = Form("Unknown"), accident: str = Form("Unknown"),
                           new_price: Optional[float] = Form(None),
                           images: list[UploadFile] = File(default=[])):
    if kind not in KINDS:
        raise HTTPException(400, "kind must be car/bike/scooter")
    tmp = tempfile.mkdtemp(); paths = []
    for i, f in enumerate(images[:5]):
        p = os.path.join(tmp, f"{i}.img")
        with open(p, "wb") as out: shutil.copyfileobj(f.file, out)
        paths.append(p)
    try:
        return service.analyze(name, kind, year, km, owners, price, service_history, accident, paths, new_price)
    except ValueError as ex:
        raise HTTPException(400, str(ex))


@api.get("/api/reports/{rid}")
def report(rid: int):
    r = db.get(rid)
    if not r: raise HTTPException(404, "Not found")
    return r


@api.get("/api/history")
def hist():
    return db.history()


# ---------------- Gradio dashboard ----------------
def run(kind, name, year, km, owners, price, svc, acc, new_price, files):
    paths = [f if isinstance(f, str) else f.name for f in (files or [])]
    try:
        r = service.analyze(name, kind, year, km, owners, price, svc, acc, paths, new_price)
    except ValueError as ex:
        raise gr.Error(str(ex))
    return dashboard.render(r), r


def on_kind(k):
    names = names_for(k)
    return gr.update(choices=names, value=names[0])


def chat(q, r):
    if not r: return "Pehle vehicle analyze karo, phir sawal poocho."
    if not q or not q.strip(): return "Sawal likho."
    return service.ask(q, r)


def load_history():
    return [[h["id"], h["vehicle"], h["score"], h["label"], h["created"][:16].replace("T", " ")] for h in db.history()]


HERO = """<div style="padding:22px 24px;border-radius:18px;background:linear-gradient(135deg,#2563eb,#7c3aed);color:white;margin-bottom:6px">
<div style="font-size:26px;font-weight:800">🚗 AI Used Vehicle Risk & Value Analyzer</div>
<div style="opacity:.9;margin-top:4px">Car, bike ya scooter — risk score, fair price, photo analysis aur seller questions, ek jagah.</div></div>"""

with gr.Blocks(title="AI Used Vehicle Risk Analyzer", theme=gr.themes.Soft(primary_hue="indigo")) as demo:
    gr.HTML(HERO)
    state = gr.State(None)
    with gr.Row():
        with gr.Column(scale=4, min_width=320):
            gr.Markdown("### 📝 Vehicle details")
            kind = gr.Radio(KINDS, value="car", label="Type")
            name = gr.Dropdown(names_for("car"), value="Honda City", allow_custom_value=True,
                               label="Make & model (list se chuno ya khud type karo)")
            with gr.Row():
                year = gr.Number(label="Year", value=2020, precision=0, minimum=1980)
                km = gr.Number(label="Mileage (km)", value=72000, precision=0, minimum=0, step=1000)
            owners = gr.Slider(1, 5, value=2, step=1, label="Owners")
            price = gr.Number(label="Asking price (₹)", value=820000, precision=0, minimum=1000, step=1000,
                              info="Poora rupees mein, jaise 45000 ya 820000")
            new_price = gr.Number(label="New/ex-showroom price (₹) — optional", value=None, precision=0, minimum=0, step=1000,
                                  info="Custom model ho to daalo, accuracy badhti hai")
            svc = gr.Radio(["Available", "Partial", "Not available", "Unknown"], value="Available", label="Service history")
            acc = gr.Radio(["No", "Yes", "Unknown"], value="Unknown", label="Accident history")
            files = gr.File(label="Photos (3–5, optional)", file_count="multiple", file_types=["image"])
            btn = gr.Button("🔍 Analyze", variant="primary", size="lg")
            gr.Examples(
                [["car", "Honda City", 2020, 72000, 2, 820000, "Available", "Unknown", None],
                 ["bike", "Royal Enfield Classic 350", 2019, 38000, 1, 95000, "Partial", "No", None],
                 ["scooter", "Honda Activa 6G", 2021, 15000, 1, 52000, "Available", "No", None],
                 ["bike", "Yamaha R15 V3", 2018, 30000, 2, 90000, "Unknown", "Unknown", 180000]],
                [kind, name, year, km, owners, price, svc, acc, new_price], label="Quick examples")
        with gr.Column(scale=8):
            with gr.Tabs():
                with gr.Tab("📊 Dashboard"):
                    out = gr.HTML(dashboard.placeholder())
                with gr.Tab("💬 Ask AI"):
                    gr.Markdown("Inspection ya maintenance ke baare mein poocho (FAISS RAG + AI).")
                    q = gr.Textbox(label="Sawal", placeholder="e.g. Bumper repaint ke signs kaise check karun?")
                    ask_btn = gr.Button("Ask")
                    ans = gr.Markdown()
                with gr.Tab("🕘 History"):
                    hist = gr.Dataframe(headers=["ID", "Vehicle", "Score", "Risk", "Time"], interactive=False)
                    gr.Button("Refresh").click(load_history, None, hist)

    kind.input(on_kind, kind, name)
    btn.click(run, [kind, name, year, km, owners, price, svc, acc, new_price, files], [out, state]) \
       .then(load_history, None, hist)
    ask_btn.click(chat, [q, state], ans)
    q.submit(chat, [q, state], ans)
    demo.load(load_history, None, hist)

app = gr.mount_gradio_app(api, demo, path="/")
