import { Link, NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import StylesList from './pages/StylesList.jsx'
import StyleDetail from './pages/StyleDetail.jsx'
import Materials from './pages/Materials.jsx'

export default function App() {
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <Link to="/" className="brand">👟 dev-app</Link>
          <nav className="nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink>
            <NavLink to="/styles" className={({ isActive }) => (isActive ? 'active' : '')}>鞋款</NavLink>
            <NavLink to="/materials" className={({ isActive }) => (isActive ? 'active' : '')}>物料主檔</NavLink>
          </nav>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/styles" element={<StylesList />} />
        <Route path="/styles/:id" element={<StyleDetail />} />
        <Route path="/materials" element={<Materials />} />
      </Routes>
    </>
  )
}
