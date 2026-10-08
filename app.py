"""FastAPI: JSON API (/api/*) + app-style frontend (static/index.html). Run: uvicorn app:app --reload"""
import os
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(v, "1")  # small containers: avoid thread oversubscription slowness
from dotenv import load_dotenv
load_dotenv()

import resource, shutil, tempfile, threading, time
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend import service, db, price_model, rag, llm
from backend.catalog import KINDS, names_for

app = FastAPI(title="Used Vehicle Risk Analyzer")
HERE = os.path.dirname(__file__)


@app.on_event("startup")
def warm():
    price_model.warmup()
    threading.Thread(target=lambda: rag.retrieve("warmup"), daemon=True).start()


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/catalog")
def catalog():
    return {k: names_for(k) for k in KINDS}


@app.get("/api/diag")
def diag():
    """Open /api/diag in browser to see what is slow/broken on the server (no secrets shown)."""
    ping = None
    c = llm._client()
    if c:
        t = time.time()
        try:
            c.chat.completions.create(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), max_tokens=5, timeout=10,
                                      messages=[{"role": "user", "content": "hi"}])
            ping = f"ok {time.time() - t:.1f}s"
        except Exception as ex:
            ping = f"FAIL: {str(ex)[:160]}"
    return {"key_set": bool(os.getenv("LLM_API_KEY")), "base_url": os.getenv("LLM_BASE_URL"),
            "llm_model": os.getenv("LLM_MODEL"), "vision_model": os.getenv("VISION_MODEL"),
            "embed_model": os.getenv("EMBED_MODEL"), "price_model_ready": price_model.ready(),
            "rag_mode": rag._state.get("mode"), "peak_mem_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
            "llm_ping": ping}


@app.post("/api/analyze")
def analyze(name: str = Form(...), kind: str = Form("car"), year: int = Form(...), km: int = Form(...),
            owners: int = Form(...), price: float = Form(...), service_history: str = Form("Unknown"),
            accident: str = Form("Unknown"), new_price: Optional[float] = Form(None),
            images: list[UploadFile] = File(default=[])):
    if kind not in KINDS: raise HTTPException(400, "kind must be car/bike/scooter")
    tmp, paths = tempfile.mkdtemp(), []
    try:
        for i, f in enumerate(images[:5]):
            p = os.path.join(tmp, f"{i}.img")
            with open(p, "wb") as out: shutil.copyfileobj(f.file, out)
            paths.append(p)
        return service.analyze(name, kind, year, km, owners, price, service_history, accident, paths, new_price)
    except ValueError as ex:
        raise HTTPException(400, str(ex))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class Ask(BaseModel):
    id: int
    question: str


@app.post("/api/ask")
def ask(a: Ask):
    r = db.get(a.id)
    if not r: raise HTTPException(404, "Pehle vehicle analyze karo.")
    return {"answer": service.ask(a.question, r)}


@app.get("/api/reports/{rid}")
def report(rid: int):
    r = db.get(rid)
    if not r: raise HTTPException(404, "Not found")
    return r


@app.get("/api/history")
def hist():
    return db.history()


app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
