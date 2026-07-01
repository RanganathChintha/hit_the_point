// Thin API client. In dev, Vite proxies /api → FastAPI (see vite.config.js).
const BASE = import.meta.env.VITE_API_BASE || ''

async function get(path, params) {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const res = await fetch(url)
  if (!res.ok) {
    let detail
    try {
      detail = (await res.json()).detail
    } catch {
      detail = res.statusText
    }
    const err = new Error(typeof detail === 'string' ? detail : 'Request failed')
    err.status = res.status
    err.detail = detail
    throw err
  }
  return res.json()
}

export const api = {
  health: () => get('/api/health'),
  summary: () => get('/api/summary'),
  reports: (params) => get('/api/reports', params),
  reportDetail: (sku) => get(`/api/reports/${encodeURIComponent(sku)}`),
  hierarchy: (sku) => get(`/api/hierarchy/${encodeURIComponent(sku)}`),
  // Customer Group Comparison APIs
  customerGroupComparison: (params) => get('/api/customer-group-comparison', params),
  customerGroupComparisonSummary: () => get('/api/customer-group-comparison/summary'),
  customerGroupComparisonDetail: (sku) => get(`/api/customer-group-comparison/${encodeURIComponent(sku)}`),
}
