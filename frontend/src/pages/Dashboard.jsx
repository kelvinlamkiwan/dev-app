import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'

const statusBadge = (s) => (s === 'development' ? 'badge-blue' : s === 'production' ? 'badge-green' : 'badge-grey')

const ENTITY_ICON = { sample: '📦', milestone: '🎯', style: '👟', bom: '📋' }

function timeAgo(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const m = Math.floor((Date.now() - d.getTime()) / 60000)
  if (m < 1) return '啱啱'
  if (m < 60) return `${m} 分鐘前`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h} 小時前`
  const days = Math.floor(h / 24)
  return `${days} 日前`
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => { api.get('/stats').then(setStats) }, [])

  if (!stats) return <div className="page"><div className="empty">載入中…</div></div>

  const cpm = stats.cpm || {}

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
        <div className="stat-card stat-card-accent">
          <div className="stat-num">{stats.boms_confirmed}<span className="stat-sub"> / {stats.boms_total}</span></div>
          <div className="stat-label">已確認 BOM</div>
        </div>
      </div>

      <div className="stats-grid" style={{ marginTop: 12 }}>
        <Link to="/cpm" className="stat-card" style={{ borderLeft: '3px solid #c62828' }}>
          <div className="stat-num" style={{ color: '#c62828' }}>{cpm.critical}</div>
          <div className="stat-label">⚠ Critical（關鍵路徑爆）</div>
        </Link>
        <Link to="/cpm" className="stat-card" style={{ borderLeft: '3px solid #e65100' }}>
          <div className="stat-num" style={{ color: '#e65100' }}>{cpm.delayed}</div>
          <div className="stat-label">遲到</div>
        </Link>
        <Link to="/cpm" className="stat-card" style={{ borderLeft: '3px solid #b71c1c' }}>
          <div className="stat-num" style={{ color: '#b71c1c' }}>{cpm.overdue}</div>
          <div className="stat-label">逾期</div>
        </Link>
        <Link to="/costing" className="stat-card" style={{ borderLeft: '3px solid #c62828' }}>
          <div className="stat-num" style={{ color: '#c62828' }}>{stats.costing_over_target}</div>
          <div className="stat-label">成本超標</div>
        </Link>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
          <h3 style={{ margin: 0 }}>🕐 最近動態</h3>
          <div className="spacer" />
          <Link to="/activity" className="muted" style={{ fontSize: 13 }}>全部 →</Link>
        </div>
        {(stats.recent_activity || []).length === 0 ? (
          <div className="muted">未有狀態變更</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {stats.recent_activity.map((a, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
                <span>{ENTITY_ICON[a.entity_type] || '•'}</span>
                <span style={{ fontWeight: 600 }}>{a.ref_no || '—'}</span>
                <span className="muted">{a.entity_type}</span>
                <span style={{ background: '#f0f0f0', padding: '1px 8px', borderRadius: 10, fontSize: 12 }}>
                  {a.old_value || '—'} → {a.new_value || '—'}
                </span>
                <span className="muted" style={{ marginLeft: 'auto', fontSize: 12 }}>{timeAgo(a.changed_at)}</span>
              </div>
            ))}
          </div>
        )}
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
