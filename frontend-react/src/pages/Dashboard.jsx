import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useStream } from '../hooks/useStream'
import StatCard from '../components/StatCard'
import DonutChart from '../components/DonutChart'
import BarChart from '../components/BarChart'
import Sparkline from '../components/Sparkline'
import { ModeGrid } from '../components/ModeGrid'
import SystemMonitor from '../components/SystemMonitor'
import EmptyState from '../components/EmptyState'
import {
  clampProb,
  cleanKey,
  fmtMoney,
  fmtNum,
  probColor,
  shortTime,
  toAlertItem,
  toFeedRow,
} from '../utils/format'

const MAX_FEED_ROWS = 60
const MAX_ALERTS = 30

function ProbBadge({ prob }) {
  const v = clampProb(prob)
  const color = probColor(v)
  return (
    <div className="prob-cell">
      <span className="prob-badge" style={{ color }}>
        {v.toFixed(3)}
      </span>
      <div className="prob-track">
        <div
          className="prob-fill-inline"
          style={{ width: `${Math.round(v * 100)}%`, background: color }}
        />
      </div>
    </div>
  )
}

function FeedRow({ r, isNew }) {
  const amt = fmtMoney(r.amount)
  const cat = cleanKey(r.category)
  const mode = cleanKey(r.simulation_mode)
  const blocked = r.decision === 'BLOCKED'
  return (
    <tr className={isNew ? 'new-row' : ''}>
      <td className="cell-time">{shortTime(r.time)}</td>
      <td className="cell-amount">{amt}</td>
      <td className="cell-cat">{cat}</td>
      <td>
        <ProbBadge prob={r.fraud_probability} />
      </td>
      <td>
        <span className="tag tag-mode">{mode}</span>
      </td>
      <td>
        <span className={`tag ${blocked ? 'tag-blocked' : 'tag-approved'}`}>
          {r.decision}
        </span>
      </td>
      <td className="cell-latency">{Math.round(r.latency_ms || 0)}</td>
    </tr>
  )
}

