export function ShieldLogo({ size = 22 }) {
  return (
    <svg
      className="shield-svg"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="url(#shieldGrad)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <defs>
        <linearGradient id="shieldGrad" x1="0" y1="0" x2="24" y2="24">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#22d3ee" />
        </linearGradient>
      </defs>
      <path d="M12 2L3 5.5V11c0 5.25 3.8 10 9 11 5.2-1 9-5.75 9-11V5.5L12 2z" />
      <path d="M8.5 12l2.5 2.5 4.5-4.5" />
    </svg>
  )
}