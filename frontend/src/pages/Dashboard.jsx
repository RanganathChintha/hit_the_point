import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox } from '../components/Common.jsx'

const fmt = (n) => (n ?? 0).toLocaleString()

export default function Dashboard() {
  const navigate = useNavigate()
  const [refreshKey, setRefreshKey] = useState(0)
  const [fetchMode, setFetchMode] = useState('previous')
  const [reloadStatus, setReloadStatus] = useState(null)
  const [reloadBusy, setReloadBusy] = useState(false)

  const { loading, data, error } = useAsync(() => api.summary(), [refreshKey])

  const handleReload = async (fetch) => {
    setReloadBusy(true)
    setReloadStatus(null)
    try {
      const result = await api.magentoReload(fetch)
      setReloadStatus({ success: true, message: result.message })
      setRefreshKey((value) => value + 1)
    } catch (err) {
      setReloadStatus({ success: false, message: err.detail || err.message || 'Reload failed.' })
    } finally {
      setReloadBusy(false)
    }
  }

  if (loading) return <Loading label="Loading summary…" />
  if (error) return <ErrorBox error={error} />

  const s = data
  const goCat = (cat) => navigate(`/comparison?category=${encodeURIComponent(cat)}`)

  let subtitleContent = (
    <>
      {fmt(s.pim_sku_count)} PIM SKUs &nbsp;·&nbsp; {fmt(s.magento_sku_count)} Magento SKUs
    </>
  )

  if (s.customer_group_comparison) {
    subtitleContent = (
      <>
        {fmt(s.pim_sku_count)} PIM SKUs &nbsp;·&nbsp; {fmt(s.magento_sku_count)} Magento SKUs
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

      <div className="panel magento-panel">
        <h3>Magento Data Source</h3>
        <div className="row-gap">
          <label>
            <input
              type="radio"
              name="magento-source"
              value="previous"
              checked={fetchMode === 'previous'}
              onChange={() => setFetchMode('previous')}
            />
            Use existing previous Magento data files
          </label>
          <label>
            <input
              type="radio"
              name="magento-source"
              value="fetch"
              checked={fetchMode === 'fetch'}
              onChange={() => setFetchMode('fetch')}
            />
            Fetch fresh Magento products and categories now
          </label>
          <div className="muted" style={{ marginTop: 8 }}>
            Current product file: <code>{s.magento_products_file || 'n/a'}</code><br />
            Current category file: <code>{s.magento_cat_file || 'n/a'}</code>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button
              className="btn"
              disabled={reloadBusy}
              onClick={() => handleReload(fetchMode === 'fetch')}
            >
              {reloadBusy ? 'Processing…' : fetchMode === 'fetch' ? 'Fetch Magento data + reload' : 'Reload existing data'}
            </button>
            <button
              className="btn ghost"
              onClick={() => handleReload(false)}
              disabled={reloadBusy}
            >
              Reload existing data
            </button>
          </div>
          {reloadStatus && (
            <div className={`muted ${reloadStatus.success ? 'ok' : 'err'}`}>
              {reloadStatus.message}
            </div>
          )}
        </div>
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