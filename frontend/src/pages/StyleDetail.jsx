import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import BomEditor from '../components/BomEditor.jsx'

const STAGES = ['development', 'confirmation', 'salesman', 'production', 'photo']

export default function StyleDetail() {
  const { id } = useParams()
  const [style, setStyle] = useState(null)
  const [activeSample, setActiveSample] = useState(null)
  const [newStage, setNewStage] = useState('development')
  const [pdfResult, setPdfResult] = useState(null)
  const [parsing, setParsing] = useState(false)

  async function load() {
    const s = await api.get(`/styles/${id}`)
    setStyle(s)
    setActiveSample((prev) => (prev && s.samples.some((x) => x.id === prev) ? prev : (s.samples[0]?.id || null)))
  }
  useEffect(() => { load() }, [id])

  async function addSample() {
    try {
      const sample = await api.post(`/styles/${id}/samples`, { stage: newStage })
      await load()
      setActiveSample(sample.id)
    } catch (e) { alert(e.message) }
  }

  async function uploadPdf(e) {
    const file = e.target.files[0]
    if (!file) return
    setParsing(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.upload(`/styles/${id}/spec-sheets`, fd)
      setPdfResult(res.parsed)
    } catch (err) { alert(err.message) } finally { setParsing(false) }
  }

  if (!style) return <div className="page muted">loading…</div>

  const sample = style.samples.find((s) => s.id === activeSample) || style.samples[0]
  const usedStages = new Set(style.samples.map((s) => s.stage))

  return (
    <div className="page">
      <Link to="/" className="muted">← 返去鞋款列表</Link>
      <div className="page-head">
        <div>
          <h1>{style.ref_no}</h1>
          <div className="sub">{[style.customer, style.brand, style.designer].filter(Boolean).join(' · ')}</div>
        </div>
        <span className="badge badge-blue">{style.status || 'draft'}</span>
      </div>

      <div className="tabs">
        {style.samples.map((s) => (
          <div key={s.id} className={`tab ${s.id === sample?.id ? 'active' : ''}`} onClick={() => setActiveSample(s.id)}>
            {s.stage}
            {s.bom?.confirmed && ' ✓'}
          </div>
        ))}
        <div style={{ display: 'flex', gap: 6 }}>
          <select value={newStage} onChange={(e) => setNewStage(e.target.value)} style={{ width: 'auto' }}>
            {STAGES.filter((s) => !usedStages.has(s)).map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <button className="btn btn-sm" onClick={addSample}>＋ 加階段</button>
        </div>
      </div>

      {sample ? (
        <>
          <div className="row-sub" style={{ marginBottom: 10 }}>
            Sample: {sample.sample_no || '—'} · Size: {sample.size || '—'} · 狀態: {sample.status || '—'}
          </div>
          <BomEditor key={sample.id} bom={sample.bom} onChanged={load} />
        </>
      ) : (
        <div className="empty">未有樣本階段，撳「＋ 加階段」</div>
      )}

      <div className="card" style={{ marginTop: 20 }}>
        <h3 style={{ marginTop: 0 }}>📄 Import PDF Spec Sheet</h3>
        <input type="file" accept="application/pdf" onChange={uploadPdf} />
        {parsing && <div className="muted">解析中…</div>}
        {pdfResult && (
          <div style={{ marginTop: 10 }}>
            <div className="sub">✅ 解析結果（可 review，之後會預填欄位）：</div>
            <pre style={{ background: '#f6f7f9', padding: 12, borderRadius: 8, fontSize: 12, overflow: 'auto' }}>{JSON.stringify(pdfResult, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
