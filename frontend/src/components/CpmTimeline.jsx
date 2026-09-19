import { useEffect, useState } from 'react'
import { api } from '../api.js'

const STATUS = {
  delayed: { text: '遲到', color: '#c62828', bg: '#fdecea' },
  overdue: { text: '逾期', color: '#c62828', bg: '#fdecea' },
  done: { text: '完成', color: '#0a7d33', bg: '#e6f4ea' },
  scheduled: { text: '計劃中', color: '#1a56db', bg: '#e8f0fe' },
  not_started: { text: '未設日期', color: '#888', bg: '#f2f2f2' },
}

const MANUAL_STATUS = ['not started', 'in progress', 'done', 'on hold']

function timeAgo(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const m = Math.floor((Date.now() - d.getTime()) / 60000)
  if (m < 1) return '啱啱'
  if (m < 60) return `${m} 分鐘前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小時前`
  return `${Math.floor(h / 24)} 日前`
}

export default function CpmTimeline({ styleId }) {
  const [cpm, setCpm] = useState(null)
  const [newName, setNewName] = useState('')

  async function load() {
    const c = await api.get(`/styles/${styleId}/cpm`)
    setCpm(c)
  }
  useEffect(() => { if (styleId) load() }, [styleId])

  async function saveDate(kind, id, which, value) {
    if (kind === 'sample') {
      const field = which === 'planned' ? 'requested_date' : 'received_date'
      await api.put(`/samples/${id}`, { [field]: value || null })
    } else {
      const field = which === 'planned' ? 'planned_date' : 'actual_date'
      await api.put(`/milestones/${id}`, { [field]: value || null })
    }
    load()
  }

  async function saveStatus(kind, id, value) {
    if (kind === 'sample') {
      await api.put(`/samples/${id}`, { status: value || null })
    } else {
      await api.put(`/milestones/${id}`, { status: value || null })
    }
    load()
  }

  async function addMilestone() {
    if (!newName.trim()) return alert('要入里程碑名')
    try {
      await api.post(`/styles/${styleId}/milestones`, { name: newName.trim() })
      setNewName('')
      load()
    } catch (e) { alert(e.message) }
  }

  async function removeMilestone(mid) {
    await api.del(`/milestones/${mid}`)
    load()
  }

  async function importExcel(e) {
    const file = e.target.files[0]
    if (!file) return
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.upload('/cpm/import', fd)
      alert(`匯入完成：${res.rows} 行 · 新增 ${res.styles_created} 款 / 更新 ${res.styles_updated} 款 · sample ${res.samples_created} 新增 / ${res.samples_updated} 更新`)
      load()
    } catch (err) { alert(err.message) }
    e.target.value = ''
  }

  if (!cpm) return <div className="card muted">載入 CPM…</div>

  const statusBadge = (item) => {
    const st = STATUS[item.status] || STATUS.not_started
    return <span style={{ color: st.color, background: st.bg, padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}>{st.text}</span>
  }

  const statusSelect = (item) => (
    <select value={item.manual_status || ''} onChange={(e) => saveStatus(item.kind, item.id, e.target.value)} style={{ width: 'auto', fontSize: 13 }}>
      <option value="">—</option>
      {MANUAL_STATUS.map((o) => <option key={o} value={o}>{o}</option>)}
      {item.manual_status && !MANUAL_STATUS.includes(item.manual_status) && <option value={item.manual_status}>{item.manual_status}</option>}
    </select>
  )

  const changedAt = (item) => (
    item.status_changed_at ? <div className="muted" style={{ fontSize: 11 }}>{timeAgo(item.status_changed_at)}</div> : null
  )

  const renderSampleRow = (item) => (
    <tr key={`${item.kind}-${item.id}`}>
      <td>
        <div>{item.name}</div>
        {item.critical && <span style={{ fontSize: 11, color: '#c62828', fontWeight: 600 }}>⚠ critical</span>}
      </td>
      <td>{statusSelect(item)}{changedAt(item)}</td>
      <td><input type="date" value={item.planned || ''} onChange={(e) => saveDate(item.kind, item.id, 'planned', e.target.value)} /></td>
      <td><input type="date" value={item.actual || ''} onChange={(e) => saveDate(item.kind, item.id, 'actual', e.target.value)} /></td>
      <td>{statusBadge(item)}</td>
      <td style={{ textAlign: 'right', color: item.delay_days > 0 ? '#c62828' : '#888', fontWeight: item.delay_days > 0 ? 600 : 400 }}>
        {item.delay_days > 0 ? `+${item.delay_days} 日` : '—'}
      </td>
    </tr>
  )

  const s = cpm.summary || {}

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0 }}>🗓️ CPM 關鍵路徑 Critical Path</h3>
        <span className="badge badge-grey">共 {s.total} 項</span>
        <span className="badge badge-green">完成 {s.done}</span>
        <span className="badge" style={{ background: '#fdecea', color: '#c62828' }}>遲到 {s.delayed} · 逾期 {s.overdue}</span>
        <div className="spacer" />
        <label className="btn btn-sm" style={{ cursor: 'pointer' }}>
          📥 匯入 Excel
          <input type="file" accept=".xlsx" onChange={importExcel} style={{ display: 'none' }} />
        </label>
      </div>

      <div className="row-sub" style={{ marginBottom: 10 }}>
        改「手動狀態」做 done 會自動記錄完成時間並填「實際」日期；「計劃」= requested／planned，「實際」= received／actual。
      </div>

      <h4 style={{ margin: '14px 0 6px' }}>Sample 階段時間線</h4>
      <table>
        <thead><tr><th>階段</th><th>手動狀態</th><th>計劃日期</th><th>實際日期</th><th>狀態</th><th>Delay</th></tr></thead>
        <tbody>
          {cpm.sample_timeline.map(renderSampleRow)}
          {cpm.sample_timeline.length === 0 && <tr><td colSpan={6} className="empty">未有樣本階段</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: '14px 0 6px' }}>里程碑 Milestones</h4>
      <table>
        <thead><tr><th>里程碑</th><th>手動狀態</th><th>計劃日期</th><th>實際日期</th><th>狀態</th><th>Delay</th><th></th></tr></thead>
        <tbody>
          {cpm.milestones.map((m) => (
            <tr key={`m-${m.id}`}>
              <td>
                <div>{m.name}</div>
                {m.critical && <span style={{ fontSize: 11, color: '#c62828', fontWeight: 600 }}>⚠ critical</span>}
              </td>
              <td>{statusSelect(m)}{changedAt(m)}</td>
              <td><input type="date" value={m.planned || ''} onChange={(e) => saveDate('milestone', m.id, 'planned', e.target.value)} /></td>
              <td><input type="date" value={m.actual || ''} onChange={(e) => saveDate('milestone', m.id, 'actual', e.target.value)} /></td>
              <td>{statusBadge(m)}</td>
              <td style={{ textAlign: 'right', color: m.delay_days > 0 ? '#c62828' : '#888', fontWeight: m.delay_days > 0 ? 600 : 400 }}>
                {m.delay_days > 0 ? `+${m.delay_days} 日` : '—'}
              </td>
              <td><button className="btn btn-sm btn-danger" onClick={() => removeMilestone(m.id)}>刪</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input style={{ flex: 1, maxWidth: 320 }} value={newName} placeholder="新里程碑名（例：船期確認）" onChange={(e) => setNewName(e.target.value)} />
        <button className="btn btn-primary btn-sm" onClick={addMilestone}>＋ 加里程碑</button>
      </div>
    </div>
  )
}
