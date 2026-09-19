import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

const EMPTY = { ref_no: '', customer: '', brand: '', designer: '', season: '', category: '' }

export default function StylesList() {
  const [styles, setStyles] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY)

  async function load() {
    setStyles(await api.get('/styles'))
  }
  useEffect(() => { load() }, [])

  async function create() {
    if (!form.ref_no.trim()) return alert('要填 Ref No')
    try {
      await api.post('/styles', form)
      setShowForm(false)
      setForm(EMPTY)
      load()
    } catch (e) { alert(e.message) }
  }

  const statusBadge = (s) => (s === 'development' ? 'badge-blue' : s === 'production' ? 'badge-green' : 'badge-grey')

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>👟 鞋款</h1>
          <div className="sub">記錄每個開發款式（Style）</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>＋ 新鞋款</button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="form-grid">
            <div className="field"><label>Ref No *</label><input value={form.ref_no} onChange={e => setForm({ ...form, ref_no: e.target.value })} /></div>
            <div className="field"><label>客戶</label><input value={form.customer} onChange={e => setForm({ ...form, customer: e.target.value })} /></div>
            <div className="field"><label>品牌</label><input value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })} /></div>
            <div className="field"><label>設計師</label><input value={form.designer} onChange={e => setForm({ ...form, designer: e.target.value })} /></div>
            <div className="field"><label>季節</label><input value={form.season} onChange={e => setForm({ ...form, season: e.target.value })} /></div>
            <div className="field"><label>類別</label><input value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} /></div>
          </div>
          <button className="btn btn-primary" onClick={create}>建立</button>
        </div>
      )}

      <div className="list">
        {styles.map((s) => (
          <Link key={s.id} to={`/styles/${s.id}`} className="row-item">
            <div className="row-main">
              <div className="row-title">{s.ref_no}</div>
              <div className="row-sub">{[s.customer, s.brand, s.designer].filter(Boolean).join(' · ') || '—'}</div>
            </div>
            <span className={`badge ${statusBadge(s.status)}`}>{s.status || 'draft'}</span>
          </Link>
        ))}
        {styles.length === 0 && <div className="empty">未有鞋款，撳「＋ 新鞋款」開始</div>}
      </div>
    </div>
  )
}
