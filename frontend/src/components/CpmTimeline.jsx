import { useEffect, useState } from 'react'
import { api } from '../api.js'

const STATUS = {
  delayed: { text: '遲到', color: '#c62828', bg: '#fdecea' },
  overdue: { text: '逾期', color: '#c62828', bg: '#fdecea' },
  done: { text: '完成', color: '#0a7d33', bg: '#e6f4ea' },
  scheduled: { text: '計劃中', color: '#1a56db', bg: '#e8f0fe' },
  not_started: { text: '未設日期', color: '#888', bg: '#f2f2f2' },
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

  const renderRow = (item) => {
    const st = STATUS[item.status] || STATUS.not_started
    return (
      <tr key={`${item.kind}-${item.id}`}>
        <td>
          <div>{item.name}</div>
          {item.critical && <span style={{ fontSize: 11, color: '#c62828', fontWeight: 600 }}>⚠ critical</span>}
        </td>
        <td><input type="date" value={item.planned || ''} onChange={(e) => saveDate(item.kind, item.id, 'planned', e.target.value)} /></td>
        <td><input type="date" value={item.actual || ''} onChange={(e) => saveDate(item.kind, item.id, 'actual', e.target.value)} /></td>
        <td><span style={{ color: st.color, background: st.bg, padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600 }}>{st.text}</span></td>
        <td style={{ textAlign: 'right', color: item.delay_days > 0 ? '#c62828' : '#888', fontWeight: item.delay_days > 0 ? 600 : 400 }}>
          {item.delay_days > 0 ? `+${item.delay_days} 日` : '—'}
        </td>
      </tr>
    )
  }

  const s = cpm.summary || {}

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0 }}>🗓️ CPM 關鍵路徑 Critical Path</h3>
        <div className="spacer" />
        <span className="badge badge-grey">共 {s.total} 項</span>
        <span className="badge badge-green">完成 {s.done}</span>
        <span className="badge" style={{ background: '#fdecea', color: '#c62828' }}>遲到 {s.delayed} · 逾期 {s.overdue}</span>
        <label className="btn btn-sm" style={{ cursor: 'pointer', marginLeft: 'auto' }}>
          📥 匯入 Excel
          <input type="file" accept=".xlsx" onChange={importExcel} style={{ display: 'none' }} />
        </label>
      </div>

      <div className="row-sub" style={{ marginBottom: 10 }}>
        「計劃」係 requested／planned 日期，「實際」係 received／actual 日期。遲到或逾期嘅會標做 critical，影響出貨。
      </div>

      <h4 style={{ margin: '14px 0 6px' }}>Sample 階段時間線</h4>
      <table>
        <thead><tr><th>階段</th><th>計劃日期</th><th>實際日期</th><th>狀態</th><th>Delay</th></tr></thead>
        <tbody>
          {cpm.sample_timeline.map(renderRow)}
          {cpm.sample_timeline.length === 0 && <tr><td colSpan={5} className="empty">未有樣本階段</td></tr>}
        </tbody>
      </table>

      <h4 style={{ margin: '14px 0 6px' }}>里程碑 Milestones</h4>
      <table>
        <thead><tr><th>里程碑</th><th>計劃日期</th><th>實際日期</th><th>狀態</th><th>Delay</th><th></th></tr></thead>
        <tbody>
          {cpm.milestones.map((m) => (
            <tr key={`m-${m.id}`}>
              <td>
                <div>{m.name}</div>
                {m.critical && <span style={{ fontSize: 11, color: '#c62828', fontWeight: 600 }}>⚠ critical</span>}
              </td>
              <td><input type="date" value={m.planned || ''} onChange={(e) => saveDate('milestone', m.id, 'planned', e.target.value)} /></td>
              <td><input type="date" value={m.actual || ''} onChange={(e) => saveDate('milestone', m.id, 'actual', e.target.value)} /></td>
              <td>
                <span style={{ color: (STATUS[m.status] || STATUS.not_started).color, background: (STATUS[m.status] || STATUS.not_started).bg, padding: '2px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600 }}>
                  {(STATUS[m.status] || STATUS.not_started).text}
                </span>
              </td>
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
