"""Price estimation: GradientBoosting trained on synthetic depreciation data.
Swap `make_synthetic()` with a real CSV via `train(df)` when you have a dataset."""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from .catalog import CATALOG, KM_PER_YEAR

MODEL_PATH = os.path.join(os.path.dirname(__file__), "price_model.joblib")
FEATURES = ["log_base", "age", "km", "owners", "service_ok", "accident", "is_bike"]


def _value(base, age, km, owners, service_ok, accident, is_bike):
    kpy = KM_PER_YEAR["bike" if is_bike else "car"]
    v = base * 0.92 * np.exp(-0.08 * age)
    v *= 1 - 0.12 * np.clip(km / (np.maximum(age, 1) * kpy) - 1, -0.6, 1.5)
    v *= 1 - 0.04 * (owners - 1)
    v *= np.where(service_ok == 1, 1.0, 0.95)
    v *= np.where(accident == 1, 0.82, 1.0)
    return v


def make_synthetic(n=4000, seed=42):
    rng = np.random.default_rng(seed)
    names = list(CATALOG)
    rows = []
    for _ in range(n):
        name = names[rng.integers(len(names))]
        base, kind = CATALOG[name]
        is_bike = int(kind == "bike")
        age = int(rng.integers(0, 14))
        km = max(500, rng.normal(age * KM_PER_YEAR[kind], 5000 if not is_bike else 3500) + 3000)
        owners = int(rng.choice([1, 2, 3, 4], p=[.5, .3, .15, .05]))
        s, a = int(rng.random() < .65), int(rng.random() < .12)
        price = _value(base, age, km, owners, s, a, is_bike) * rng.normal(1, 0.04)
        rows.append([np.log(base), age, km, owners, s, a, is_bike, price])
    return pd.DataFrame(rows, columns=FEATURES + ["price"])


def train(df=None):
    df = make_synthetic() if df is None else df
    m = GradientBoostingRegressor(n_estimators=250, max_depth=3, learning_rate=0.08, random_state=1)
    m.fit(df[FEATURES], df["price"])
    joblib.dump(m, MODEL_PATH)
    return m


_model = None


def _get():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else train()
    return _model


def estimate(name, age, km, owners, service, accident, asking):
    base, kind = CATALOG[name]
    x = pd.DataFrame([[np.log(base), age, km, owners, int(service == "Available"),
                       int(accident == "Yes"), int(kind == "bike")]], columns=FEATURES)
    mid = float(_get().predict(x)[0])
    low, high = mid * 0.95, mid * 1.05
    ratio = asking / high
    if asking < low * 0.8:
        label, pts = "SUSPICIOUSLY LOW", 4
    elif ratio <= 1.0:
        label, pts = "FAIR / GOOD", 0
    elif ratio <= 1.1:
        label, pts = "SLIGHTLY HIGH", min(10, (ratio - 1) / 0.25 * 10)
    else:
        label, pts = "HIGH", min(10, (ratio - 1) / 0.25 * 10)
    return {"fair_low": round(low), "fair_high": round(high), "mid": round(mid),
            "asking": asking, "label": label, "points": round(pts, 1)}
