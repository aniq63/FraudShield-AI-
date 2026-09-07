const W = 300
const H = 48
const PAD = 4

export default function Sparkline({ data }) {
  if (!data || data.length < 2) {
    return (
      <div className="spark-wrap">
        <svg className="spark-svg" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          <line x1="0" y1={H - PAD - 12} x2={W} y2={H - PAD - 12} className="spark-zero" />
        </svg>
      </div>
    )
  }

  const maxV = Math.max(...data, 10)
  const points = data
    .map((v, i) => {
      const x = PAD + (i / (data.length - 1)) * (W - PAD * 2)
      const y = H - PAD - (v / maxV) * (H - PAD * 2)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <div className="spark-wrap">
      <svg className="spark-svg" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        <line x1="0" y1={H - PAD - 12} x2={W} y2={H - PAD - 12} className="spark-zero" />
        <polyline
          points={points}
          fill="none"
          stroke="url(#sparkGrad)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  )
}