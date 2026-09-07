const DEFAULT_COLORS = ['grad', 'grad', 'warn', 'warn', 'red']

export default function BarChart({ data }) {
  if (!data || Object.keys(data).length === 0) return null

  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 5)
  const max = entries[0][1]

  return (
    <div className="bar-chart">
      {entries.map(([cat, count], i) => {
        const pct = max > 0 ? (count / max) * 100 : 0
        const color = DEFAULT_COLORS[i] || 'grad'
        const label =
          cat.length > 16
            ? `${cat.replace(/_/g, ' ').slice(0, 16)}…`
            : cat.replace(/_/g, ' ')
        return (
          <div className="bar-row" key={cat}>
            <div className="bar-label">{label}</div>
            <div className="bar-track">
              <div
                className={`bar-fill ${color}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <div className="bar-val">{count}</div>
          </div>
        )
      })}
    </div>
  )
}