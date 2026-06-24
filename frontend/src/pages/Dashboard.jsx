import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox } from '../components/Common.jsx'

const fmt = (n) => (n ?? 0).toLocaleString()

export default function Dashboard() {
  const navigate = useNavigate()
  const { loading, data, error } = useAsync(() => api.summary(), [])

  if (loading) return <Loading label="Loading summary…" />
  if (error) return <ErrorBox error={error} />

  const s = data
  const goCat = (cat) => navigate(`/comparison?category=${encodeURIComponent(cat)}`)

  const cards = [
    { cls: 'ok', num: s.perfect, lbl: 'Perfect Matches', onClick: () => goCat('ok') },
    { cls: 'err', num: s.total_issues, lbl: 'Total Issues', onClick: () => navigate('/comparison') },
    { cls: 'err', num: s.missing_in_storefront, lbl: 'Missing in Storefront', onClick: () => goCat('Missing in Storefront') },
    { cls: 'warn', num: s.type_mismatches, lbl: 'Type Mismatches', onClick: () => goCat('Type Mismatch') },
    { cls: 'info', num: s.bundle_issues, lbl: 'Bundle Issues', onClick: () => goCat('Bundle Slot Issue') },
    { cls: 'info', num: s.configurable_issues, lbl: 'Configurable Issues', onClick: () => goCat('Configurable Child Issue') },
  ]

  return (
    <>
      <div className="page-title">Dashboard</div>
      <div className="page-sub">
        {fmt(s.pim_sku_count)} PIM SKUs &nbsp;·&nbsp; {fmt(s.storefront_sku_count)} Storefront SKUs
        &nbsp;·&nbsp; {fmt(s.market_count)} markets
      </div>

      <div className="summary-grid">
        {cards.map((c) => (
          <div key={c.lbl} className={`card ${c.cls} clickable`} onClick={c.onClick}>
            <div className="num">{fmt(c.num)}</div>
            <div className="lbl">{c.lbl}</div>
          </div>
        ))}
      </div>

      <div className="panel">
        <h3>Total SKUs Compared</h3>
        <div className="row-gap">
          <div style={{ fontSize: 30, fontWeight: 700 }}>{fmt(s.total)}</div>
          <div className="muted">
            {fmt(s.perfect)} in sync ({((s.perfect / s.total) * 100 || 0).toFixed(1)}%) ·
            {' '}{fmt(s.total_issues)} need attention
          </div>
        </div>
        <div style={{ marginTop: 14, height: 10, borderRadius: 999, background: '#fee2e2', overflow: 'hidden' }}>
          <div
            style={{
              width: `${(s.perfect / s.total) * 100 || 0}%`,
              height: '100%',
              background: 'var(--ok)',
            }}
          />
        </div>
      </div>

      <p className="muted" style={{ fontSize: 13 }}>
        Click any card to jump into the filtered comparison view.
      </p>
    </>
  )
}
