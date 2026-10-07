"""FastAPI backend (/api/*) + Gradio UI mounted at /. Run: uvicorn app:app --reload"""
from dotenv import load_dotenv
load_dotenv()

import os, shutil, tempfile
import gradio as gr
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from backend import service, db
from backend.catalog import CATALOG

api = FastAPI(title="Used Vehicle Risk Analyzer")


@api.get("/api/health")
def health():
    return {"ok": True}


@api.post("/api/analyze")
async def analyze_endpoint(name: str = Form(...), year: int = Form(...), km: int = Form(...),
                           owners: int = Form(...), price: float = Form(...),
                           service: str = Form("Unknown"), accident: str = Form("Unknown"),
                           images: list[UploadFile] = File(default=[])):
    if name not in CATALOG:
        raise HTTPException(400, "Unknown vehicle")
    tmp = tempfile.mkdtemp(); paths = []
    for i, f in enumerate(images[:5]):
        p = os.path.join(tmp, f"{i}.img")
        with open(p, "wb") as out: shutil.copyfileobj(f.file, out)
        paths.append(p)
    return service.analyze(name, year, km, owners, price, service, accident, paths)


@api.get("/api/reports/{rid}")
def report(rid: int):
    r = db.get(rid)
    if not r: raise HTTPException(404, "Not found")
    return r


@api.get("/api/history")
def hist():
    return db.history()


# ---------------- Gradio UI ----------------
def lakh(x): return f"₹{x/100000:.2f}L"


def run(name, year, km, owners, price_lakh, svc, acc, files):
    if not name or not price_lakh:
        raise gr.Error("Vehicle aur price daalo.")
    paths = [f if isinstance(f, str) else f.name for f in (files or [])]
    r = service.analyze(name, year, km, owners, price_lakh * 100000, svc, acc, paths)
    k, pr, rep = r["risk"], r["price"], r["report"]
    head = f"## {k['emoji']} Risk Score: {k['total']}/100 — {k['label']}\n{rep.get('summary','')}"
    rows = [[a, f"{v}/{k['max'][a]}"] for a, v in k["parts"].items()]
    price_md = (f"**Asking:** {lakh(pr['asking'])}  \n**Estimated fair range:** {lakh(pr['fair_low'])} – {lakh(pr['fair_high'])}  \n"
                f"**Price verdict:** {pr['label']}  \n_Estimate is from a demo model trained on synthetic data._")
    vis = "\n".join(f"- **{o['area']}**: {o['observation']} _({o['severity']})_" for o in r["vision"]) \
        or f"_{r['vision_status']}_"
    bl = lambda xs: "\n".join(f"- {x}" for x in xs)
    report_md = (f"### ⚠️ Potential Concerns\n{bl(rep['concerns'])}\n\n### ✅ Positive Factors\n{bl(rep['positives'])}\n\n"
                 f"### 🔍 Questions for Seller\n{bl(rep['seller_questions'])}\n\n"
                 f"### 🔧 Pre-Purchase Checklist\n" + "\n".join(f"- ☐ {x}" for x in rep["checklist"]) +
                 "\n\n_Visual notes are possibilities, not a mechanical diagnosis. Get an independent inspection._")
    return head, rows, price_md, vis, report_md, r


def chat(q, r):
    if not r: return "Pehle vehicle analyze karo."
    return service.ask(q, r)


with gr.Blocks(title="AI Used Vehicle Risk Analyzer", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚗 AI Used Vehicle Risk & Value Analyzer\nCar/bike kharidne se pehle risk score, fair price aur seller questions pao.")
    state = gr.State(None)
    with gr.Row():
        with gr.Column():
            name = gr.Dropdown(list(CATALOG), label="Vehicle", value="Honda City")
            year = gr.Number(label="Year", value=2020, precision=0)
            km = gr.Number(label="Mileage (km)", value=72000, precision=0)
            owners = gr.Slider(1, 5, value=2, step=1, label="Owners")
            price = gr.Number(label="Asking price (₹ lakh)", value=8.2)
            svc = gr.Radio(["Available", "Partial", "Not available", "Unknown"], value="Available", label="Service history")
            acc = gr.Radio(["No", "Yes", "Unknown"], value="Unknown", label="Accident history")
            files = gr.File(label="Photos (3–5)", file_count="multiple", file_types=["image"])
            btn = gr.Button("Analyze", variant="primary")
        with gr.Column():
            head = gr.Markdown()
            table = gr.Dataframe(headers=["Factor", "Risk points"], interactive=False)
            price_md = gr.Markdown(); vis = gr.Markdown(label="Image observations")
    report_md = gr.Markdown()
    gr.Markdown("### 💬 Ask about inspection / maintenance (RAG)")
    q = gr.Textbox(placeholder="e.g. Bumper repaint ke signs kaise check karun?", label="Question")
    ans = gr.Markdown(); gr.Button("Ask").click(chat, [q, state], ans)
    btn.click(run, [name, year, km, owners, price, svc, acc, files], [head, table, price_md, vis, report_md, state])

app = gr.mount_gradio_app(api, demo, path="/")
