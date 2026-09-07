import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { ShieldLogo } from './ShieldLogo'

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/simulator', label: 'Simulator' },
  { to: '/dashboard', label: 'Dashboard' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <nav className="navbar">
      <div
        className="nav-logo"
        onClick={() => {
          setOpen(false)
          navigate('/')
        }}
      >
        <ShieldLogo />
        FRAUD<span className="logo-accent">SHIELD</span>
      </div>

      <div className={`nav-links ${open ? 'open' : ''}`}>
        {LINKS.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            onClick={() => setOpen(false)}
          >
            {l.label}
          </NavLink>
        ))}
      </div>

      <div className="nav-right">
        <div className="live-badge">
          <span className="live-dot" />
          LIVE
        </div>
        <button
          className="nav-burger"
          aria-label="Toggle menu"
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="4" y1="7" x2="20" y2="7" />
            <line x1="4" y1="12" x2="20" y2="12" />
            <line x1="4" y1="17" x2="20" y2="17" />
          </svg>
        </button>
      </div>
    </nav>
  )
}