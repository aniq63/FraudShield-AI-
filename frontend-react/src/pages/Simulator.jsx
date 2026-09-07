import { useCallback, useRef, useState } from 'react'
import { api } from '../api/client'
import { useStream } from '../hooks/useStream'
import EmptyState from '../components/EmptyState'
import { cleanKey, esc, fmtMoney } from '../utils/format'

const MODES = [
  { key: 'normal', icon: '🟢', label: 'Normal', desc: 'Baseline transaction behaviour' },
  { key: 'stolen_card', icon: '💳', label: 'Stolen Card', desc: 'High-value irregular purchases' },
  { key: 'geo_attack', icon: '🌍', label: 'Geo Attack', desc: 'Impossible location anomaly' },
  { key: 'velocity_burst', icon: '⚡', label: 'Velocity Burst', desc: 'Rapid late-night transactions' },
]

function ResultCard({ r }) {
  const isBlocked = r.decision === 'BLOCKED'
  const prob = r.fraud_probability || 0
  const txn = r.transaction || {}
  const probPct = (prob * 100).toFixed(1)
  return (
    <div className={`result-card ${isBlocked ? 'blocked' : 'approved'} anim-slide-in`}>
      <div className="rc-header">
        <div className="rc-meta">
          <strong>
            {fmtMoney(txn.transaction_amount)} · {cleanKey(txn.category)}
          </strong>
          <div className="rc-tags">
            <span className={`tag ${isBlocked ? 'tag-blocked' : 'tag-approved'}`}>
              {r.decision}
            </span>
            <span className="tag tag-mode">{cleanKey(r.simulation_mode)}</span>
          </div>
        </div>
        <div className="rc-score">
          <div className={`score-val ${prob >= 0.5 ? 'high' : 'low'}`}>{probPct}%</div>
          <div className="score-label">fraud score</div>
        </div>
      </div>
      {r.reasoning && <div className="rc-reasoning">{esc(r.reasoning)}</div>}
      <div className="rc-latency">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M12 6v6l4 2" />
        </svg>
        {r.latency_ms}ms
      </div>
    </div>
  )
}

