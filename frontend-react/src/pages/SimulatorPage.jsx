import React, { useState, useRef, useEffect } from 'react';
import { runSimulation, resetDashboard, createSSEStream } from '../utils/api';
import '../styles/SimulatorPage.css';

function SimulatorPage() {
  const [mode, setMode] = useState('normal');
  const [count, setCount] = useState(100);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [status, setStatus] = useState('idle');
  const sseRef = useRef(null);

  const startSimulation = async () => {
    if (running) return;
    
    setRunning(true);
    setResults([]);
    setProgress({ done: 0, total: count });
    setStatus('running');

    try {
      // Start simulation on backend
      await runSimulation({
        mode,
        count,
      });

      // Open SSE stream
      const url = import.meta.env.VITE_API_URL || 'https://fraudshield-ai-production-78c0.up.railway.app';
      sseRef.current = new EventSource(`${url}/simulate/stream`);

      sseRef.current.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'result') {
          setResults((prev) => [data, ...prev]);
          setProgress((prev) => ({ ...prev, done: prev.done + 1 }));
        }
      };

      sseRef.current.onerror = () => {
        setStatus('error');
        setRunning(false);
        if (sseRef.current) {
          sseRef.current.close();
          sseRef.current = null;
        }
      };
    } catch (error) {
      console.error('Simulation error:', error);
      setStatus('error');
      setRunning(false);
    }

    // Stop after count results
    const checkInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev.done >= count) {
          clearInterval(checkInterval);
          setStatus('done');
          setRunning(false);
          if (sseRef.current) {
            sseRef.current.close();
            sseRef.current = null;
          }
          return prev;
        }
        return prev;
      });
    }, 500);
  };

  const handleReset = async () => {
    setResults([]);
    setProgress({ done: 0, total: 0 });
    setStatus('idle');
    setRunning(false);
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    try {
      await resetDashboard();
    } catch (error) {
      console.error('Reset error:', error);
    }
  };

  useEffect(() => {
    return () => {
      if (sseRef.current) {
        sseRef.current.close();
      }
    };
  }, []);

  return (
    <div className="simulator-page">
      <div className="page-header">
        <div>
          <div className="page-tag">SIMULATOR</div>
          <h1>Transaction Simulator</h1>
          <p className="page-desc">
            Test your fraud detection system by generating synthetic transactions across different attack modes.
          </p>
        </div>
      </div>

      <div className="sim-layout">
        {/* Control Panel */}
        <div className="control-panel">
          <div>
            <div className="panel-section-title">Attack Mode</div>
            <div className="mode-grid">
              {['normal', 'stolen_card', 'geo_attack', 'velocity_burst'].map((m) => (
                <button
                  key={m}
                  className={`mode-btn ${mode === m ? 'selected' : ''}`}
                  onClick={() => setMode(m)}
                  disabled={running}
                >
                  <div className="mode-label">{m.replace('_', ' ')}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="panel-section-title">Transaction Count</div>
            <div className="slider-wrap">
              <div className="slider-row">
                <label>Transactions</label>
                <span className="slider-val">{count}</span>
              </div>
              <input
                type="range"
                min="10"
                max="1000"
                step="10"
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                disabled={running}
              />
            </div>
          </div>

          <button
            className="run-btn"
            onClick={startSimulation}
            disabled={running}
          >
            {running ? 'Running...' : 'Run Simulation'}
          </button>
          <button
            className="reset-btn"
            onClick={handleReset}
            disabled={running}
          >
            Reset
          </button>

          <div className="status-bar">
            <div className={`status-dot ${status}`}></div>
            <div className="status-text">
              {status === 'idle' && 'Idle — Ready to run'}
              {status === 'running' && `Running — ${progress.done} / ${progress.total}`}
              {status === 'done' && `Complete — ${progress.done} transactions processed`}
              {status === 'error' && 'Error — Check API server'}
            </div>
          </div>

          {progress.total > 0 && (
            <div className="progress-wrap">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${(progress.done / progress.total) * 100}%` }}
                ></div>
              </div>
              <div className="progress-label">{progress.done} / {progress.total}</div>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="results-section">
          {results.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon">🚀</span>
              <span className="empty-text">Run simulation to see results</span>
            </div>
          ) : (
            <div className="results-wrap">
              <div className="results-header">
                <span className="results-count">{results.length} Results</span>
              </div>
              {results.map((result, i) => {
                const isBlocked = result.decision === 'BLOCKED';
                const prob = (result.fraud_probability || 0) * 100;
                return (
                  <div key={i} className={`result-card ${isBlocked ? 'blocked' : 'approved'}`}>
                    <div className="rc-header">
                      <div className="rc-meta">
                        <strong>${result.transaction?.transaction_amount?.toLocaleString()}</strong>
                        <span className={`tag ${isBlocked ? 'tag-blocked' : 'tag-approved'}`}>
                          {result.decision}
                        </span>
                      </div>
                      <div className="rc-score">
                        <div className={`score-val ${prob >= 50 ? 'high' : 'low'}`}>{prob.toFixed(1)}%</div>
                        <div className="score-label">fraud score</div>
                      </div>
                    </div>
                    {result.reasoning && (
                      <div className="rc-reasoning">{result.reasoning}</div>
                    )}
                    <div className="rc-latency">⏱ {result.latency_ms}ms</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SimulatorPage;
