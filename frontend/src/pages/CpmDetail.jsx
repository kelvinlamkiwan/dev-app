import { Link, useParams } from 'react-router-dom'
import CpmTimeline from '../components/CpmTimeline.jsx'

export default function CpmDetail() {
  const { id } = useParams()
  return (
    <div className="page">
      <Link to="/cpm" className="muted">← 返去 CPM 列表</Link>
      <CpmTimeline styleId={Number(id)} />
    </div>
  )
}
