import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Comparison from './pages/Comparison.jsx'
import SkuDetail from './pages/SkuDetail.jsx'
import Markets from './pages/Markets.jsx'
import MarketDetail from './pages/MarketDetail.jsx'

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>PIM ↔ Magento Reconciliation</h1>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/comparison">Comparison</NavLink>
          <NavLink to="/markets">Markets</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/sku/:sku" element={<SkuDetail />} />
          <Route path="/markets" element={<Markets />} />
          <Route path="/markets/:code" element={<MarketDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
