export default function SystemMonitor({ health, sseState, lastRefresh }) {
  const rows = [
    { label: 'API STATUS', value: health ? '● ONLINE' : '● OFFLINE', cls: health ? 'ok' : 'err' },
    { label: 'QUEUE SIZE', value: health ? String(health.queue_size ?? '—') : '—', cls: '' },
    { label: 'RESULTS STORED', value: health ? String(health.results_stored ?? '—') : '—', cls: '' },
    { label: 'LAST REFRESH', value: lastRefresh || '—', cls: '' },
    {
      label: 'SSE STREAM',
      value:
        sseState === 'connected'
          ? '● CONNECTED'
          : sseState === 'error'
            ? '● RECONNECTING…'
            : 'connecting…',
      cls: sseState === 'connected' ? 'ok' : sseState === 'error' ? 'warn' : '',
    },
  ]

  return (
    <div className="monitor-card card">
      <div className="section-title" style={{ marginBottom: 12 }}>
        system monitor
      </div>
      {rows.map((r) => (
        <div className="monitor-row" key={r.label}>
          <span className="monitor-label">{r.label}</span>
          <span className={`monitor-val ${r.cls ? `status-${r.cls}` : ''}`}>{r.value}</span>
        </div>
      ))}
    </div>
  )
}