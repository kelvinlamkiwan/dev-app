import { useState } from 'react'

export default function MaterialPicker({ materials, value, onChange }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)

  const selected = materials.find((m) => m.id === Number(value))
  const filtered = materials.filter(
    (m) =>
      !q ||
      m.name.toLowerCase().includes(q.toLowerCase()) ||
      m.material_code.toLowerCase().includes(q.toLowerCase()) ||
      (m.color || '').toLowerCase().includes(q.toLowerCase()),
  )

  return (
    <div className="dropdown">
      <input
        value={selected ? `${selected.material_code} — ${selected.name}` : q}
        placeholder="搜尋物料…"
        onFocus={() => setOpen(true)}
        onChange={(e) => { setQ(e.target.value); setOpen(true) }}
      />
      {open && (
        <div className="dropdown-menu">
          {filtered.map((m) => (
            <button key={m.id} onClick={() => { onChange(m.id); setOpen(false); setQ('') }}>
              <b>{m.material_code}</b> — {m.name} <span className="muted">({m.color || '—'})</span>
            </button>
          ))}
          {filtered.length === 0 && <div className="muted" style={{ padding: 8 }}>冇 match</div>}
        </div>
      )}
    </div>
  )
}
