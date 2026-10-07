"""Builds the interactive HTML dashboard (pure HTML/CSS/SVG, works in light & dark)."""
from html import escape as e

CSS = """<style>
.vra{color:var(--body-text-color,inherit)}
.vra .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin-bottom:14px}
.vra .card{border:1px solid rgba(128,128,128,.28);border-radius:16px;padding:16px 18px;background:rgba(128,128,128,.07)}
.vra h4{margin:0 0 12px;font-size:15px;opacity:.9}
.vra .big{font-size:34px;font-weight:800;line-height:1.1}
.vra .sub{opacity:.7;font-size:13px}
.vra .bar{height:10px;border-radius:6px;background:rgba(128,128,128,.22);overflow:hidden}
.vra .bar i{display:block;height:100%;border-radius:6px;transition:width .8s}
.vra .row{margin:11px 0}.vra .row .t{display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px}
.vra .chip{display:inline-block;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:600;margin:2px 4px 2px 0}
.vra ul{margin:0;padding-left:18px}.vra li{margin:6px 0}
.vra .pm{position:relative;height:14px;border-radius:7px;background:rgba(128,128,128,.22);margin:34px 0 26px}
.vra .pm .fair{position:absolute;top:0;height:100%;background:rgba(34,197,94,.55);border-radius:7px}
.vra .pm .ask{position:absolute;top:-8px;width:4px;height:30px;border-radius:2px}
.vra .pm .lbl{position:absolute;font-size:11px;white-space:nowrap;transform:translateX(-50%)}
.vra .cl label{display:block;margin:7px 0;cursor:pointer}.vra .cl input{margin-right:8px;transform:scale(1.15)}
.vra .tag{font-size:12px;opacity:.7}
</style>"""


def inr(x):
    x = int(round(x)); s = str(abs(x))
    if len(s) > 3:
        last, rest, parts = s[-3:], s[:-3], []
        while len(rest) > 2:
            parts.insert(0, rest[-2:]); rest = rest[:-2]
        if rest: parts.insert(0, rest)
        s = ",".join(parts + [last])
    return ("-" if x < 0 else "") + "₹" + s


def _col(ratio):
    return "#22c55e" if ratio < .34 else "#f59e0b" if ratio < .67 else "#ef4444"


BAND = {"Low Risk": "#22c55e", "Moderate Risk": "#eab308", "High Risk": "#f97316", "Very High Risk": "#ef4444"}
PRICE_COL = {"FAIR / GOOD": "#22c55e", "SLIGHTLY HIGH": "#f59e0b", "HIGH": "#ef4444", "SUSPICIOUSLY LOW": "#a855f7"}
ICON = {"car": "🚗", "bike": "🏍️", "scooter": "🛵"}


def placeholder():
    return CSS + '<div class="vra"><div class="card" style="text-align:center;padding:40px">' \
        '<div style="font-size:42px">📊</div><h3>Dashboard yahan dikhega</h3>' \
        '<div class="sub">Left side mein vehicle details bharo aur <b>Analyze</b> dabao.</div></div></div>'


