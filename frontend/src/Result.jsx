import { useState } from 'react'
import { Bar, Card, Gauge, col, inr, num } from './ui.jsx'

const BAND = { 'Low Risk': '#22c55e', 'Moderate Risk': '#eab308', 'High Risk': '#f97316', 'Very High Risk': '#ef4444' }
const PC = { 'FAIR / GOOD': '#22c55e', 'SLIGHTLY HIGH': '#f59e0b', HIGH: '#ef4444', 'SUSPICIOUSLY LOW': '#a855f7' }
const ICON = { car: '🚗', bike: '🏍️', scooter: '🛵' }
const SEV = { none: '#22c55e', minor: '#f59e0b', possible_concern: '#ef4444' }
const Tag = ({ c, children }) => <span className="tag" style={{ background: c + '28', color: c }}>{children}</span>
const List = ({ items }) => <ul className="l">{items.map((x, i) => <li key={i}>{String(x)}</li>)}</ul>

function Odometer({ v }) {
  const T = { car: 12000, bike: 8000, scooter: 6000 }[v.kind] || 10000, L = { car: 250000, bike: 120000, scooter: 90000 }[v.kind] || 150000
  const py = v.km / Math.max(v.age, 1), r = py / T, life = Math.min(100, (v.km / L) * 100)
  const t = r < 0.6 ? ['Low usage', '#22c55e', 'Driven less than typical — verify both the odometer reading and the overall condition.']
    : r <= 1.25 ? ['Normal usage', '#22c55e', 'Driven a normal amount for its age.']
    : r <= 1.7 ? ['High usage', '#f59e0b', 'Driven more than typical — check engine, clutch and suspension wear.']
    : ['Very high usage', '#ef4444', 'Very high running — the price should be lower and a mechanic inspection is a must.']
  return (
    <Card title="🛣️ Odometer insight">
      <div className="big">{num(v.km)} km <span className="mut sm">driven</span></div>
      <div className="fr mt"><span>Per year: <b>{num(py)} km</b> (typical ~{num(T)})</span><b style={{ color: t[1] }}>{t[0]}</b></div>
      <Bar value={Math.min(100, (r / 2) * 100)} color={t[1]} />
      <div className="fr"><span>Estimated life used (~{num(L)} km)</span><b>{Math.round(life)}%</b></div>
      <Bar value={life} color={col(life / 100)} /><div className="mut">{t[2]}</div>
    </Card>)
}
function Mileage({ m }) {
  if (!m) return null
  const V = { good: ['Good mileage', '#22c55e', 'Close to or better than typical — fuel efficiency looks fine.'], slightly_low: ['Slightly low', '#f59e0b', 'Slightly below typical — check it on a test ride.'], low: ['Low mileage', '#ef4444', 'Far below typical — possible engine/injector or tyre issue; have a mechanic check it.'] }[m.verdict]
  return (
    <Card title="⛽ Fuel mileage">
      <div className="big">{m.entered ? m.entered + ' kmpl' : '~' + m.typical + ' kmpl'} <span className="mut sm">{m.entered ? '(seller claim)' : '(typical expected)'}</span></div>
      {V ? <><div className="fr mt"><span>Compared with typical {m.typical} kmpl</span><b style={{ color: V[1] }}>{V[0]}</b></div><Bar value={Math.min(100, (m.ratio * 100) / 1.4)} color={V[1]} /><div className="mut">{V[2]}</div></>
        : <div className="mut mt">Ask the seller for the actual mileage and enter it in the form — we will compare it with the typical value.</div>}
      <div className="fr mt"><span>Fuel cost (petrol ~₹{m.petrol}/L)</span><b>₹{m.cost_per_km}/km · ₹{num(m.cost_per_km * 1000)} per 1,000 km</b></div>
    </Card>)
}
function PriceMeter({ p }) {
  const pc = PC[p.label] || '#f59e0b', lo = Math.min(p.asking, p.fair_low) * 0.85, hi = Math.max(p.asking, p.fair_high) * 1.15
  const pos = x => Math.max(0, Math.min(100, ((x - lo) / (hi - lo)) * 100))
  return (
    <Card title="💰 Price check">
      <div className="big" style={{ color: pc }}>{p.label}</div>
      <div className="mut">Asking {inr(p.asking)} · Fair {inr(p.fair_low)} – {inr(p.fair_high)}</div>
      <div className="pm">
        <div className="f" style={{ left: pos(p.fair_low) + '%', width: pos(p.fair_high) - pos(p.fair_low) + '%' }} />
        <em style={{ left: (pos(p.fair_low) + pos(p.fair_high)) / 2 + '%', top: 20, color: '#22c55e' }}>fair range</em>
        <div className="a" style={{ left: pos(p.asking) + '%', background: pc }} />
        <em style={{ left: pos(p.asking) + '%', top: -28, color: pc }}>asking {inr(p.asking)}</em>
      </div>
      <div className="mut">Demo model (synthetic data) — approximate only.</div>
    </Card>)
}
function Checklist({ items, id }) {
  const key = 'ck' + (id || 'x'), [on, setOn] = useState(() => JSON.parse(localStorage.getItem(key) || '[]'))
  const tog = i => { const n = on.includes(i) ? on.filter(x => x !== i) : [...on, i]; setOn(n); localStorage.setItem(key, JSON.stringify(n)) }
  return (
    <Card title="🔧 Pre-purchase checklist" className="ck">
      <div className="mut sm">{on.length}/{items.length} done</div><Bar value={(on.length / items.length) * 100} color="var(--pri)" />
      {items.map((x, i) => <label key={i} className={on.includes(i) ? 'done' : ''}><input type="checkbox" checked={on.includes(i)} onChange={() => tog(i)} />{x}</label>)}
    </Card>)
}
function AskAI({ id }) {
  const [msgs, setMsgs] = useState([]), [q, setQ] = useState(''), [busy, setBusy] = useState(false)
  const send = async () => {
    const text = q.trim(); if (!text || !id || busy) return
    setQ(''); setBusy(true); setMsgs(m => [...m, { me: true, t: text }])
    try { const r = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id, question: text }) }); const j = await r.json(); setMsgs(m => [...m, { t: j.answer || j.detail }]) }
    catch (e) { setMsgs(m => [...m, { t: 'Error: ' + e.message }]) }
    setBusy(false)
  }
  return (
    <Card title="💬 Ask AI">
      {msgs.map((m, i) => <div key={i} className={'bub ' + (m.me ? 'me' : 'ai')}>{m.t}</div>)}{busy && <div className="bub ai">…</div>}
      <div className="row mt"><input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder="e.g. How do I check for a bumper repaint?" style={{ flex: 4 }} /><button className="go sm-go" onClick={send}>Ask</button></div>
    </Card>)
}

