export default function StatCard({
  label,
  value,
  sub,
  subClass,
  variant,
  badge,
}) {
  const cls = [`stat-card card`]
  if (variant) cls.push(variant)
  return (
    <div className={cls.join(' ')}>
      {badge && <span className="stat-badge">{badge}</span>}
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${variant ? variant : 'grad'}`}>{value}</div>
      {sub && <div className={`stat-sub ${subClass || ''}`}>{sub}</div>}
    </div>
  )
}