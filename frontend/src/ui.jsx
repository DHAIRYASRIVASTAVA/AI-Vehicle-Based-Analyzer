import { useEffect, useRef, useState } from 'react'
export const inr = x => '₹' + Math.round(x).toLocaleString('en-IN')
export const num = x => Math.round(x).toLocaleString('en-IN')
export const col = r => (r < 0.34 ? '#22c55e' : r < 0.67 ? '#f59e0b' : '#ef4444')

export function useReveal() {
  const ref = useRef(null)
  useEffect(() => {
    const io = new IntersectionObserver(es => es.forEach(e => e.isIntersecting && (e.target.classList.add('in'), io.unobserve(e.target))), { threshold: 0.12 })
    ref.current && io.observe(ref.current)
    return () => io.disconnect()
  }, [])
  return ref
}
export const Reveal = ({ children, className = '', ...p }) => <div ref={useReveal()} className={'rv ' + className} {...p}>{children}</div>
export const Card = ({ title, accent, className = '', children }) => (
  <section className={'card ' + className} style={accent ? { borderColor: accent + '66' } : null}>
    {title && <h3>{title}</h3>}{children}
  </section>)

export function Bar({ value, color }) {           // animated progress bar (value 0-100)
  const [w, setW] = useState(0)
  useEffect(() => { const t = setTimeout(() => setW(value), 60); return () => clearTimeout(t) }, [value])
  return <div className="fb"><i style={{ width: w + '%', background: color }} /></div>
}
export function Gauge({ score, color }) {         // animated semicircle gauge + count-up
  const [s, setS] = useState(0), [n, setN] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setS(score), 60)
    let c = 0; const iv = setInterval(() => { c = Math.min(score, c + Math.max(1, Math.round(score / 30))); setN(c); if (c >= score) clearInterval(iv) }, 35)
    return () => { clearTimeout(t); clearInterval(iv) }
  }, [score])
  return (
    <svg className="gauge" viewBox="0 0 200 120">
      <path d="M20 100A80 80 0 0 1 180 100" fill="none" stroke="var(--bd)" strokeWidth="16" strokeLinecap="round" />
      <path d="M20 100A80 80 0 0 1 180 100" fill="none" stroke={color} strokeWidth="16" strokeLinecap="round" strokeDasharray={`${(251.3 * s) / 100} 251.3`} style={{ transition: 'stroke-dasharray 1.3s cubic-bezier(.2,.8,.2,1)' }} />
      <text x="100" y="94" textAnchor="middle" fontSize="40" fontWeight="800" fill="currentColor">{n}</text>
      <text x="100" y="114" textAnchor="middle" fontSize="12" fill="var(--mut)">out of 100</text>
    </svg>)
}
