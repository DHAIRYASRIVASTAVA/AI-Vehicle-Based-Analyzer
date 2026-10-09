import { useEffect, useMemo, useRef, useState } from 'react'
import Result, { BAND } from './Result.jsx'
import { Card, Gauge, Reveal, inr } from './ui.jsx'

const KINDS = [['car', '🚗', 'Car'], ['bike', '🏍️', 'Bike'], ['scooter', '🛵', 'Scooter']]
const PQ = [[25000, '₹25k'], [50000, '₹50k'], [100000, '₹1L'], [300000, '₹3L'], [500000, '₹5L'], [1000000, '₹10L']]
const KQ = [[10000, '10k'], [25000, '25k'], [50000, '50k'], [75000, '75k'], [100000, '1L']]
const STAGES = ['Validating vehicle details…', 'Estimating the fair price range…', 'Checking the photos…', 'Calculating the risk score…', 'Writing the AI report…']
const INIT = { kind: 'car', name: 'Honda City', year: 2020, km: 72000, owners: 2, price: 820000, np: '', kmpl: '', svc: 'Available', acc: 'Unknown' }

const Chips = ({ opts, value, onPick }) => <div className="chips">{opts.map(o => <button type="button" key={o} className={'chip' + (value === o ? ' on' : '')} onClick={() => onPick(o)}>{o}</button>)}</div>
const Field = ({ label, hint, children }) => <label className="fld"><span>{label}{hint && <small> {hint}</small>}</span>{children}</label>

function Loader() {
  const [i, setI] = useState(0)
  useEffect(() => { const t = setInterval(() => setI(x => x + 1), 2800); return () => clearInterval(t) }, [])
  return <div className="ov"><div className="box"><div className="spin" /><b>Analyzing…</b><div className="mut">{STAGES[Math.min(i, 4)]}</div><div className="pg"><i style={{ width: Math.min(92, 8 + i * 18) + '%' }} /></div></div></div>
}

