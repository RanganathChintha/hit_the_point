import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync, useDebounced } from '../hooks.js'
import { Loading, ErrorBox, Empty } from '../components/Common.jsx'

export default function Markets() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const q = useDebounced(search, 300)
  const { loading, data, error } = useAsync(() => api.markets(q), [q])

  return (
    <>
      <div className="page-title">Markets</div>
      <div className="page-sub">Products per brand / customer-label code (from PIM).</div>

      <div className="toolbar">
        <input
          type="search"
          placeholder="Search by code or description…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {data && <span className="muted" style={{ fontSize: 13 }}>{data.count} market(s)</span>}
      </div>

      {error && <ErrorBox error={error} />}
      {loading && <Loading label="Loading markets…" />}

      {data && !loading && (
        data.items.length === 0 ? <Empty label="No markets matched." /> : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Description</th>
                  <th>Products</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((m) => (
                  <tr
                    key={m.code}
                    className="clickable"
                    onClick={() => navigate(`/markets/${encodeURIComponent(m.code)}`)}
                  >
                    <td><span className="badge badge-info">{m.code}</span></td>
                    <td>{m.description || '—'}</td>
                    <td><b>{m.count.toLocaleString()}</b></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      )}
    </>
  )
}
