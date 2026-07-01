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

  // Update the subtitle to show market matching stats if available
  let subtitleContent = (
    <>
      {fmt(s.pim_sku_count)} PIM SKUs &nbsp;·&nbsp; {fmt(s.magento_sku_count)} Magento SKUs
      &nbsp;·&nbsp; {fmt(s.market_count)} markets
    </>
  )

  if (s.customer_group_comparison) {
    subtitleContent = (
      <>
        {fmt(s.pim_sku_count)} PIM SKUs &nbsp;·&nbsp; {fmt(s.magento_sku_count)} Magento SKUs
        &nbsp;·&nbsp; {fmt(s.market_count)} markets
        &nbsp;·&nbsp; {fmt(s.customer_group_comparison?.total_skus_with_groups ?? 0)} SKUs with groups
      </>
    )
  }

  // Define the cards array for the summary grid
  const cards = [
    { cls: 'ok', num: s.perfect, lbl: 'Perfect Matches', onClick: () => goCat('ok') },
    { cls: 'err', num: s.total_issues, lbl: 'Total Issues', onClick: () => navigate('/comparison') },
    { cls: 'err', num: s.missing_in_magento, lbl: 'Missing in Magento', onClick: () => goCat('Missing in Magento') },
    { cls: 'pim-err', num: s.missing_in_pim, lbl: 'Missing in PIM', onClick: () => navigate('/comparison?missing=pim') },
    { cls: 'warn', num: s.type_mismatches, lbl: 'Type Mismatches', onClick: () => goCat('Type Mismatch') },
    { cls: 'info', num: s.bundle_issues, lbl: 'Bundle Issues', onClick: () => goCat('Bundle Slot Issue') },
    { cls: 'info', num: s.configurable_issues, lbl: 'Configurable Issues', onClick: () => goCat('Configurable Child Issue') },
    // Customer Group Comparison Cards
    {
      cls: 'info',
      num: s.customer_group_comparison?.total_skus_with_groups ?? 0,
      lbl: 'SKUs with Customer Groups',
      onClick: () => navigate('/customer-group-comparison'),
    },
    {
      cls: s.customer_group_comparison?.match_rate ?? 0 >= 95 ? 'ok' : s.customer_group_comparison?.match_rate ?? 0 >= 80 ? 'warn' : 'err',
      num: s.customer_group_comparison?.match_rate ?? 0,
      lbl: 'Customer Group Match Rate',
      onClick: () => navigate('/customer-group-comparison?match_status=unmatched'),
    },
  ]

  return (
    <>
      <div className="page-title">Dashboard</div>
      <div className="page-sub">
        {subtitleContent}
      </div>

      {/* Product Count Comparison Panel */}
      <div className="panel comparison-panel">
        <h3>Product Count Comparison</h3>
        <div className="comparison-stats">
          <div className="stat-row">
            <div className="stat-label">PIM Products</div>
            <div className="stat-value">{fmt(s.pim_sku_count)}</div>
          </div>
          <div className="stat-row">
            <div className="stat-label">Magento Products</div>
            <div className="stat-value">{fmt(s.magento_sku_count)}</div>
          </div>
          <div className="stat-row missing">
            <div className="stat-label">Missing in Magento</div>
            <div className="stat-value err">{fmt(s.missing_in_magento)}</div>
          </div>
          <div className="stat-row missing">
            <div className="stat-label">Missing in PIM</div>
            <div className="stat-value err">{fmt(s.missing_in_pim)}</div>
          </div>
          <div className="stat-row total">
            <div className="stat-label">Match Rate</div>
            <div className="stat-value ok">{((s.perfect / s.total) * 100 || 0).toFixed(1)}%</div>
          </div>
        </div>
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