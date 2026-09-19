import { useEffect, useState } from 'react'
import { api } from '../api.js'
import MaterialPicker from './MaterialPicker.jsx'

const EMPTY = { material_id: '', component_id: '', quantity: '', unit: '', cpm: '', color: '' }

export default function BomEditor({ bom, onChanged }) {
  const [materials, setMaterials] = useState([])
  const [components, setComponents] = useState([])
  const [newItem, setNewItem] = useState(EMPTY)

  useEffect(() => {
    api.get('/materials').then(setMaterials)
    api.get('/components').then(setComponents)
  }, [])

  async function addItem() {
    if (!newItem.material_id) return alert('要揀物料')
    try {
      await api.post(`/boms/${bom.id}/items`, {
        material_id: Number(newItem.material_id),
        component_id: newItem.component_id ? Number(newItem.component_id) : null,
        quantity: newItem.quantity ? Number(newItem.quantity) : null,
        unit: newItem.unit || null,
        cpm: newItem.cpm ? Number(newItem.cpm) : null,
        color: newItem.color || null,
      })
      setNewItem(EMPTY)
      onChanged()
    } catch (e) { alert(e.message) }
  }

  async function removeItem(iid) {
    await api.del(`/bom-items/${iid}`)
    onChanged()
  }

  async function confirmBom() {
    await api.put(`/boms/${bom.id}/confirm`)
    onChanged()
  }

  const items = bom?.items || []
  const subtotal = (i) => (i.quantity != null && i.cpm != null ? i.quantity * i.cpm : null)
  const total = items.reduce((sum, i) => sum + (subtotal(i) || 0), 0)

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>📋 BOM（物料清單）</h3>
        {bom?.confirmed ? <span className="badge badge-green">已確認 ✓</span> : <span className="badge badge-grey">未確認</span>}
        <div className="spacer" />
        {!bom?.confirmed && <button className="btn btn-sm" onClick={confirmBom}>確認 BOM（閘口）</button>}
      </div>

      <table>
        <thead>
          <tr><th>部件</th><th>物料</th><th>數量</th><th>單位</th><th>單價(CPM)</th><th>小計</th><th>顏色</th><th></th></tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.id}>
              <td>{i.component?.name || '—'}</td>
              <td>
                <div>{i.material?.name}</div>
                <div className="muted">{i.material?.material_code}</div>
              </td>
              <td>{i.quantity ?? '—'}</td>
              <td>{i.unit || '—'}</td>
              <td>{i.cpm != null ? `$${i.cpm.toFixed(2)}` : '—'}</td>
              <td>{subtotal(i) != null ? `$${subtotal(i).toFixed(2)}` : '—'}</td>
              <td>{i.color || '—'}</td>
              <td><button className="btn btn-sm btn-danger" onClick={() => removeItem(i.id)}>刪</button></td>
            </tr>
          ))}
          {items.length === 0 && <tr><td colSpan={8} className="empty">未有物料，喺下面揀料加入</td></tr>}
        </tbody>
        {items.length > 0 && (
          <tfoot>
            <tr>
              <td colSpan={5} style={{ textAlign: 'right', fontWeight: 600 }}>BOM 總成本</td>
              <td style={{ fontWeight: 600 }}>${total.toFixed(2)}</td>
              <td colSpan={2}></td>
            </tr>
          </tfoot>
        )}
      </table>

      <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: 180 }}>
          <label>物料（從 master 揀）</label>
          <MaterialPicker materials={materials} value={newItem.material_id} onChange={(v) => setNewItem({ ...newItem, material_id: v })} />
        </div>
        <div style={{ minWidth: 130 }}>
          <label>部件</label>
          <select value={newItem.component_id} onChange={(e) => setNewItem({ ...newItem, component_id: e.target.value })}>
            <option value="">—</option>
            {components.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div style={{ width: 76 }}>
          <label>數量</label>
          <input value={newItem.quantity} onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })} />
        </div>
        <div style={{ width: 76 }}>
          <label>單位</label>
          <input value={newItem.unit} onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })} />
        </div>
        <div style={{ width: 90 }}>
          <label>單價(CPM)</label>
          <input value={newItem.cpm} placeholder="留空用 price" onChange={(e) => setNewItem({ ...newItem, cpm: e.target.value })} />
        </div>
        <div style={{ width: 90 }}>
          <label>顏色</label>
          <input value={newItem.color} onChange={(e) => setNewItem({ ...newItem, color: e.target.value })} />
        </div>
        <button className="btn btn-primary" onClick={addItem}>＋ 加物料</button>
      </div>
    </div>
  )
}
