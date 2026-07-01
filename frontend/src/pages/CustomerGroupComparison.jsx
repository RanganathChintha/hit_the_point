import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync, useDebounced } from '../hooks.js'
import { Loading, ErrorBox, Empty } from '../components/Common.jsx'
import SkuCopyButton from '../components/SkuCopyButton.jsx'

export default function CustomerGroupComparison() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [matchStatus, setMatchStatus] = useState('all')
  const [page, setPage] = useState(1)
  const PAGE_SIZE = 50

  const debouncedSearch = useDebounced(search, 300)

  useEffect(() => { setPage(1) }, [debouncedSearch, matchStatus])

  const { loading, data, error } = useAsync(
    () => api.customerGroupComparison({
      search: debouncedSearch,
      match_status: matchStatus,
      page,
      page_size: PAGE_SIZE,
    }),
    [debouncedSearch, matchStatus, page],
  )

  return (
    <>
      <div className="page-title">Customer Group Comparison</div>
      <div className="page-sub">Bidirectional comparison of PIM customer labels vs Magento customer groups</div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search by SKU or group code…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={matchStatus} onChange={(e) => setMatchStatus(e.target.value)} title="Filter by match status">
          <option value="all">All SKUs</option>
          <option value="matched">Matched</option>
          <option value="not_matched">Not Matched</option>
        </select>
        {data && <span className="muted" style={{ fontSize: 13 }}>{data.total.toLocaleString()} SKUs</span>}
      </div>

      {error && <ErrorBox error={error} />}
      {loading && <Loading label="Loading customer group data..." />}

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
                    <th>PIM Groups</th>
                    <th>Magento Groups</th>
                    <th>Match Status</th>
                    <th>Match %</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => {
                    const isMatched = item.fully_matched
                    const magentoSet = new Set(item.magento_groups)
                    const pimSet = new Set(item.pim_groups.map((g) => g.code))
                    return (
                      <tr
                        key={item.sku}
                        className="clickable"
                        onClick={() => navigate(`/customer-group-comparison/${encodeURIComponent(item.sku)}`)}
                      >
                        <td>
                          <code>{item.sku}</code>
                          <SkuCopyButton sku={item.sku} />
                        </td>
                        <td>
                          <span className="badge-group">
                            {item.pim_groups.map((group) => (
                              <span
                                key={group.code}
                                className={`badge ${magentoSet.has(group.code) ? 'badge-ok' : 'badge-warn'}`}
                                title={group.description || 'No description'}
                              >
                                {group.code}
                              </span>
                            ))}
                          </span>
                        </td>
                        <td>
                          <span className="badge-group">
                            {item.magento_groups.map((group) => (
                              <span
                                key={group}
                                className={`badge ${pimSet.has(group) ? 'badge-ok' : 'badge-info'}`}
                                title={pimSet.has(group) ? 'Present in both' : 'Only in Magento'}
                              >
                                {group}
                              </span>
                            ))}
                          </span>
                        </td>
                        <td>
                          {isMatched ? (
                            <span className="badge badge-ok">Matched</span>
                          ) : (
                            <span className="badge badge-err">Not Matched</span>
                          )}
                        </td>
                        <td>{item.match_percentage.toFixed(1)}%</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="pagination">
              <span className="page-info">Page {page} of {data.total_pages}</span>
              <button disabled={page === 1} onClick={() => setPage(page - 1)}>‹ Prev</button>
              <button disabled={page >= data.total_pages} onClick={() => setPage(page + 1)}>Next ›</button>
            </div>
          </>
        )
      )}
    </>
  )
}