def render(r):
    v, p, k, rep = r["vehicle"], r["price"], r["risk"], r["report"]
    bc = BAND.get(k["label"], "#eab308")
    arc = 251.3
    gauge = (f'<svg viewBox="0 0 200 120" style="width:100%;max-width:260px">'
             f'<path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="rgba(128,128,128,.25)" stroke-width="16" stroke-linecap="round"/>'
             f'<path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="{bc}" stroke-width="16" stroke-linecap="round" '
             f'stroke-dasharray="{arc * k["total"] / 100:.1f} {arc}"/>'
             f'<text x="100" y="92" text-anchor="middle" font-size="38" font-weight="800" fill="currentColor">{k["total"]}</text>'
             f'<text x="100" y="112" text-anchor="middle" font-size="12" fill="currentColor" opacity=".7">out of 100</text></svg>')
    head = (f'<div class="card" style="text-align:center"><h4>Overall Risk</h4>{gauge}'
            f'<div class="big" style="color:{bc};font-size:24px">{k["emoji"]} {e(k["label"])}</div>'
            f'<div class="sub" style="margin-top:6px">{e(rep.get("summary", ""))}</div></div>')

    info = (f'<div class="card"><h4>{ICON.get(v["kind"], "🚘")} Vehicle</h4>'
            f'<div class="big" style="font-size:22px">{e(v["name"])}</div>'
            f'<div class="sub" style="margin-bottom:12px">{v["year"]} · {v["age"]} yrs · {v["km"]:,} km · {v["owners"]} owner(s)</div>'
            f'<span class="chip" style="background:rgba(128,128,128,.2)">Service: {e(v["service"])}</span>'
            f'<span class="chip" style="background:rgba(128,128,128,.2)">Accident: {e(v["accident"])}</span>'
            f'<span class="chip" style="background:rgba(128,128,128,.2)">{v["kind"].title()}</span>'
            f'<div class="sub" style="margin-top:12px">Base (new) price used: {inr(v["base_price"])}</div></div>')

    lo = min(p["asking"], p["fair_low"]) * .85; hi = max(p["asking"], p["fair_high"]) * 1.15
    pos = lambda x: max(0, min(100, (x - lo) / (hi - lo) * 100))
    pc = PRICE_COL.get(p["label"], "#f59e0b")
    price = (f'<div class="card"><h4>💰 Price Analysis</h4>'
             f'<div class="big" style="color:{pc};font-size:24px">{e(p["label"])}</div>'
             f'<div class="sub">Asking {inr(p["asking"])} vs fair {inr(p["fair_low"])} – {inr(p["fair_high"])}</div>'
             f'<div class="pm"><div class="fair" style="left:{pos(p["fair_low"]):.1f}%;width:{pos(p["fair_high"]) - pos(p["fair_low"]):.1f}%"></div>'
             f'<div class="lbl" style="left:{(pos(p["fair_low"]) + pos(p["fair_high"])) / 2:.1f}%;top:20px;color:#22c55e">fair range</div>'
             f'<div class="ask" style="left:{pos(p["asking"]):.1f}%;background:{pc}"></div>'
             f'<div class="lbl" style="left:{pos(p["asking"]):.1f}%;top:-26px;color:{pc}">asking {inr(p["asking"])}</div></div>'
             f'<div class="tag">Demo model (synthetic data) — approximate hai, final price negotiate karke hi decide karo.</div></div>')

    rows = "".join(
        f'<div class="row"><div class="t"><span>{e(a)}</span><span>{pts}/{k["max"][a]}</span></div>'
        f'<div class="bar"><i style="width:{pts / k["max"][a] * 100:.0f}%;background:{_col(pts / k["max"][a])}"></i></div></div>'
        for a, pts in k["parts"].items())
    breakdown = f'<div class="card"><h4>📉 Risk Breakdown</h4>{rows}</div>'

    sev = {"none": "#22c55e", "minor": "#f59e0b", "possible_concern": "#ef4444"}
    if r["vision"]:
        obs = "".join(f'<li><span class="chip" style="background:{sev.get(o.get("severity"), "#888")}33;color:{sev.get(o.get("severity"), "#888")}">'
                      f'{e(str(o.get("severity", "")).replace("_", " "))}</span><b>{e(str(o.get("area", "")))}</b>: {e(str(o.get("observation", "")))}</li>'
                      for o in r["vision"])
        photos = f'<div class="card"><h4>📷 Photo Observations</h4><ul style="list-style:none;padding:0">{obs}</ul>' \
                 f'<div class="tag">Possible signs only — mechanical diagnosis nahi hai.</div></div>'
    else:
        photos = f'<div class="card"><h4>📷 Photo Observations</h4><div class="sub">{e(r["vision_status"])}</div></div>'

    ul = lambda xs: "<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in xs) + "</ul>"
    cl = "".join(f'<label><input type="checkbox">{e(str(x))}</label>' for x in rep["checklist"])
    concerns = f'<div class="card" style="border-color:#ef444466"><h4>⚠️ Potential Concerns</h4>{ul(rep["concerns"])}</div>'
    pos_c = f'<div class="card" style="border-color:#22c55e66"><h4>✅ Positive Factors</h4>{ul(rep["positives"])}</div>'
    qs = f'<div class="card"><h4>🔍 Questions for Seller</h4>{ul(rep["seller_questions"])}</div>'
    chk = f'<div class="card cl"><h4>🔧 Pre-Purchase Checklist <span class="tag">(tick karte jao)</span></h4>{cl}</div>'

    return (CSS + '<div class="vra">'
            f'<div class="grid">{head}{info}{price}</div>'
            f'<div class="grid">{breakdown}{photos}</div>'
            f'<div class="grid">{concerns}{pos_c}</div>'
            f'<div class="grid">{qs}{chk}</div>'
            '<div class="tag" style="text-align:center">Ye AI-based estimate hai. Khareedne se pehle independent mechanic inspection zaroor karwao.</div>'
            '</div>')