export default function Simulator() {
  const [mode, setMode] = useState('normal')
  const [count, setCount] = useState(10)
  const [state, setState] = useState('idle') // idle | running | done | error
  const [statusMsg, setStatusMsg] = useState('Idle — configure and run a simulation')
  const [rawTxns, setRawTxns] = useState([])
  const [results, setResults] = useState([])
  const [progress, setProgress] = useState({ done: 0, total: 0 })
  const [toast, setToast] = useState(null)
  const totalRef = useRef(0)
  const receivedRef = useRef(0)
  const runningRef = useRef(false)

  const handleResult = useCallback(({ type, data }) => {
    if (type === 'result') {
      receivedRef.current += 1
      setProgress({ done: receivedRef.current, total: totalRef.current })
      setResults((prev) => [{ data, idx: receivedRef.current - 1 }, ...prev])

      if (receivedRef.current >= totalRef.current) {
        runningRef.current = false
        setState('done')
        setStatusMsg(`Complete — ${totalRef.current} transactions processed`)
      }
    }
  }, [])

  useStream(handleResult)

  const runSimulation = async () => {
    const n = count
    runningRef.current = true
    receivedRef.current = 0
    totalRef.current = n
    setRawTxns([])
    setResults([])
    setToast(null)
    setState('running')
    setStatusMsg(`Generating ${n} transactions…`)
    setProgress({ done: 0, total: n })

    try {
      const data = await api.simulate(mode, n)
      setRawTxns(data.transactions)
      setStatusMsg(`Predicting ${n} transactions…`)
    } catch (e) {
      runningRef.current = false
      setState('error')
      setStatusMsg(`Error: ${e.message}`)
      setToast(e.message)
    }
  }

  const resetSession = async () => {
    runningRef.current = false
    receivedRef.current = 0
    totalRef.current = 0
    setRawTxns([])
    setResults([])
    setProgress({ done: 0, total: 0 })
    setState('idle')
    setStatusMsg('Idle — session cleared')
    setToast(null)
    try {
      await api.reset()
    } catch {
      /* ignore */
    }
  }

  const pendingMap = new Map(
    rawTxns.map((t, i) => {
      const res = results.find((r) => r.idx === i)
      return [i, res ? res.data : null]
    }),
  )

  return (
    <div className="sim-page">
      <div className="bg-aurora" />
      <div className="bg-grid" />

      <div className="sim-header">
        <div className="kicker">// transaction simulator</div>
        <div className="sim-title" style={{ marginTop: 12 }}>
          Attack Simulator
        </div>
        <p className="sim-desc">
          Generate synthetic transactions and exercise the FraudShield
          prediction pipeline. Choose an attack mode and hit run — results
          stream back live with fraud scores and LLM reasoning.
        </p>
      </div>

      <div className="sim-layout">
        <div className="control-panel card">
          <div>
            <div className="panel-section-title">
              <span>01</span> — select attack mode
            </div>
            <div className="mode-picker">
              {MODES.map((m) => (
                <button
                  key={m.key}
                  className={`mode-btn ${mode === m.key ? 'selected' : ''}`}
                  onClick={() => setMode(m.key)}
                  disabled={state === 'running'}
                >
                  <span className="mode-icon">{m.icon}</span>
                  <span className="mode-label">{m.label}</span>
                  <span className="mode-desc">{m.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="slider-wrap">
            <div className="panel-section-title">
              <span>02</span> — number of transactions
            </div>
            <div className="slider-row">
              <span className="slider-label">Count</span>
              <span className="slider-val">{count}</span>
            </div>
            <input
              type="range"
              min="1"
              max="100"
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value))}
              disabled={state === 'running'}
            />
            <div className="range-scale">
              <span>1</span>
              <span>25</span>
              <span>50</span>
              <span>75</span>
              <span>100</span>
            </div>
          </div>

          <div>
            <div className="panel-section-title">
              <span>03</span> — execute
            </div>
            <button
              className="btn btn-primary"
              style={{ width: '100%' }}
              onClick={runSimulation}
              disabled={state === 'running'}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              {state === 'running' ? 'Running…' : 'Run Simulation'}
            </button>
          </div>

          <button
            className="btn btn-danger-ghost"
            style={{ width: '100%', fontSize: 13 }}
            onClick={resetSession}
            disabled={state === 'running'}
          >
            ↺ Clear Session
          </button>
        </div>

        <div className="sim-right">
          <div className="status-bar">
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span className={`status-dot ${state === 'running' ? 'running' : state === 'done' ? 'done' : state === 'error' ? 'error' : ''}`} />
              <span className={`state-${state}`}>{statusMsg}</span>
            </div>
            {state === 'running' && (
              <span style={{ color: 'var(--muted)', fontSize: 12 }}>
                {progress.done} / {progress.total}
              </span>
            )}
            {state === 'done' && (
              <span className="state-done" style={{ fontSize: 12 }}>
                ✓ {progress.total} processed
              </span>
            )}
          </div>

          {state === 'running' && (
            <div className="progress-wrap">
              <div className="progress-header">
                <span>Processing predictions</span>
                <span>
                  {progress.done} / {progress.total}
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${(progress.done / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}

          {rawTxns.length > 0 && (
            <div>
              <div className="section-title" style={{ marginBottom: 10 }}>
                generated transactions
                <span className="count-pill">{rawTxns.length}</span>
              </div>
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>amount</th>
                      <th>category</th>
                      <th>hour</th>
                      <th>gender</th>
                      <th>mode</th>
                      <th>prediction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rawTxns.map((t, i) => {
                      const res = pendingMap.get(i)
                      return (
                        <tr key={i}>
                          <td style={{ color: 'var(--muted)' }}>{i + 1}</td>
                          <td className="amt">{fmtMoney(t.transaction_amount)}</td>
                          <td>{t.category || '—'}</td>
                          <td>{t.transaction_hour != null ? `${t.transaction_hour}:00` : '—'}</td>
                          <td>{t.buyer_gender || '—'}</td>
                          <td>
                            <span className="tag tag-mode">{cleanKey(t.simulation_mode)}</span>
                          </td>
                          <td>
                            {res ? (
                              <span
                                className={`tag ${res.decision === 'BLOCKED' ? 'tag-blocked' : 'tag-approved'}`}
                              >
                                {res.decision} {(res.fraud_probability || 0).toFixed(3)}
                              </span>
                            ) : (
                              <span className="tag tag-pending">pending…</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div>
              <div className="section-title" style={{ marginBottom: 10 }}>
                prediction results
                <span className="count-pill">{results.length}</span>
              </div>
              <div className="results-wrap">
                {results.map((r) => (
                  <ResultCard key={`${r.data.transaction?.transaction_time}-${r.idx}`} r={r.data} />
                ))}
              </div>
            </div>
          )}

          {state !== 'running' && rawTxns.length === 0 && results.length === 0 && (
            <EmptyState
              icon="⬡"
              text={'No simulation running.\nConfigure attack mode and hit RUN.'}
            />
          )}
        </div>
      </div>

      {toast && (
        <div className="toast" onClick={() => setToast(null)}>
          {toast}
        </div>
      )}
    </div>
  )
}