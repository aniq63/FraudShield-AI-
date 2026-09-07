export function fmtMoney(v) {
  return `$${parseFloat(v || 0).toLocaleString('en', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function fmtNum(v) {
  return parseFloat(v || 0).toLocaleString()
}

export function cleanKey(s) {
  return String(s || '').replace(/_/g, ' ')
}

export function clampProb(p) {
  return Math.min(1, Math.max(0, parseFloat(p || 0)))
}

export function probColor(p) {
  const v = clampProb(p)
  return v >= 0.5 ? 'var(--danger)' : v >= 0.25 ? 'var(--warn)' : 'var(--success)'
}

export function shortTime(t) {
  return String(t || '').substring(0, 8)
}

export function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

export function toFeedRow(result) {
  const txn = result.transaction || {}
  return {
    time: txn.transaction_time || '',
    amount: txn.transaction_amount || 0,
    category: txn.category || '',
    fraud_probability: result.fraud_probability,
    simulation_mode: result.simulation_mode,
    decision: result.decision,
    latency_ms: result.latency_ms,
  }
}

export function toAlertItem(result) {
  const txn = result.transaction || {}
  return {
    amount: txn.transaction_amount || 0,
    category: txn.category || '',
    simulation_mode: result.simulation_mode,
    time: txn.transaction_time || '',
    fraud_probability: result.fraud_probability,
    reasoning: result.reasoning || '',
  }
}