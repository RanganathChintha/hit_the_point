import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAsync } from '../hooks.js'
import { Loading, ErrorBox } from '../components/Common.jsx'

export default function MarketMatchingDetail() {
  const { sku } = useParams()
  const marketMatching = useAsync(() => api.marketMatchingDetail(sku), [sku])

  return (
    <>
      <Link to="/market-matching" className="back-link">← Back to market matching</Link>

      {marketMatching.loading && <Loading label="Loading SKU…" />}
      {marketMatching.error && <ErrorBox error={marketMatching.error} />}

      {marketMatching.data && (
        <>
          <div className="page-title">
            <code>{marketMatching.data.sku}</code>
          </div>
          <div className="page-sub">Market Matching Details</div>

          <div className="panel">
            <h3>Market Matching Summary</h3>
            <div className="kv">
              <span>PIM Markets: <b>{marketMatching.data.total_pim_markets}</b></span>
              <span>·</span>
              <span>Matched Markets: <b>{marketMatching.data.match_count}</b></span>
              <span className="badge">
                {marketMatching.data.fully_matched
                  ? '✅ Fully Matched'
                  : marketMatching.data.match_count > 0
                  ? '⚠️ Partially Matched'
                  : '❌ Not Matched'}
              </span>
            </div>
            <div className="kv">
              <span>Match Percentage:</span>
              <b>
                {marketMatching.data.total_pim_markets > 0
                  ? (marketMatching.data.match_count / marketMatching.data.total_pim_markets * 100).toFixed(1) + '%'
                  : 'N/A'}
              </b>
            </div>
          </div>

          <div className="panel">
            <h3>PIM Markets (Customer Labels)</h3>
            {marketMatching.data.pim_markets.length > 0 ? (
              <div className="badge-group">
                {marketMatching.data.pim_markets.map((market) => (
                  <span
                    key={market.code}
                    className={`badge badge-info${marketMatching.data.market_matches.find(m => m.code === market.code && m.matched) ? '' : '-invalid'}`}
                    title={market.description || 'No description'}
                  >
                    {market.code}
                  </span>
                ))}
              </div>
            ) : (
              <span className="muted">No market data in PIM</span>
            )}
          </div>

          <div className="panel">
            <h3>Magento Markets (Customer Groups)</h3>
            {marketMatching.data.magento_markets.length > 0 ? (
              <div className="badge-group">
                {marketMatching.data.magento_markets.map((market) => (
                  <span
                    key={market}
                    className={`badge badge-info${marketMatching.data.market_matches.find(m => m.code === market && m.matched) ? '' : '-invalid'}`}
                  >
                    {market}
                  </span>
                ))}
              </div>
            ) : (
              <span className="muted">No market data in Magento</span>
            )}
          </div>

          <div className="panel">
            <h3>Match Details</h3>
            <div className="kv">
              <span>Matched Markets:</span>
              <div className="badge-group">
                {marketMatching.data.market_matches
                  .filter(m => m.matched)
                  .map(m => (
                    <span key={m.code} className="badge badge-ok">
                      {m.code}
                    </span>
                  ))}
              </div>
            </div>
            {marketMatching.data.market_matches
              .filter(m => !m.matched)
              .length > 0 && (
                <div className="kv">
                  <span>Unmatched Markets:</span>
                  <div className="badge-group">
                    {marketMatching.data.market_matches
                      .filter(m => !m.matched)
                      .map(m => (
                        <span
                          key={m.code}
                          className="badge badge-err"
                          title={`PIM: ${m.code} not found in Magento`}
                        >
                          {m.code}
                        </span>
                      ))}
                  </div>
                </div>
              )}
          </div>
        </>
      )}
    </>
  )
}