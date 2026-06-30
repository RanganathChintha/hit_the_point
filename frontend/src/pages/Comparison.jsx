import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync, useDebounced } from '../hooks.js'
import { Loading, ErrorBox, Empty, StatusBadges } from '../components/Common.jsx'

const PAGE_SIZE = 50

const SORTABLE = [
  { key: 'sku', label: 'SKU' },
  { key: 'name', label: 'Name' },
  { key: 'pim_type', label: 'PIM Type' },
  { key: 'magento_type', label: 'Magento Type' },
  { key: 'has_issues', label: 'Status' },
]

export default function Comparison() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [search, setSearch] = useState('')
  const [category, setCategory] = useState(searchParams.get('category') || 'all')
  const [market, setMarket] = useState(searchParams.get('market') || 'all')
  const [sort, setSort] = useState('sku')
  const [direction, setDirection] = useState('asc')
  const [page, setPage] = useState(1)

  const debouncedSearch = useDebounced(search, 300)

  // Keep the category/market query-params in sync when arriving from another page.
  useEffect(() => {
    const c = searchParams.get('category')
    if (c && c !== category) setCategory(c)
    const m = searchParams.get('market')
    if (m && m !== market) setMarket(m)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  // Reset to page 1 whenever a filter/sort changes.
  useEffect(() => { setPage(1) }, [debouncedSearch, category, market, sort, direction])

  const summaryState = useAsync(() => api.summary(), [])
  const issueCategories = summaryState.data?.issue_categories || []

  const marketsState = useAsync(() => api.markets(), [])
  const marketOptions = marketsState.data?.items || []

  const { loading, data, error } = useAsync(
    () => api.reports({
      search: debouncedSearch,
      category,
      market,
      sort,
      direction,
      page,
      page_size: PAGE_SIZE,
    }),
    [debouncedSearch, category, market, sort, direction, page],
  )

  const onSort = (key) => {
    if (sort === key) setDirection((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSort(key); setDirection('asc') }
  }

  const syncParam = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value === 'all') next.delete(key)
    else next.set(key, value)
    setSearchParams(next, { replace: true })
  }

  const setCat = (c) => { setCategory(c); syncParam('category', c) }
  const setMkt = (m) => { setMarket(m); syncParam('market', m) }

  // Build category filter options including special categories
  const specialCategories = ['missingInMagento', 'missingInPIM']
  const allCategories = ['all', 'ok', ...specialCategories, ...issueCategories]

  return (
    <>
      <div className="page-title">Comparison</div>
      <div className="page-sub">PIM-driven comparison of every SKU against Magento.</div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search by SKU or name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={market} onChange={(e) => setMkt(e.target.value)} title="Filter by market">
          <option value="all">All markets</option>
          {marketOptions.map((m) => (
            <option key={m.code} value={m.code}>
              {m.code} — {m.description} ({m.count.toLocaleString()})
            </option>
          ))}
        </select>
        <select value={category} onChange={(e) => setCat(e.target.value)} title="Filter by status">
          <option value="all">All SKUs</option>
          <option value="ok">OK only</option>
          {issueCategories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        {data && <span className="muted" style={{ fontSize: 13 }}>{data.total.toLocaleString()} match</span>}
      </div>

      {error && <ErrorBox error={error} />}
      {loading && <Loading label="Loading rows…" />}

      {data && !loading && (
        data.items.length === 0 ? <Empty /> : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {SORTABLE.map((col) => {
                      const sorted = sort === col.key
                      return (
                        <th
                          key={col.key}
                          className={`sortable ${sorted ? 'sorted' : ''}`}
                          onClick={() => onSort(col.key)}
                        >
                          {col.label}
                          <span className="sort-icon">
                            {sorted ? (direction === 'asc' ? '↑' : '↓') : '⇅'}
                          </span>
                        </th>
                      )
                    })}
                    <th>Markets</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((r) => (
                    <tr
                      key={r.sku}
                      className="clickable"
                      onClick={() => navigate(`/sku/${encodeURIComponent(r.sku)}`)}
                    >
                      <td><code>{r.sku}</code></td>
                      <td className="name-cell" title={r.name}>{r.name || '—'}</td>
                      <td><span className="badge badge-ptype">{r.pim_type}</span></td>
                      <td><span className="badge badge-ftype">{r.magento_type}</span></td>
                      <td><StatusBadges hasIssues={r.has_issues} issueCats={r.issue_cats} /></td>
                      <td>
                        <span className="badge-group">
                          {(r.markets || []).map((m) => (
                            <span key={m} className="badge badge-info">{m}</span>
                          ))}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} totalPages={data.total_pages} onGo={setPage} />
          </>
        )
      )}
    </>
  )
}

function Pagination({ page, totalPages, onGo }) {
  if (totalPages <= 1) return null
  const pages = []
  for (let p = 1; p <= totalPages; p++) {
    if (totalPages > 10 && Math.abs(p - page) > 2 && p !== 1 && p !== totalPages) {
      if (p === 2 || p === totalPages - 1) pages.push('…')
      continue
    }
    pages.push(p)
  }
  return (
    <div className="pagination">
      <span className="page-info">Page {page} of {totalPages}</span>
      <button disabled={page === 1} onClick={() => onGo(page - 1)}>‹ Prev</button>
      {pages.map((p, i) =>
        p === '…'
          ? <span key={`e${i}`} style={{ padding: '0 4px' }}>…</span>
          : <button key={p} className={p === page ? 'active' : ''} onClick={() => onGo(p)}>{p}</button>,
      )}
      <button disabled={page === totalPages} onClick={() => onGo(page + 1)}>Next ›</button>
    </div>
  )
}
