import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import Comparison from './pages/Comparison.jsx'
import SkuDetail from './pages/SkuDetail.jsx'
import CustomerGroupComparison from './pages/CustomerGroupComparison.jsx'
import CustomerGroupComparisonDetail from './pages/CustomerGroupComparisonDetail.jsx'

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>PIM ↔ Magento Reconciliation</h1>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/comparison">Comparison</NavLink>
          <NavLink to="/customer-group-comparison">Customer Groups</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/comparison" element={<Comparison />} />
          <Route path="/sku/:sku" element={<SkuDetail />} />
          <Route path="/customer-group-comparison" element={<CustomerGroupComparison />} />
          <Route path="/customer-group-comparison/:sku" element={<CustomerGroupComparisonDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
