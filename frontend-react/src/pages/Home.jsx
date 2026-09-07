import { Link } from 'react-router-dom'
import Ticker from '../components/Ticker'

const STATS = [
  { value: '98ms', label: 'avg latency' },
  { value: '4', label: 'attack modes' },
  { value: 'XGB', label: 'ML model' },
  { value: 'LLM', label: 'reasoning' },
]

const FEATURES = [
  {
    num: '01',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 12h4l3-9 4 18 3-9h4" />
      </svg>
    ),
    title: 'Streaming Predictions',
    desc: 'Every transaction flows through an in-memory queue, processed one-by-one with results pushed live via Server-Sent Events.',
  },
  {
    num: '02',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 19V5m0 14h16M4 9l4 4 4-6 4 3 4-5" />
      </svg>
    ),
    title: 'XGBoost + Feature Eng.',
    desc: 'Haversine distance, log-amount transforms, night-hour flags, and velocity signals feed a model trained with class-imbalance handling.',
  },
  {
    num: '03',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12a9 9 0 1 1-9-9" strokeDasharray="2 2" />
        <path d="M12 7v5l3 3" />
      </svg>
    ),
    title: 'LLM Explanations',
    desc: 'Every blocked transaction gets a structured fraud analysis report from Groq LLaMA — decision, risk factors, recommended action.',
  },
]

export default function Home() {
  return (
    <>
      <div className="bg-aurora" />
      <div className="bg-grid" />

      <section className="hero">
        <div className="hero-orbs">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
        </div>
        <div className="hero-badge anim-fade-up">
          <span className="live-dot" />
          System online — real-time detection active
        </div>
        <h1 className="anim-fade-up" style={{ animationDelay: '0.1s' }}>
          FRAUD
          <span className="grad-line">SHIELD AI</span>
        </h1>
        <p className="hero-sub anim-fade-up" style={{ animationDelay: '0.2s' }}>
          Real-time financial fraud detection powered by XGBoost + LLM
          reasoning. Streaming ML predictions at sub-100ms latency.
        </p>
        <div className="hero-actions anim-fade-up" style={{ animationDelay: '0.3s' }}>
          <Link to="/simulator" className="btn btn-primary">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Run Simulation
          </Link>
          <Link to="/dashboard" className="btn btn-ghost">
            View Dashboard
          </Link>
        </div>
      </section>

      <Ticker />

      <section className="stats-strip">
        {STATS.map((s) => (
          <div className="stat-tile" key={s.label}>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </section>

      <section className="features">
        <div className="features-head">
          <div className="kicker" style={{ justifyContent: 'center' }}>
            how it works
          </div>
          <h2>Three layers of protection</h2>
          <p>Streaming inference, engineered features, and AI reasoning.</p>
        </div>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.num}>
              <div className="feature-num">{f.num} / PIPELINE</div>
              <div className="feature-icon">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}