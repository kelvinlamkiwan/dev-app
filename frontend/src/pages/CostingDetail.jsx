import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import CostingEditor from '../components/CostingEditor.jsx'

export default function CostingDetail() {
  const { id } = useParams()
  const [style, setStyle] = useState(null)
  useEffect(() => { api.get(`/styles/${id}`).then(setStyle) }, [id])

  if (!style) return <div className="page muted">loading…</div>

  return (
    <div className="page">
      <Link to="/costing" className="muted">← 返去成本表列表</Link>
      <div className="page-head">
        <h1>{style.ref_no}</h1>
        <div className="sub">{[style.customer, style.brand, style.designer].filter(Boolean).join(' · ')}</div>
      </div>

      {style.samples.length === 0 && <div className="empty">未有樣本階段</div>}
      {style.samples.map((s) => <CostingEditor key={s.id} sample={s} />)}
    </div>
  )
}
