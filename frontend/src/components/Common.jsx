// Small shared presentational helpers used across pages.

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="loading">
      <div className="spinner" />
      {label}
    </div>
  )
}

export function ErrorBox({ error }) {
  const msg = typeof error === 'string' ? error : error?.message || 'Something went wrong.'
  return <div className="error-box">⚠️ {msg}</div>
}

export function Empty({ label = 'No results.' }) {
  return <div className="empty">{label}</div>
}

const ISSUE_BADGE = {
  'Missing in Magento': 'badge-err',
  'Type Mismatch': 'badge-warn',
  'Bundle Slot Issue': 'badge-info',
  'Bundle SKU Issue': 'badge-info',
  'Configurable Child Issue': 'badge-info',
}

export function StatusBadges({ hasIssues, issueCats }) {
  if (!hasIssues) return <span className="badge badge-ok">✅ OK</span>
  return (
    <span className="badge-group">
      {issueCats.map((c) => (
        <span key={c} className={`badge ${ISSUE_BADGE[c] || 'badge-info'}`}>{c}</span>
      ))}
    </span>
  )
}

export function SkuChips({ skus, variant }) {
  if (!skus || skus.length === 0) return null
  return (
    <div className="sku-list">
      {skus.map((s) => (
        <span key={s} className={`sku-chip ${variant || ''}`}>{s}</span>
      ))}
    </div>
  )
}
