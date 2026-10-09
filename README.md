---
title: AI Used Vehicle Risk Analyzer
emoji: 🚗
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🚗 AI Used Vehicle Risk & Value Analyzer

Vehicle form + photos → vision observations → risk score /100 → price range → LLM report (concerns, seller questions, checklist) + RAG Q&A.

## Run
```bash
pip install -r requirements.txt
cp .env.example .env      # add LLM_API_KEY (optional; works offline with rule-based report)
uvicorn app:app --reload  # UI at http://localhost:8000  |  API docs at /docs
```

## Structure
- `app.py` – FastAPI (`/api/analyze`, `/api/reports/{id}`, `/api/history`) + Gradio UI
- `backend/risk_engine.py` – rule-based scoring (Mileage 25, Age 15, Owners 10, Service 20, Accident 20, Price 10)
- `backend/price_model.py` – sklearn GradientBoosting (synthetic data; plug a real CSV into `train(df)`)
- `backend/llm.py` – vision + report via OpenAI-compatible API (OpenAI/Groq/Gemini), offline fallback
- `backend/rag.py` + `data/knowledge/` – retrieval over inspection guidelines (FAISS; API embeddings or local fastembed, TF-IDF fallback)
- `backend/db.py` – SQLAlchemy, SQLite locally, PostgreSQL on Render

## Deploy

**Docker (local, with PostgreSQL)**
```bash
cp .env.example .env && docker compose up --build   # http://localhost:7860
```

**Render** – push to GitHub → New → Blueprint → select repo (`render.yaml`). Set `LLM_API_KEY`.

**Hugging Face Spaces (free, easiest)**
1. huggingface.co → New Space → SDK: **Docker** → blank.
2. `git remote add space https://huggingface.co/spaces/<user>/<space>` then `git push space main`.
3. Space → Settings → Variables and secrets → add `LLM_API_KEY` (secret), optional `LLM_MODEL`, `VISION_MODEL`, `EMBED_MODEL`.
4. Without `DATABASE_URL` it uses SQLite (resets on restart). For persistence, add an external Postgres (Neon/Supabase) URL as `DATABASE_URL`.

## Frontend (React + Vite)
Source: `frontend/src`. Built output is committed in `static/` so Render needs no Node.
```bash
cd frontend && npm install && npm run dev     # dev server (proxies /api to :8000)
npm run build                                 # rebuilds ../static  (commit it)
```