export default function Result({ r, toast }) {
  const [tab, setTab] = useState(0)
  const v = r.vehicle, p = r.price, k = r.risk, rep = r.report, bc = BAND[k.label] || '#eab308'
  const share = () => {
    const t = `${v.name} (${v.year}) – Risk ${k.total}/100 (${k.label}). Asking ${inr(p.asking)}, fair ${inr(p.fair_low)}–${inr(p.fair_high)} (${p.label}).`
    navigator.share ? navigator.share({ title: 'VehicleCheck', text: t }).catch(() => {}) : (navigator.clipboard.writeText(t), toast('Summary copied ✅', 'ok'))
  }
  const pdf = () => { setTab(-1); setTimeout(() => window.print(), 100); setTimeout(() => setTab(0), 800) }
  const show = i => tab === i || tab === -1
  return (
    <div>
      <div className="rtabs">{['Overview', 'Risk & photos', 'Action plan'].map((t, i) => <button key={t} className={tab === i ? 'on' : ''} onClick={() => { setTab(i); window.scrollTo({ top: document.getElementById('app').offsetTop - 8, behavior: 'smooth' }) }}>{t}</button>)}</div>
      {show(0) && <div className="tp">
        <Card className="center"><Gauge key={r.id} score={k.total} color={bc} />
          <div className="big" style={{ color: bc }}>{k.emoji} {k.label}</div><div className="mut mt">{rep.summary}</div>
          <div className="mt"><button className="chip" onClick={share}>📤 Share</button> <button className="chip" onClick={pdf}>🖨️ Save PDF</button></div></Card>
        <Card title={`${ICON[v.kind] || '🚘'} ${v.name}`}><div className="mut">{v.year} · {v.age} yrs · {num(v.km)} km · {v.owners} owner(s)</div>
          <div className="mt"><Tag c="#6366f1">Service: {v.service}</Tag><Tag c="#6366f1">Accident: {v.accident}</Tag></div></Card>
        <Odometer v={v} /><Mileage m={r.mileage} /><PriceMeter p={p} />
      </div>}
      {show(1) && <div className="tp">
        <Card title="📉 Risk breakdown">{Object.entries(k.parts).map(([a, x]) => <div key={a}><div className="fr"><span>{a}</span><b>{x}/{k.max[a]}</b></div><Bar value={(x / k.max[a]) * 100} color={col(x / k.max[a])} /></div>)}</Card>
        <Card title="📷 Photo observations">{r.vision.length ? <><ul className="l plain">{r.vision.map((o, i) => <li key={i}><Tag c={SEV[o.severity] || '#888'}>{(o.severity || '').replace('_', ' ')}</Tag><b>{o.area}</b>: {o.observation}</li>)}</ul><div className="mut">Possible signs only — not a diagnosis.</div></> : <div className="mut">{r.vision_status}</div>}</Card>
        <Card title="⚠️ Concerns" accent="#ef4444"><List items={rep.concerns} /></Card>
        <Card title="✅ Positives" accent="#22c55e"><List items={rep.positives} /></Card>
      </div>}
      {show(2) && <div className="tp">
        <Card title="🔍 Questions for seller"><List items={rep.seller_questions} /></Card>
        <Checklist items={rep.checklist} id={r.id} /><AskAI id={r.id} />
      </div>}
      <div className="mut center pad">This is an AI estimate. Always get an independent mechanic inspection before buying.{r.timings ? ` · ${r.timings.report}s` : ''}</div>
    </div>)
}
export { BAND }
