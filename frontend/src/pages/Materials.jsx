import { useEffect, useState } from 'react'
import { api } from '../api.js'

const FIELDS = [
  ['material_code', '物料編號 *'], ['name', '名稱 *'], ['type', '類型'],
  ['color', '顏色'], ['color_code', '色碼'], ['supplier', '供應商'],
  ['supplier_ref', '供應商 ref'], ['unit', '單位'], ['price', '單價'],
  ['min_order', '最小訂量'],
]

const EMPTY = { material_code: '', name: '' }

export default function Materials() {
  const [materials, setMaterials] = useState([])
  const [q, setQ] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(EMPTY)

  async function load() {
    setMaterials(await api.get('/materials' + (q ? `?q=${encodeURIComponent(q)}` : '')))
  }
  useEffect(() => { load() }, [q])

  async function create() {
    if (!form.material_code.trim() || !form.name.trim()) return alert('要填編號 + 名稱')
    try {
      await api.post('/materials', form)
      setForm(EMPTY)
      setShowForm(false)
      load()
    } catch (e) { alert(e.message) }
  }

  async function remove(m) {
    if (!confirm(`刪除物料「${m.name}」？`)) return
    await api.del(`/materials/${m.id}`)
    load()
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>🧵 物料主檔</h1>
          <div className="sub">Master Material Data —— 喺 BOM 揀料時重用</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>＋ 新物料</button>
      </div>

      <input placeholder="搜尋名稱 / 編號 / 供應商 / 顏色…" value={q} onChange={(e) => setQ(e.target.value)} style={{ marginBottom: 12 }} />

      {showForm && (
        <div className="card" style={{ marginBottom: 12 }}>
          <div className="form-grid">
            {FIELDS.map(([k, label]) => (
              <div className="field" key={k}><label>{label}</label><input value={form[k] || ''} onChange={(e) => setForm({ ...form, [k]: e.target.value })} /></div>
            ))}
          </div>
          <button className="btn btn-primary" onClick={create}>建立</button>
        </div>
      )}

      <div className="card">
        <table>
          <thead>
            <tr><th>編號</th><th>名稱</th><th>類型</th><th>顏色</th><th>供應商</th><th>單位</th><th>單價</th><th></th></tr>
          </thead>
          <tbody>
            {materials.map((m) => (
              <tr key={m.id}>
                <td><b>{m.material_code}</b></td>
                <td>{m.name}</td>
                <td>{m.type || '—'}</td>
                <td>{m.color || '—'}</td>
                <td>{m.supplier || '—'}</td>
                <td>{m.unit || '—'}</td>
                <td>{m.price ?? '—'}</td>
                <td><button className="btn btn-sm btn-danger" onClick={() => remove(m)}>刪</button></td>
              </tr>
            ))}
            {materials.length === 0 && <tr><td colSpan={8} className="empty">未有物料</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
