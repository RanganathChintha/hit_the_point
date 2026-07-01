// Thin API client. In dev, Vite proxies /api → FastAPI (see vite.config.js).
const BASE = import.meta.env.VITE_API_BASE || ''

async function request(path, method = 'GET', params, body) {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
    })
  }
  const options = { method }
  if (body !== undefined) {
    options.headers = { 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  const res = await fetch(url, options)
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
  health: () => request('/api/health'),
  summary: () => request('/api/summary'),
  reports: (params) => request('/api/reports', 'GET', params),
  reportDetail: (sku) => request(`/api/reports/${encodeURIComponent(sku)}`),
  hierarchy: (sku) => request(`/api/hierarchy/${encodeURIComponent(sku)}`),
  magentoReload: (fetch = false) => request('/api/magento-reload', 'POST', { fetch }),
  // Customer Group Comparison APIs
  customerGroupComparison: (params) => request('/api/customer-group-comparison', 'GET', params),
  customerGroupComparisonSummary: () => request('/api/customer-group-comparison/summary'),
  customerGroupComparisonDetail: (sku) => request(`/api/customer-group-comparison/${encodeURIComponent(sku)}`),
}
