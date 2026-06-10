import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../styles/HomePage.css';

function HomePage() {
  const [liveData, setLiveData] = useState([
    { txn: '#18823', amount: '$4,200', category: 'travel', status: 'BLOCKED', score: '0.97' },
    { txn: '#18824', amount: '$38', category: 'grocery_pos', status: 'APPROVED', score: '0.02' },
    { txn: '#18825', amount: '$7,419', category: 'shopping_net', status: 'BLOCKED', score: '0.88' },
    { txn: '#18826', amount: '$112', category: 'food_dining', status: 'APPROVED', score: '0.05' },
    { txn: '#18827', amount: '$5,779', category: 'misc_net', status: 'BLOCKED', score: '0.76' },
    { txn: '#18828', amount: '$22', category: 'gas_transport', status: 'APPROVED', score: '0.01' },
  ]);

  useEffect(() => {
    // Rotate ticker
    const interval = setInterval(() => {
      setLiveData((prev) => [...prev.slice(1), prev[0]]);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="home-page">
      <section className="hero fade-up">
        <div className="hero-badge">
          <span className="badge-dot"></span>
          SYSTEM ONLINE — REAL-TIME DETECTION ACTIVE
        </div>
        <h1>FRAUD<em>SHIELD AI</em></h1>
        <p className="hero-sub">
          Real-time financial fraud detection powered by XGBoost + LLM reasoning. 
          Streaming ML predictions at sub-100ms latency.
        </p>
        <div className="hero-actions">
          <Link to="/simulator" className="btn btn-primary">
            <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Run Simulation
          </Link>
          <Link to="/dashboard" className="btn btn-ghost">
            View Dashboard
          </Link>
        </div>
      </section>

      {/* Live Ticker */}
      <div className="ticker">
        <div className="ticker-inner">
          {liveData.map((item, i) => (
            <span key={i} className="ticker-item">
              TXN {item.txn} · {item.amount} · {item.category} ·{' '}
              <span className={`t-${item.status.toLowerCase()}`}>
                {item.status} {item.score}
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* Stats Strip */}
      <div className="stats-strip">
        <div className="stat-item">
          <div className="stat-value">98ms</div>
          <div className="stat-label">avg latency</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">4</div>
          <div className="stat-label">attack modes</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">XGB</div>
          <div className="stat-label">ML model</div>
        </div>
        <div className="stat-item">
          <div className="stat-value">LLM</div>
          <div className="stat-label">reasoning</div>
        </div>
      </div>

      {/* Features */}
      <div className="features">
        <div className="feature">
          <div className="feature-num">01 / PIPELINE</div>
          <h3>Streaming Predictions</h3>
          <p>Every transaction flows through an in-memory queue, processed one-by-one with results pushed live via Server-Sent Events.</p>
        </div>
        <div className="feature">
          <div className="feature-num">02 / MODEL</div>
          <h3>XGBoost + Feature Eng.</h3>
          <p>Haversine distance, log-amount transforms, night-hour flags, and velocity signals feed a model trained with class-imbalance handling.</p>
        </div>
        <div className="feature">
          <div className="feature-num">03 / REASONING</div>
          <h3>LLM Explanations</h3>
          <p>Every blocked transaction gets a structured fraud analysis report from Groq LLaMA — decision, risk factors, recommended action.</p>
        </div>
      </div>

      <footer>FRAUDSHIELD AI · BUILT FOR REAL-TIME FRAUD DETECTION · © 2026</footer>
    </div>
  );
}

export default HomePage;
