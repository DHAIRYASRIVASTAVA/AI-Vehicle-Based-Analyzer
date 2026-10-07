"""RAG over data/knowledge/*.md using FAISS.
Embeddings (first available): 1) OpenAI-compatible API (set EMBED_MODEL), 2) local fastembed (ONNX, no torch),
3) fallback to TF-IDF so the app never breaks. FAISS index is cached in data/index/."""
import glob, hashlib, json, os
import numpy as np

_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_KB = os.path.join(_DIR, "knowledge")
_IDX = os.path.join(_DIR, "index")
_state = {}


def _embed(texts):
    """Returns (float32 matrix, backend_tag) or (None, None)."""
    key, model = os.getenv("LLM_API_KEY"), os.getenv("EMBED_MODEL")
    if key and model:
        try:
            from openai import OpenAI
            c = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
            r = c.embeddings.create(model=model, input=texts)
            return np.array([d.embedding for d in r.data], dtype="float32"), f"api-{model}"
        except Exception:
            pass
    try:
        from fastembed import TextEmbedding
        m = _state.get("fe") or _state.setdefault("fe", TextEmbedding("BAAI/bge-small-en-v1.5"))
        return np.array(list(m.embed(texts)), dtype="float32"), "fastembed-bge-small"
    except Exception:
        return None, None


def _chunks():
    out = []
    for f in sorted(glob.glob(os.path.join(_KB, "*.md"))):
        out += [p.strip() for p in open(f, encoding="utf-8").read().split("\n\n") if len(p.strip()) > 40]
    return out


def _build():
    chunks = _chunks()
    sig = hashlib.md5("\n".join(chunks).encode()).hexdigest()[:10]
    try:
        import faiss
        vecs, tag = _embed(chunks)
        if vecs is not None:
            os.makedirs(_IDX, exist_ok=True)
            path = os.path.join(_IDX, f"{tag}-{sig}")
            if os.path.exists(path + ".faiss"):
                index = faiss.read_index(path + ".faiss")
            else:
                faiss.normalize_L2(vecs)
                index = faiss.IndexFlatIP(vecs.shape[1])  # cosine via normalized inner product
                index.add(vecs)
                faiss.write_index(index, path + ".faiss")
                json.dump(chunks, open(path + ".json", "w"))
            _state.update(mode="faiss", index=index, chunks=chunks, faiss=faiss)
            return
    except ImportError:
        pass
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(stop_words="english")
    _state.update(mode="tfidf", vec=vec, mat=vec.fit_transform(chunks), chunks=chunks)


def retrieve(query, k=3):
    if "mode" not in _state:
        _build()
    chunks = _state["chunks"]
    if _state["mode"] == "faiss":
        q, _ = _embed([query])
        if q is not None:
            _state["faiss"].normalize_L2(q)
            _, ids = _state["index"].search(q, min(k, len(chunks)))
            return "\n\n".join(chunks[i] for i in ids[0] if i >= 0)
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    if "vec" not in _state:
        _state["vec"] = TfidfVectorizer(stop_words="english")
        _state["mat"] = _state["vec"].fit_transform(chunks)
    sims = cosine_similarity(_state["vec"].transform([query]), _state["mat"])[0]
    return "\n\n".join(chunks[i] for i in sims.argsort()[::-1][:k])
