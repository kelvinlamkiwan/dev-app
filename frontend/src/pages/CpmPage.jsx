import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

export default function CpmPage() {
  const [rows, setRows] = useState(null)
  useEffect(() => { api.get('/cpm').then(setRows) }, [])
  if (!rows) return <div className="page muted">loading…</div>

  return (
    <div className="page">
      <div className="page-head"><h1>🗓️ CPM 關鍵路徑</h1></div>
      <table>
        <thead>
          <tr><th>鞋款</th><th>客戶</th><th>總項</th><th>完成</th><th>遲到</th><th>逾期</th><th>Critical</th><th></th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.style_id}>
              <td style={{ fontWeight: 600 }}>{r.ref_no}</td>
              <td>{r.customer || '—'}</td>
              <td>{r.summary.total}</td>
              <td style={{ color: '#0a7d33' }}>{r.summary.done}</td>
              <td style={{ color: r.summary.delayed ? '#c62828' : '#888' }}>{r.summary.delayed}</td>
              <td style={{ color: r.summary.overdue ? '#c62828' : '#888' }}>{r.summary.overdue}</td>
              <td>
                {r.summary.critical > 0
                  ? <span className="badge" style={{ background: '#fdecea', color: '#c62828' }}>{r.summary.critical}</span>
                  : <span style={{ color: '#888' }}>—</span>}
              </td>
              <td><Link className="btn btn-sm" to={`/cpm/${r.style_id}`}>查看／編輯</Link></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={8} className="empty">未有鞋款</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
