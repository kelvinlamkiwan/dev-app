import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

const fmt = (n) => (n == null ? '—' : `$${Number(n).toFixed(2)}`)

export default function CostingPage() {
  const [rows, setRows] = useState(null)
  useEffect(() => { api.get('/costing').then(setRows) }, [])
  if (!rows) return <div className="page muted">loading…</div>

  return (
    <div className="page">
      <div className="page-head"><h1>💰 成本表 Costing</h1></div>
      <table>
        <thead>
          <tr><th>鞋款</th><th>客戶</th><th>階段</th><th>材料成本</th><th>FOB 報價</th><th>目標價</th><th>差異</th><th></th></tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            if (r.samples.length === 0) {
              return (
                <tr key={`${r.style_id}-empty`}>
                  <td style={{ fontWeight: 600 }}>{r.ref_no}</td>
                  <td>{r.customer || '—'}</td>
                  <td colSpan={4} className="empty">未有樣本階段</td>
                  <td><Link className="btn btn-sm" to={`/costing/${r.style_id}`}>查看／編輯</Link></td>
                </tr>
              )
            }
            return r.samples.map((s, i) => (
              <tr key={s.sample_id}>
                {i === 0 && <td rowSpan={r.samples.length} style={{ fontWeight: 600 }}>{r.ref_no}</td>}
                {i === 0 && <td rowSpan={r.samples.length}>{r.customer || '—'}</td>}
                <td>{s.stage}</td>
                <td>{fmt(s.materials)}</td>
                <td style={{ fontWeight: 600 }}>{fmt(s.fob_price)}</td>
                <td>{fmt(s.target_price)}</td>
                <td style={{ color: s.variance != null ? (s.variance >= 0 ? '#0a7d33' : '#c62828') : '#888', fontWeight: 600 }}>
                  {s.variance != null ? `${s.variance >= 0 ? '+' : ''}${s.variance.toFixed(2)}` : '—'}
                </td>
                {i === 0 && <td rowSpan={r.samples.length}><Link className="btn btn-sm" to={`/costing/${r.style_id}`}>查看／編輯</Link></td>}
              </tr>
            ))
          })}
          {rows.length === 0 && <tr><td colSpan={8} className="empty">未有鞋款</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
