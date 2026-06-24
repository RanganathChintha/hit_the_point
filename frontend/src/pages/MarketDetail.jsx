import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox } from '../components/Common.jsx'

export default function MarketDetail() {
  const { code } = useParams()
  const navigate = useNavigate()
  const { loading, data, error } = useAsync(() => api.marketDetail(code), [code])

  return (
    <>
      <Link to="/markets" className="back-link">← Back to markets</Link>

      {loading && <Loading label="Loading market…" />}
      {error && (
        <ErrorBox error={
          typeof error.detail === 'object' && error.detail?.message
            ? error.detail.message
            : error
        } />
      )}

      {data && (
        <>
          <div className="page-title">
            <span className="badge badge-info" style={{ fontSize: 14 }}>{data.code}</span>{' '}
            {data.description}
          </div>
          <div className="page-sub row-gap">
            <span>{data.count.toLocaleString()} products</span>
            <Link to={`/comparison?market=${encodeURIComponent(data.code)}`} className="btn ghost" style={{ padding: '4px 12px' }}>
              View in comparison →
            </Link>
          </div>

          <div className="panel">
            <h3>Breakdown by Product Type</h3>
            <div className="row-gap">
              {Object.entries(data.by_type)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([ptype, skus]) => (
                  <span key={ptype} className="badge badge-ptype" style={{ fontSize: 12 }}>
                    {ptype}: {skus.length}
                  </span>
                ))}
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Type</th>
                  <th>Name</th>
                </tr>
              </thead>
              <tbody>
                {data.skus.map((p) => (
                  <tr
                    key={p.sku}
                    className="clickable"
                    onClick={() => navigate(`/sku/${encodeURIComponent(p.sku)}`)}
                  >
                    <td><code>{p.sku}</code></td>
                    <td><span className="badge badge-ptype">{p.product_type}</span></td>
                    <td className="name-cell" title={p.name}>{p.name || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  )
}
