const MODES = [
  { key: 'normal', label: 'normal' },
  { key: 'stolen_card', label: 'stolen card' },
  { key: 'geo_attack', label: 'geo attack' },
  { key: 'velocity_burst', label: 'velocity burst' },
]

export function ModeGrid({ breakdown }) {
  return (
    <div className="mode-grid">
      {MODES.map((m) => (
        <div className="mode-cell" key={m.key}>
          <div className="mode-cell-label">{m.label}</div>
          <div className="mode-cell-val">
            {(breakdown?.[m.key] || 0).toLocaleString()}
          </div>
        </div>
      ))}
    </div>
  )
}