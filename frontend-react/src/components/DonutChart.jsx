export default function DonutChart({ pct, size = 110 }) {
  const radius = 38
  const circ = 2 * Math.PI * radius
  const filled = (Math.min(pct, 100) / 100) * circ

  return (
    <div className="donut-wrap">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg
          className="donut-svg"
          width={size}
          height={size}
          viewBox="0 0 100 100"
        >
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="rgba(52,211,153,0.1)"
            strokeWidth="12"
          />
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="none"
            stroke="#fb7185"
            strokeWidth="12"
            strokeDasharray={`${filled.toFixed(1)} ${circ.toFixed(1)}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--danger)', lineHeight: 1 }}>
            {pct.toFixed(1)}%
          </div>
          <div style={{ fontSize: 9, color: 'var(--muted)', letterSpacing: '0.1em', textTransform: 'uppercase', marginTop: 4 }}>
            fraud
          </div>
        </div>
      </div>
      <div className="donut-legend">
        <div className="legend-item">
          <span className="legend-dot red" /> Blocked
        </div>
        <div className="legend-item">
          <span className="legend-dot green" /> Approved
        </div>
      </div>
    </div>
  )
}