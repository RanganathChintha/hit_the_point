import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox, StatusBadges, SkuChips } from '../components/Common.jsx'

export default function SkuDetail() {
  const { sku } = useParams()
  const detail = useAsync(() => api.reportDetail(sku), [sku])
  const tree = useAsync(() => api.hierarchy(sku), [sku])

  return (
    <>
      <Link to="/comparison" className="back-link">← Back to comparison</Link>

      {detail.loading && <Loading label="Loading SKU…" />}
      {detail.error && <ErrorBox error={detail.error} />}

      {detail.data && (
        <>
          <div className="page-title">
            <code>{detail.data.sku}</code>
          </div>
          <div className="page-sub">{detail.data.name || '—'}</div>

          <div className="panel">
            <h3>Overview</h3>
            <div className="kv">
              <span className="badge badge-ptype">PIM: {detail.data.pim_type}</span>
              <span>→</span>
              <span className="badge badge-ftype">Storefront: {detail.data.storefront_type}</span>
              <StatusBadges hasIssues={detail.data.has_issues} issueCats={detail.data.issue_cats} />
            </div>
            <div className="kv">
              {detail.data.found_in_storefront
                ? <span className="badge badge-ok">✅ Found in Storefront</span>
                : <span className="badge badge-err">❌ Missing in Storefront</span>}
            </div>
          </div>

          <TypeComparison tc={detail.data.type_comparison} />
          <BundleComparison bc={detail.data.bundle_comparison} />
          <ConfigurableComparison cc={detail.data.configurable_comparison} />
        </>
      )}

      <div className="panel">
        <h3>Hierarchy</h3>
        {tree.loading && <Loading label="Loading hierarchy…" />}
        {tree.error && <ErrorBox error={tree.error} />}
        {tree.data && (
          <div className="row-gap" style={{ alignItems: 'flex-start', gap: 18 }}>
            <div style={{ flex: 1, minWidth: 280 }}>
              <div className="muted" style={{ marginBottom: 6, fontWeight: 600 }}>PIM</div>
              <pre className="tree">{tree.data.pim.join('\n') || '—'}</pre>
            </div>
            <div style={{ flex: 1, minWidth: 280 }}>
              <div className="muted" style={{ marginBottom: 6, fontWeight: 600 }}>Storefront</div>
              <pre className="tree">{tree.data.storefront.join('\n') || '—'}</pre>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function MatchBadge({ ok }) {
  return ok
    ? <span className="badge badge-ok">✅ Match</span>
    : <span className="badge badge-err">❌ Mismatch</span>
}

function TypeComparison({ tc }) {
  if (!tc) return null
  return (
    <div className="panel">
      <h3>Type Comparison</h3>
      <div className="kv">
        <span className="badge badge-ptype">PIM: {tc.pim_type}</span>
        <span>→</span>
        <span className="badge badge-ftype">Storefront: {tc.storefront_type}</span>
        <MatchBadge ok={tc.types_match} />
      </div>
      {tc.mismatch_note && <p className="muted">{tc.mismatch_note}</p>}
    </div>
  )
}

function BundleComparison({ bc }) {
  if (!bc) return null
  return (
    <div className="panel">
      <h3>Bundle Slots</h3>
      <div className="kv">
        <span>PIM slots: <b>{bc.pim_slot_count}</b></span>
        <span>·</span>
        <span>Storefront slots: <b>{bc.storefront_slot_count}</b></span>
        <MatchBadge ok={bc.slot_count_match} />
      </div>
      {bc.slots_only_in_pim.length > 0 && (
        <div className="kv"><span>❌ Missing in Storefront:</span><SkuChips skus={bc.slots_only_in_pim} variant="missing" /></div>
      )}
      {bc.slots_only_in_storefront.length > 0 && (
        <div className="kv"><span>ℹ️ Extra in Storefront:</span><SkuChips skus={bc.slots_only_in_storefront} variant="extra" /></div>
      )}
      {Object.entries(bc.per_slot).map(([slot, sd]) => (
        <div className="slot-box" key={slot}>
          <div className="kv">
            <b style={{ fontSize: 12 }}>[{slot.toUpperCase()}]</b>
            <span>PIM: <b>{sd.pim_sku_count}</b></span>
            <span>·</span>
            <span>Storefront: <b>{sd.storefront_sku_count}</b></span>
            <MatchBadge ok={sd.count_match} />
          </div>
          {sd.skus_only_in_pim.length > 0 && (
            <div className="kv"><span>❌ Missing:</span><SkuChips skus={sd.skus_only_in_pim} variant="missing" /></div>
          )}
          {sd.skus_only_in_storefront.length > 0 && (
            <div className="kv"><span>ℹ️ Extra:</span><SkuChips skus={sd.skus_only_in_storefront} variant="extra" /></div>
          )}
          {sd.count_match && sd.skus_only_in_pim.length === 0 && sd.skus_only_in_storefront.length === 0 && (
            <span className="badge badge-ok">✅ All children match</span>
          )}
        </div>
      ))}
    </div>
  )
}

function ConfigurableComparison({ cc }) {
  if (!cc) return null
  return (
    <div className="panel">
      <h3>Configurable Children</h3>
      <div className="kv">
        <span>PIM: <b>{cc.pim_child_count}</b></span>
        <span>·</span>
        <span>Storefront: <b>{cc.storefront_child_count}</b></span>
        <MatchBadge ok={cc.count_match} />
      </div>
      {cc.skus_only_in_pim.length > 0 && (
        <div className="kv"><span>❌ Missing in Storefront:</span><SkuChips skus={cc.skus_only_in_pim} variant="missing" /></div>
      )}
      {cc.skus_only_in_storefront.length > 0 && (
        <div className="kv"><span>ℹ️ Extra in Storefront:</span><SkuChips skus={cc.skus_only_in_storefront} variant="extra" /></div>
      )}
      {cc.unresolved_storefront_ids?.length > 0 && (
        <p className="muted">⚠️ Unresolved Storefront IDs: {cc.unresolved_storefront_ids.join(', ')}</p>
      )}
      {cc.count_match && cc.skus_only_in_pim.length === 0 && cc.skus_only_in_storefront.length === 0 && (
        <span className="badge badge-ok">✅ All children match</span>
      )}
    </div>
  )
}
