import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync, useDebounced } from '../hooks.js'
import { Loading, ErrorBox, Empty } from '../components/Common.jsx'

export default function MarketMatching() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [matchStatus, setMatchStatus] = useState('all')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 50

  const debouncedSearch = useDebounced(search, 300)

  // Reset to page 1 whenever filter changes
  useEffect(() => { setPage(1) }, [debouncedSearch, matchStatus])

  const { loading, data, error } = useAsync(
    () => api.marketMatching({
      search: debouncedSearch,
      match_status: matchStatus,
      page,
      page_size: PAGE_SIZE,
    }),
    [debouncedSearch, matchStatus, page],
  )

  const onSort = (key) => {
    // Sorting would be implemented in the API if needed
  }

  return (
    <>
      <div className="page-title">Market Matching</div>
      <div className="page-sub">Comparison of PIM customer labels vs Magento customer groups</div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search by SKU or market code…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={matchStatus} onChange={(e) => setMatchStatus(e.target.value)} title="Filter by match status">
          <option value="all">All Match Statuses</option>
          <option value="matched">Fully Matched</option>
          <option value="partial">Partially Matched</option>
          <option value="unmatched">Not Matched</option>
        </select>
        {data && <span className="muted" style={{ fontSize: 13 }}>{data.total.toLocaleString()} SKUs</span>}
      </div>

      {error && <ErrorBox error={error} />}
      {loading && <Loading label="Loading market matching data…" />}

      {data && !loading && (
        data.items.length === 0 ? (
          <Empty label="No SKUs match the current filters." />
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>PIM Markets</th>
                    <th>Magento Markets</th>
                    <th>Match Status</th>
                    <th>Match %</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={item.sku}
                      className="clickable"
                      onClick={() => navigate(`/market-matching/${encodeURIComponent(item.sku)}`)}
                    >
                      <td><code>{item.sku}</code></td>
                      <td>
                        <span className="badge-group">
                          {item.pim_markets.map((market) => (
                            <span key={market.code} className="badge badge-info">{market.code}</span>
                          ))}
                        </span>
                      </td>
                      <td>
                        <span className="badge-group">
                          {item.magento_markets.map((market) => (
                            <span key={market} className="badge badge-info">{market}</span>
                          ))}
                        </span>
                      </td>
                      <td>
                        {item.fully_matched ? (
                          <span className="badge badge-ok">✅ Fully Matched</span>
                        ) : item.match_count > 0 ? (
                          <span className="badge badge-warn">⚠️ Partially Matched</span>
                        ) : (
                          <span className="badge badge-err">❌ Not Matched</span>
                        )}
                      </td>
                      <td>
                        {item.match_percentage.toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <span className="page-info">Page {page} of {data.total_pages}</span>
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>‹ Prev</button>
              {/* Page numbers would go here - simplified for now */}
              <button disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>Next ›</button>
            </div>
          </>
        )
      )}
    </>
  )
}