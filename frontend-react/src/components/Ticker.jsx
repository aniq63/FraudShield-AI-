const BASE_ITEMS = [
  { id: 18823, amt: 4200, cat: 'travel', status: 'BLOCKED 0.97' },
  { id: 18824, amt: 38, cat: 'grocery_pos', status: 'APPROVED 0.02' },
  { id: 18825, amt: 7419, cat: 'shopping_net', status: 'BLOCKED 0.88' },
  { id: 18826, amt: 112, cat: 'food_dining', status: 'APPROVED 0.05' },
  { id: 18827, amt: 5779, cat: 'misc_net', status: 'BLOCKED 0.76' },
  { id: 18828, amt: 22, cat: 'gas_transport', status: 'APPROVED 0.01' },
  { id: 18829, amt: 9100, cat: 'travel', status: 'BLOCKED 0.94' },
]

function Item({ it }) {
  const blocked = it.status.startsWith('BLOCKED')
  return (
    <span className="ticker-item">
      TXN #{it.id} · ${it.amt.toLocaleString()} · {it.cat} ·{' '}
      <span className={blocked ? 't-blocked' : 't-approved'}>{it.status}</span>
    </span>
  )
}

export default function Ticker() {
  const doubled = [...BASE_ITEMS, ...BASE_ITEMS]
  return (
    <div className="ticker">
      <div className="ticker-track">
        {doubled.map((it, i) => (
          <Item key={`${it.id}-${i}`} it={it} />
        ))}
      </div>
    </div>
  )
}