function AlertCard({ a }) {
  const [open, setOpen] = useState(false)
  const prob = clampProb(a.fraud_probability)
  const hasReasoning = Boolean(a.reasoning)
  return (
    <div
      className="alert-card"
      onClick={() => hasReasoning && setOpen((v) => !v)}
    >
      <div className="alert-header">
        <div className="alert-amount">{fmtMoney(a.amount)}</div>
        <div className="alert-score">{(prob * 100).toFixed(1)}%</div>
      </div>
      <div className="alert-meta">
        <span>{cleanKey(a.category)}</span>·<span>{cleanKey(a.simulation_mode)}</span>·
        <span>{shortTime(a.time)}</span>
      </div>
      <span className="tag tag-blocked">Blocked</span>
      {hasReasoning && open && <div className="alert-reasoning">{a.reasoning}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [feed, setFeed] = useState([])
  const [alerts, setAlerts] = useState([])
  const [alertCount, setAlertCount] = useState(0)
  const [feedCount, setFeedCount] = useState(0)
  const [health, setHealth] = useState(null)
  const [sseState, setSseState] = useState('connecting')
  const [lastRefresh, setLastRefresh] = useState('—')
  const [fraudRateHistory, setFraudRateHistory] = useState([])
  const feedRef = useRef([])
  const alertsRef = useRef([])

  const checkHealth = useCallback(async () => {
    try {
      const d = await api.getHealth()
      setHealth(d)
      setLastRefresh(new Date().toLocaleTimeString())
    } catch {
      setHealth(null)
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const d = await api.getStats()
      setStats(d)
      setFraudRateHistory((prev) => {
        const next = [...prev, d.fraud_rate_pct]
        if (next.length > 40) next.shift()
        return next
      })
    } catch {
      /* ignore */
    }
  }, [])

  const fetchFeedAndAlerts = useCallback(async () => {
    try {
      const [f, a] = await Promise.all([api.getFeed(50), api.getAlerts(20)])
      if (f.feed?.length) {
        feedRef.current = f.feed
        setFeed(f.feed)
        setFeedCount(f.count)
      }
      if (a.alerts?.length) {
        alertsRef.current = a.alerts
        setAlerts(a.alerts)
        setAlertCount(a.count)
      }
    } catch {
      /* ignore */
    }
  }, [])

  const fetchAll = useCallback(() => {
    Promise.all([fetchStats(), fetchFeedAndAlerts(), checkHealth()]).catch(() => {})
  }, [fetchStats, fetchFeedAndAlerts, checkHealth])

  useEffect(() => {
    fetchAll()
    const iv = setInterval(fetchStats, 4000)
    return () => clearInterval(iv)
  }, [fetchAll, fetchStats])

  const onResult = useCallback(({ type, data }) => {
    if (type === 'connected') setSseState('connected')
    else if (type === 'sse-error') setSseState('error')
    else if (type === 'result') {
      const row = toFeedRow(data)
      feedRef.current = [row, ...feedRef.current].slice(0, MAX_FEED_ROWS)
      setFeed(feedRef.current)
      setFeedCount((c) => c + 1)

      if (data.decision === 'BLOCKED') {
        alertsRef.current = [toAlertItem(data), ...alertsRef.current].slice(0, MAX_ALERTS)
        setAlerts(alertsRef.current)
        setAlertCount((c) => c + 1)
      }
      fetchStats()
      checkHealth()
    }
  }, [fetchStats, checkHealth])

  useStream(onResult)

  const d = stats
  const modes = d?.mode_breakdown || {}

  return (
    <div className="dash-page">
      <div className="bg-aurora" />
      <div className="bg-grid" />

      <div className="dash-header">
        <div>
          <div className="dash-title">Operational Dashboard</div>
          <div className="dash-subtitle">
            Live view of model performance, transactions, and alerts
          </div>
        </div>
        <button className="btn btn-ghost" onClick={fetchAll}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 12a9 9 0 1 1-2.6-6.4M21 3v6h-6" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="stat-grid">
        <StatCard
          label="total transactions"
          value={d ? fmtNum(d.total_transactions) : '—'}
          sub="this session"
          badge="SESSION"
        />
        <StatCard
          variant="danger"
          label="fraud rate"
          value={d ? `${d.fraud_rate_pct.toFixed(1)}%` : '—'}
          sub={
            d
              ? `${d.fraud_rate_vs_normal_pct >= 0 ? '↑' : '↓'} ${Math.abs(
                  d.fraud_rate_vs_normal_pct,
                ).toFixed(1)}% vs normal`
              : 'vs normal baseline'
          }
          subClass={d ? (d.fraud_rate_vs_normal_pct >= 0 ? 'up' : 'down') : ''}
        />
        <StatCard
          variant="danger"
          label="blocked"
          value={d ? fmtNum(d.blocked_count) : '—'}
          sub={d ? `${fmtNum(d.approved_count)} approved` : '— approved'}
          subClass="down"
        />
        <StatCard
          variant="success"
          label="avg latency"
          value={d ? `${d.avg_latency_ms.toFixed(0)}ms` : '—'}
          sub={d ? `p99: ${d.p99_latency_ms.toFixed(0)}ms` : 'p99: —'}
        />
      </div>

      <div className="chart-row">
        <div className="chart-card card">
          <div className="section-title">fraud vs approved</div>
          <DonutChart pct={d?.fraud_rate_pct || 0} />
        </div>

        <div className="chart-card card">
          <div className="section-title">top categories</div>
          <BarChart data={d?.top_categories} />
          {(!d || !d.top_categories || Object.keys(d.top_categories).length === 0) && (
            <EmptyState text="Run a simulation first" />
          )}
        </div>

        <div className="chart-card card">
          <div className="section-title">mode breakdown</div>
          <ModeGrid breakdown={modes} />
          <div className="section-title" style={{ marginTop: 18 }}>
            fraud rate over time
          </div>
          <Sparkline data={fraudRateHistory} />
        </div>
      </div>

      <div className="dash-cols">
        <div className="left-col">
          <div className="feed-wrap card">
            <div className="feed-hd">
              <div className="section-title">
                live transaction feed
                <span className="count-pill">{feedCount}</span>
              </div>
              <Link
                to="/simulator"
                className="mono"
                style={{ fontSize: 10, color: 'var(--cyan)', letterSpacing: '0.08em' }}
              >
                + RUN SIMULATION →
              </Link>
            </div>
            {feed.length > 0 ? (
              <div className="feed-scroll">
                <table className="feed-table">
                  <thead>
                    <tr>
                      <th>time</th>
                      <th>amount</th>
                      <th>category</th>
                      <th>score</th>
                      <th>mode</th>
                      <th>decision</th>
                      <th>ms</th>
                    </tr>
                  </thead>
                  <tbody>
                    {feed.map((r, i) => (
                      <FeedRow key={`${r.time}-${i}`} r={r} isNew={i === 0} />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ padding: 14 }}>
                <EmptyState
                  icon="—"
                  text={`No transactions yet.\nRun a simulation to see live data.`}
                />
              </div>
            )}
          </div>

          <SystemMonitor
            health={health}
            sseState={sseState}
            lastRefresh={lastRefresh}
          />
        </div>

        <div className="right-col">
          <div className="alerts-panel card">
            <div className="alerts-hd">
              <div className="section-hd" style={{ margin: 0 }}>
                <div className="section-title" style={{ color: 'var(--danger)' }}>
                  <span className="alert-marker" aria-hidden="true" /> fraud alerts
                  <span className="count-pill danger">{alertCount}</span>
                </div>
                <span className="mono" style={{ fontSize: 9, color: 'var(--muted)' }}>
                  click to expand
                </span>
              </div>
            </div>
            <div className="alerts-scroll">
              {alerts.length > 0 ? (
                alerts.map((a, i) => <AlertCard key={`${a.time}-${i}`} a={a} />)
              ) : (
                <EmptyState
                  icon="—"
                  text={`No fraud alerts yet.\nRun an attack simulation\nto see blocked transactions.`}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}