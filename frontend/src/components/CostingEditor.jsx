import { useEffect, useState } from 'react'
import { api } from '../api.js'

const FIELDS = ['labor', 'overhead_pct', 'margin_pct', 'freight', 'mold_cost', 'order_qty', 'target_price', 'currency']

export default function CostingEditor({ sample }) {
  const [costing, setCosting] = useState(null)
  const [form, setForm] = useState({})

  useEffect(() => {
    if (!sample) return
    api.get(`/samples/${sample.id}/costing`).then((c) => {
      setCosting(c)
      setForm({
        labor: c.labor ?? '',
        overhead_pct: c.overhead_pct ?? '',
        margin_pct: c.margin_pct ?? '',
        freight: c.freight ?? '',
        mold_cost: c.mold_cost ?? '',
        order_qty: c.order_qty ?? '',
        target_price: c.target_price ?? '',
        currency: c.currency || 'USD',
      })
    })
  }, [sample?.id])

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function save() {
    const payload = {}
    for (const k of FIELDS) {
      const v = form[k]
      if (k === 'currency') payload[k] = v || 'USD'
      else if (k === 'target_price') payload[k] = v === '' ? null : Number(v)
      else if (k === 'order_qty') payload[k] = v === '' ? 0 : Number(v)
      else payload[k] = v === '' ? 0 : Number(v)
    }
    try {
      const c = await api.put(`/samples/${sample.id}/costing`, payload)
      setCosting(c)
    } catch (e) { alert(e.message) }
  }

  if (!costing) return <div className="card muted">載入成本表…</div>
  const c = costing.computed || {}
  const cur = c.currency || 'USD'
  const fmt = (n) => (n == null ? '—' : `${cur} ${Number(n).toFixed(2)}`)
  const pct = (n) => (n == null ? '—' : `${Number(n).toFixed(1)}%`)

  const variance = c.variance
  const varianceColor = variance == null ? 'muted' : variance >= 0 ? '#0a7d33' : '#c62828'

  const rows = [
    ['材料成本 Materials（由 BOM 自動計）', fmt(c.materials)],
    ['加工費 Labor / CM', fmt(c.labor)],
    ['間接成本 Overhead', `${fmt(c.overhead)} (${pct(c.overhead_pct)})`],
    ['模具攤銷 Mold / pair', fmt(c.mold_per_pair)],
    ['運費 Freight', fmt(c.freight)],
  ]

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>💰 成本表 Costing</h3>
        <div className="spacer" />
        <button className="btn btn-primary btn-sm" onClick={save}>儲存成本表</button>
      </div>

      <div className="row-sub" style={{ marginBottom: 12 }}>
        材料成本會由 {sample?.stage || '本階段'} BOM 嘅（數量 × 單價）自動加總，下面輸入其餘成本項。
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
        <div>
          <label>加工費 Labor/CM</label>
          <input type="number" step="0.01" value={form.labor} onChange={set('labor')} placeholder="0.00" />
        </div>
        <div>
          <label>間接成本 Overhead %</label>
          <input type="number" step="0.1" value={form.overhead_pct} onChange={set('overhead_pct')} placeholder="0" />
        </div>
        <div>
          <label>利潤 Margin %</label>
          <input type="number" step="0.1" value={form.margin_pct} onChange={set('margin_pct')} placeholder="0" />
        </div>
        <div>
          <label>運費 Freight / pair</label>
          <input type="number" step="0.01" value={form.freight} onChange={set('freight')} placeholder="0.00" />
        </div>
        <div>
          <label>模具費 Mold（總額）</label>
          <input type="number" step="0.01" value={form.mold_cost} onChange={set('mold_cost')} placeholder="0" />
        </div>
        <div>
          <label>訂單量 Order Qty</label>
          <input type="number" step="1" value={form.order_qty} onChange={set('order_qty')} placeholder="0" />
        </div>
        <div>
          <label>目標售價 Target</label>
          <input type="number" step="0.01" value={form.target_price} onChange={set('target_price')} placeholder="留空" />
        </div>
        <div>
          <label>幣別 Currency</label>
          <input value={form.currency} onChange={set('currency')} placeholder="USD" style={{ textTransform: 'uppercase' }} />
        </div>
      </div>

      <table style={{ marginTop: 16 }}>
        <tbody>
          {rows.map(([label, val]) => (
            <tr key={label}>
              <td style={{ color: '#555' }}>{label}</td>
              <td style={{ textAlign: 'right', fontWeight: 500 }}>{val}</td>
            </tr>
          ))}
          <tr style={{ borderTop: '2px solid #ddd' }}>
            <td style={{ fontWeight: 700 }}>總成本 Total Cost</td>
            <td style={{ textAlign: 'right', fontWeight: 700 }}>{fmt(c.total_cost)}</td>
          </tr>
          <tr>
            <td style={{ color: '#555' }}>利潤 Margin（{pct(c.margin_pct)}）</td>
            <td style={{ textAlign: 'right' }}>{fmt(c.margin)}</td>
          </tr>
          <tr style={{ borderTop: '2px solid #ddd' }}>
            <td style={{ fontWeight: 700 }}>FOB 報價 FOB Price</td>
            <td style={{ textAlign: 'right', fontWeight: 700, fontSize: '1.1em' }}>{fmt(c.fob_price)}</td>
          </tr>
          {c.target_price != null && (
            <tr>
              <td style={{ color: '#555' }}>目標價 Target · 差異</td>
              <td style={{ textAlign: 'right', fontWeight: 600, color: varianceColor }}>
                {fmt(c.target_price)} · {variance >= 0 ? '+' : ''}{Number(variance).toFixed(2)}
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
