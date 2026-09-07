const LOCAL_DEVS = ['localhost', '127.0.0.1']

const API =
  window.location.protocol === 'file:' ||
  LOCAL_DEVS.includes(window.location.hostname)
    ? 'http://127.0.0.1:8000'
    : 'https://fraudshield-ai-production-510a.up.railway.app'

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `Server error (${res.status})`
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  base: API,
  get: (path) => request(path),
  post: (path, body) =>
    request(path, { method: 'POST', body: JSON.stringify(body) }),
  getHealth: () => request('/health'),
  getStats: () => request('/dashboard/stats'),
  getFeed: (limit = 50) => request(`/dashboard/feed?limit=${limit}`),
  getAlerts: (limit = 20) => request(`/dashboard/alerts?limit=${limit}`),
  simulate: (mode, numTransactions) =>
    request('/simulate', {
      method: 'POST',
      body: JSON.stringify({ mode, num_transactions: numTransactions }),
    }),
  reset: () => request('/dashboard/reset', { method: 'POST' }),
  streamUrl: () => `${API}/simulate/stream`,
}

export function openStream() {
  return new EventSource(api.streamUrl())
}