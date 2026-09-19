import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

const statusBadge = (s) => (s === 'development' ? 'badge-blue' : s === 'production' ? 'badge-green' : 'badge-grey')

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => { api.get('/stats').then(setStats) }, [])

  if (!stats) return <div className="page"><div className="empty">載入中…</div></div>

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>📊 Dashboard</h1>
          <div className="sub">開發進度一覽</div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-num">{stats.styles_total}</div>
          <div className="stat-label">鞋款</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{stats.samples_total}</div>
          <div className="stat-label">樣本</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{stats.materials_total}</div>
          <div className="stat-label">物料</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">{stats.components_total}</div>
          <div className="stat-label">部件</div>
        </div>
        <div className="stat-card stat-card-accent">
          <div className="stat-num">{stats.boms_confirmed}<span className="stat-sub"> / {stats.boms_total}</span></div>
          <div className="stat-label">已確認 BOM</div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3 style={{ marginTop: 0, marginBottom: 8 }}>鞋款狀態</h3>
        {Object.keys(stats.styles_by_status).length === 0 ? (
          <div className="muted">未有鞋款</div>
        ) : (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {Object.entries(stats.styles_by_status).map(([s, n]) => (
              <span key={s} className={`badge ${statusBadge(s)}`}>{s} · {n}</span>
            ))}
          </div>
        )}
      </div>

      <div className="page-head" style={{ marginTop: 20, marginBottom: 10 }}>
        <h2 style={{ margin: 0, fontSize: '1.1rem' }}>最近鞋款</h2>
        <Link to="/styles" className="btn btn-sm">全部 →</Link>
      </div>
      <div className="list">
        {stats.recent_styles.map((s) => (
          <Link key={s.id} to={`/styles/${s.id}`} className="row-item">
            <div className="row-main">
              <div className="row-title">{s.ref_no}</div>
              <div className="row-sub">{[s.customer, s.brand].filter(Boolean).join(' · ') || '—'}</div>
            </div>
            <span className={`badge ${statusBadge(s.status)}`}>{s.status || 'draft'}</span>
          </Link>
        ))}
        {stats.recent_styles.length === 0 && <div className="empty">未有鞋款</div>}
      </div>
    </div>
  )
}
