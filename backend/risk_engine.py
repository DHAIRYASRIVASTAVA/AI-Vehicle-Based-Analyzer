"""Rule-based risk scoring. Higher points = riskier. Total 100."""
from .catalog import KM_PER_YEAR

MAX = {"Mileage": 25, "Age": 15, "Owners": 10, "Service": 20, "Accident": 20, "Price": 10}


def band(score):
    if score <= 25: return "Low Risk", "🟢"
    if score <= 50: return "Moderate Risk", "🟡"
    if score <= 75: return "High Risk", "🟠"
    return "Very High Risk", "🔴"


def compute(kind, age, km, owners, service, accident, price_points, vision_obs):
    expected = max(age, 1) * KM_PER_YEAR[kind]
    ratio = km / expected
    mileage = min(1, max(0, (ratio - 0.5) / 1.5)) * MAX["Mileage"]
    age_pts = min(1, age / 12) * MAX["Age"]
    owner_pts = {1: 0, 2: 5, 3: 8}.get(owners, 10)
    service_pts = {"Available": 4, "Partial": 10, "Unknown": 14, "Not available": 20}[service]
    acc = {"No": 0, "Unknown": 10, "Yes": 20}[accident]
    bump = sum(3 for o in vision_obs if o.get("severity") == "possible_concern") \
         + sum(1 for o in vision_obs if o.get("severity") == "minor")
    acc = min(MAX["Accident"], acc + min(bump, 8))
    parts = {"Mileage": mileage, "Age": age_pts, "Owners": owner_pts,
             "Service": service_pts, "Accident": acc, "Price": price_points}
    parts = {k: round(v, 1) for k, v in parts.items()}
    total = round(sum(parts.values()))
    label, emoji = band(total)
    return {"total": total, "label": label, "emoji": emoji, "parts": parts,
            "max": MAX, "km_ratio": round(ratio, 2)}
