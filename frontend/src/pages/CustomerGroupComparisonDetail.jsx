import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox } from '../components/Common.jsx'
import SkuCopyButton from '../components/SkuCopyButton.jsx'

export default function CustomerGroupComparisonDetail() {
  const { sku } = useParams()
  const cg = useAsync(() => api.customerGroupComparisonDetail(sku), [sku])

  if (!cg.data) return <Loading label="Loading SKU..." />
  if (cg.error) return <ErrorBox error={cg.error} />

  const data = cg.data
  const totalPim = data.total_pim_groups ?? 0
  const shared = data.shared ?? []
  const pimOnly = data.pim_only ?? []
  const magentoOnly = data.magento_only ?? []
  const matchCount = data.match_count ?? 0

  return (
    <>
      <Link to="/customer-group-comparison" className="back-link">← Back to customer group comparison</Link>

      <div className="page-title">
        <code>{data.sku}</code>
        <SkuCopyButton sku={data.sku} />
      </div>
      <div className="page-sub">Customer Group Comparison Details</div>

      <div className="panel">
        <h3>Match Summary</h3>
        <div className="kv">
          <span>Shared Groups:</span>
          <b>{shared.length}</b>
        </div>
        <div className="kv">
          <span>Only in PIM:</span>
          <b>{pimOnly.length}</b>
        </div>
        <div className="kv">
          <span>Only in Magento:</span>
          <b>{magentoOnly.length}</b>
        </div>
        <div className="kv">
          <span>Match Percentage:</span>
          <b>
            {totalPim > 0
              ? ((matchCount / totalPim) * 100).toFixed(1) + '%'
              : 'N/A'}
          </b>
        </div>
        <div className="kv">
          <span>Status:</span>
          <b className={`badge ${pimOnly.length === 0 ? 'badge-ok' : pimOnly.length > 0 ? 'badge-warn' : 'badge-err'}`}>
            {pimOnly.length === 0
              ? 'Fully Matched'
              : matchCount > 0
                ? 'Partially Matched'
                : 'Not Matched'}
          </b>
        </div>
      </div>

      <div className="panel">
        <h3>Shared Groups (present in both)</h3>
        {shared.length > 0 ? (
          <div className="badge-group">
            {shared.map((code) => (
              <span key={code} className="badge badge-ok">{code}</span>
            ))}
          </div>
        ) : (
          <span className="muted">No shared groups</span>
        )}
      </div>

      <div className="panel">
        <h3>Only in PIM</h3>
        {pimOnly.length > 0 ? (
          <div className="badge-group">
            {pimOnly.map((code) => (
              <span key={code} className="badge badge-warn" title="Present in PIM but not in Magento">{code}</span>
            ))}
          </div>
        ) : (
          <span className="muted">No groups unique to PIM</span>
        )}
      </div>

      <div className="panel">
        <h3>Only in Magento</h3>
        {magentoOnly.length > 0 ? (
          <div className="badge-group">
            {magentoOnly.map((code) => (
              <span key={code} className="badge badge-info" title="Present in Magento but not in PIM">{code}</span>
            ))}
          </div>
        ) : (
          <span className="muted">No groups unique to Magento</span>
        )}
      </div>

      <div className="panel">
        <h3>PIM Groups (Customer Labels)</h3>
        {data.pim_groups?.length > 0 ? (
          <div className="badge-group">
            {data.pim_groups.map((group) => (
              <span key={group.code} className="badge badge-info" title={group.description || 'No description'}>{group.code}</span>
            ))}
          </div>
        ) : (
          <span className="muted">No customer group data in PIM</span>
        )}
      </div>

      <div className="panel">
        <h3>Magento Groups (Customer Groups)</h3>
        {data.magento_groups?.length > 0 ? (
          <div className="badge-group">
            {data.magento_groups.map((group) => (
              <span key={group} className="badge badge-info">{group}</span>
            ))}
          </div>
        ) : (
          <span className="muted">No customer group data in Magento</span>
        )}
      </div>
    </>
  )
}
