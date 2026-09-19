import { useEffect, useState } from 'react'
import { api } from '../api.js'

const ENTITY_ICON = { sample: '📦', milestone: '🎯', style: '👟', bom: '📋' }

export default function ActivityPage() {
  const [logs, setLogs] = useState(null)
  useEffect(() => { api.get('/activity?limit=200').then(setLogs) }, [])

  if (!logs) return <div className="page muted">loading…</div>

  return (
    <div className="page">
      <div className="page-head"><h1>🕐 動態紀錄</h1></div>
      <table>
        <thead>
          <tr><th>時間</th><th>類型</th><th>鞋款</th><th>欄位</th><th>變更</th></tr>
        </thead>
        <tbody>
          {logs.map((l) => (
            <tr key={l.id}>
              <td className="muted" style={{ whiteSpace: 'nowrap' }}>{l.changed_at ? new Date(l.changed_at).toLocaleString('zh-HK') : '—'}</td>
              <td>{ENTITY_ICON[l.entity_type] || '•'} {l.entity_type}</td>
              <td style={{ fontWeight: 600 }}>{l.ref_no || '—'}</td>
              <td>{l.field}</td>
              <td>{l.old_value || '—'} → {l.new_value || '—'}</td>
            </tr>
          ))}
          {logs.length === 0 && <tr><td colSpan={5} className="empty">未有紀錄</td></tr>}
        </tbody>
      </table>
    </div>
  )
}