function Form({ onDone, toast, setLoading }) {
  const [f, setF] = useState(INIT), [files, setFiles] = useState([]), [cat, setCat] = useState({ car: [], bike: [], scooter: [] }), [focus, setFocus] = useState(false), [bad, setBad] = useState([])
  const fileRef = useRef(null)
  const set = (k, v) => setF(s => ({ ...s, [k]: v }))
  useEffect(() => { fetch('/api/catalog').then(r => r.json()).then(setCat).catch(() => {}) }, [])
  const sugg = useMemo(() => { const q = focus ? '' : f.name.trim().toLowerCase(); return (cat[f.kind] || []).filter(n => n.toLowerCase().includes(q)) }, [cat, f.kind, f.name, focus])
  const previews = useMemo(() => files.map(x => URL.createObjectURL(x)), [files])
  const err = k => (bad.includes(k) ? ' err' : '')

  const submit = async () => {
    const b = [!f.name.trim() && 'name', !(+f.year >= 1980) && 'year', (f.km === '' || +f.km < 0) && 'km', !(+f.price >= 1000) && 'price'].filter(Boolean)
    setBad(b); if (b.length) return toast('Please fix the highlighted fields (price must be at least ₹1,000)', 'err')
    const fd = new FormData()
    Object.entries({ name: f.name, kind: f.kind, year: f.year, km: f.km, owners: f.owners, price: f.price, service_history: f.svc, accident: f.acc }).forEach(([k, v]) => fd.append(k, v))
    if (f.np) fd.append('new_price', f.np); if (f.kmpl) fd.append('kmpl', f.kmpl); files.forEach(x => fd.append('images', x))
    setLoading(true); const ac = new AbortController(), to = setTimeout(() => ac.abort(), 100000)
    try { const r = await fetch('/api/analyze', { method: 'POST', body: fd, signal: ac.signal }); const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Server error'); onDone(j) }
    catch (e) { toast(e.name === 'AbortError' ? 'The server took too long. Please try again shortly (the free server may be waking up).' : e.message, 'err') }
    finally { clearTimeout(to); setLoading(false) }
  }
  return (
    <div>
      <Card title="Vehicle">
        <div className="seg">{KINDS.map(([k, i, l]) => <button key={k} className={f.kind === k ? 'on' : ''} onClick={() => { set('kind', k); set('name', (cat[k] || [])[0] || '') }}>{i} {l}</button>)}</div>
        <Field label="Make & model" hint="(pick from the list or type any model)"><input className={err('name')} value={f.name} onChange={e => set('name', e.target.value)} onFocus={e => { setFocus(true); e.target.select() }} onBlur={() => setTimeout(() => setFocus(false), 150)} autoComplete="off" /></Field>
        <div className="chips sug">{sugg.map(n => <button key={n} className={'chip' + (n === f.name ? ' on' : '')} onClick={() => { set('name', n); setFocus(false) }}>{n}</button>)}</div>
        <Field label="Year"><input className={err('year')} type="number" inputMode="numeric" value={f.year} onChange={e => set('year', e.target.value)} /></Field>
        <Field label="Kilometres driven" hint="(odometer reading)"><input className={err('km')} type="number" inputMode="numeric" step="1000" value={f.km} onChange={e => set('km', e.target.value)} /></Field>
        {f.km !== '' && <div className="hl">{(+f.km).toLocaleString('en-IN')} km driven</div>}
        <div className="chips mt">{KQ.map(([v, l]) => <button key={v} className="chip" onClick={() => set('km', v)}>{l} km</button>)}</div>
        <Field label="Fuel mileage (kmpl)" hint="optional — as claimed by the seller"><input type="number" inputMode="decimal" step="0.5" placeholder="e.g. 14 (car) / 45 (bike)" value={f.kmpl} onChange={e => set('kmpl', e.target.value)} /></Field>
        <Field label="Owners"><div className="step"><button onClick={() => set('owners', Math.max(1, f.owners - 1))}>−</button><span>{f.owners}</span><button onClick={() => set('owners', Math.min(6, f.owners + 1))}>+</button></div></Field>
      </Card>
      <Card title="Price">
        <Field label="Asking price (₹)" hint="— what the seller is asking"><input className={err('price')} type="number" inputMode="numeric" step="1000" value={f.price} onChange={e => set('price', e.target.value)} /></Field>
        {+f.price > 0 && <div className="hl">{inr(+f.price)}</div>}
        <div className="chips mt">{PQ.map(([v, l]) => <button key={v} className="chip" onClick={() => set('price', v)}>{l}</button>)}</div>
        <Field label="New / ex-showroom price (₹)" hint="optional — for custom models"><input type="number" inputMode="numeric" step="1000" placeholder="e.g. 180000" value={f.np} onChange={e => set('np', e.target.value)} /></Field>
      </Card>
      <Card title="History">
        <Field label="Service history"><Chips opts={['Available', 'Partial', 'Not available', 'Unknown']} value={f.svc} onPick={v => set('svc', v)} /></Field>
        <Field label="Accident history"><Chips opts={['No', 'Yes', 'Unknown']} value={f.acc} onPick={v => set('acc', v)} /></Field>
      </Card>
      <Card title="Photos (optional, max 5)">
        <div className="photos">{previews.map((s, i) => <div className="ph" key={s}><img src={s} alt="" /><i onClick={() => setFiles(x => x.filter((_, j) => j !== i))}>×</i></div>)}
          {files.length < 5 && <div className="add" onClick={() => fileRef.current.click()}>＋</div>}</div>
        <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={e => { setFiles(x => [...x, ...e.target.files].slice(0, 5)); e.target.value = '' }} />
        <div className="hint">Clear photos of the bumpers, doors, headlights and tyres work best.</div>
      </Card>
      <button className="go" onClick={submit}>🔍 Analyze Vehicle</button>
    </div>)
}

function History({ open }) {
  const [h, setH] = useState(null)
  useEffect(() => { fetch('/api/history').then(r => r.json()).then(setH).catch(() => setH([])) }, [])
  const pick = async id => { const r = await (await fetch('/api/reports/' + id)).json(); open({ ...r, id }) }
  return (
    <Card title="Past analyses">{h === null ? <div className="mut">Loading…</div> : !h.length ? <div className="mut">No analyses yet.</div> :
      h.map(x => <div className="hi" key={x.id} onClick={() => pick(x.id)}><div><b>{x.vehicle}</b><div className="mut">{x.created.slice(0, 16).replace('T', ' ')}</div></div>
        <span className="tag" style={{ background: (BAND[x.label] || '#888') + '28', color: BAND[x.label] || '#888' }}>{x.score}/100</span></div>)}</Card>)
}

export default function App() {
  const [view, setView] = useState('new'), [res, setRes] = useState(null), [loading, setLoading] = useState(false), [toasts, setToasts] = useState([]), [prog, setProg] = useState(0), [theme, setTheme] = useState(localStorage.getItem('th') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light'))
  const toast = (m, t) => { const id = Math.random(); setToasts(x => [...x, { id, m, t }]); setTimeout(() => setToasts(x => x.filter(y => y.id !== id)), 3600) }
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('th', theme) }, [theme])
  useEffect(() => { const on = () => { const h = document.documentElement; setProg(scrollY / (h.scrollHeight - h.clientHeight || 1) * 100) }; addEventListener('scroll', on, { passive: true }); return () => removeEventListener('scroll', on) }, [])
  const go = v => { setView(v); setTimeout(() => scrollTo({ top: document.getElementById('app').offsetTop - 64, behavior: 'smooth' }), 30) }
  const done = r => { setRes(r); go('res') }
  const open = r => { setRes(r); go('res') }
  const NAV = [['new', '📝', 'Analyze'], ['res', '📊', 'Result'], ['his', '🕘', 'History']]
  return (
    <>
      <div id="sp" style={{ width: prog + '%' }} />
      <div className="toasts">{toasts.map(t => <div key={t.id} className={'toast ' + (t.t || '')}>{t.m}</div>)}</div>
      {loading && <Loader />}
      <header className="top"><div className="lg"><i>🚘</i>VehicleCheck</div><a className="lk" href="#how">How it works</a><a className="lk" href="#faq">FAQ</a>
        {NAV.map(([v, , l]) => <button key={v} className={'tl' + (view === v ? ' on' : '')} onClick={() => go(v)}>{l}</button>)}
        <button className="tl2" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} title="Theme">{theme === 'dark' ? '☀️' : '🌙'}</button><a className="cta" href="#app">Start free</a></header>
      <section className="hero"><div className="hi2">
        <Reveal><h1>Know the <u>truth</u> before you buy a used vehicle.</h1><p>Car, bike or scooter — risk score, fair price range, photo checks and smart questions for the seller, in about 30 seconds.</p>
          <a className="b b1" href="#app">🔍 Analyze a vehicle</a><a className="b b2" href="#how">How it works</a>
          <div className="pills"><span>⚡ 6 risk factors</span><span>📷 AI photo check</span><span>💰 Fair price range</span><span>🛣️ Odometer & ⛽ mileage</span></div></Reveal>
        <Reveal className="pv"><div className="mut center sm">SAMPLE REPORT</div><Gauge score={45} color="#eab308" /><div className="big center" style={{ color: '#eab308' }}>🟡 Moderate Risk</div><div className="mut center">Honda City 2020 · Asking slightly high</div></Reveal>
      </div></section>
      <main className="wrap" id="app">
        {view === 'new' && <div className="view"><Form onDone={done} toast={toast} setLoading={setLoading} /></div>}
        {view === 'res' && <div className="view">{res ? <Result r={res} toast={toast} /> : <Card className="center"><div style={{ fontSize: 42 }}>📊</div><b>No analysis yet</b><div className="mut">Analyze a vehicle first.</div></Card>}</div>}
        {view === 'his' && <div className="view"><History open={open} /></div>}
      </main>
      <section className="sec" id="how"><Reveal><h2>How it works</h2><div className="sb">3 simple steps</div></Reveal><div className="g3">
        {[['📝', '1. Enter the details', 'Type, model, year, kilometres driven, mileage, asking price and service/accident history.'], ['🤖', '2. AI analyzes it', 'Risk score, fair price range, odometer & mileage insights and visual signs from the photos.'], ['✅', '3. Decide with confidence', 'Negotiate using the seller questions and the inspection checklist.']].map(([i, t, d]) =>
          <Reveal key={t} className="card"><div className="n">{i}</div><b>{t}</b><p className="mut">{d}</p></Reveal>)}</div></section>
      <section className="sec narrow" id="faq"><Reveal><h2>FAQ</h2><div className="sb">Common questions</div></Reveal>
        {[['What is the asking price?', 'The price the seller is asking for. After bargaining, the final price is often lower.'], ['Where do I find the kilometres driven?', 'Enter the reading shown on the odometer / instrument cluster.'], ['Can this replace a mechanic inspection?', 'No. This is an AI-based estimate and photo notes are only "possible signs". Always get an independent mechanic inspection before buying.'], ['Can I enter a custom model?', 'Yes, type any model. For better accuracy, also enter its new/ex-showroom price.']].map(([q, a]) =>
          <Reveal key={q}><details><summary>{q}</summary><p>{a}</p></details></Reveal>)}</section>
      <footer>🚘 VehicleCheck · AI-powered used vehicle risk & value analyzer · Estimates are for guidance only.</footer>
      <nav className="nav">{NAV.map(([v, i, l]) => <button key={v} className={view === v ? 'on' : ''} onClick={() => go(v)}><span>{i}</span>{l}</button>)}</nav>
      <button id="bt" className={prog > 8 ? 'on' : ''} onClick={() => scrollTo({ top: 0, behavior: 'smooth' })} aria-label="Top">↑</button>
    </>)
}
