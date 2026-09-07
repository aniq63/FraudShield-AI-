export default function EmptyState({ icon = '⬡', text }) {
  return (
    <div className="empty">
      <span className="empty-icon">{icon}</span>
      <span className="empty-text">{text}</span>
    </div>
  )
}