import React, { useState, useEffect, useCallback } from 'react';
import { checkHealth, getDashboardStats, getFeed, getAlerts } from '../utils/api';
import '../styles/DashboardPage.css';

function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [feed, setFeed] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAllData = useCallback(async () => {
    try {
      const [healthRes, statsRes, feedRes, alertsRes] = await Promise.all([
        checkHealth().catch(() => null),
        getDashboardStats().catch(() => null),
        getFeed().catch(() => null),
        getAlerts().catch(() => null),
      ]);

      if (healthRes?.data) setHealth(healthRes.data);
      if (statsRes?.data) setStats(statsRes.data);
      if (feedRes?.data) setFeed(feedRes.data);
      if (alertsRes?.data) setAlerts(alertsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 4000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  if (loading) {
    return <div className="dashboard-page"><div className="loading">Loading dashboard data...</div></div>;
  }

  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <button onClick={fetchAllData} className="refresh-btn">Refresh</button>
      </div>

      {/* Stat Cards */}
      <div className="stat-row">
        <div className="stat-card">
          <div className="stat-label">Total Transactions</div>
          <div className="stat-value">{stats?.total_transactions?.toLocaleString() || '—'}</div>
        </div>
        <div className="stat-card danger">
          <div className="stat-label">Fraud Rate</div>
          <div className="stat-value danger">{stats?.fraud_rate_pct?.toFixed(1) || '—'}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Blocked</div>
          <div className="stat-value">{stats?.blocked_count?.toLocaleString() || '—'}</div>
        </div>
        <div className="stat-card success">
          <div className="stat-label">Approved</div>
          <div className="stat-value success">{stats?.approved_count?.toLocaleString() || '—'}</div>
        </div>
      </div>

      <div className="main-cols">
        <div className="left-col">
          {/* Performance */}
          <div className="card">
            <div className="section-title">Performance</div>
            <div className="perf-stats">
              <div>
                <span className="label">Avg Latency</span>
                <span className="value">{stats?.avg_latency_ms?.toFixed(0) || '—'}ms</span>
              </div>
              <div>
                <span className="label">P99 Latency</span>
                <span className="value">{stats?.p99_latency_ms?.toFixed(0) || '—'}ms</span>
              </div>
            </div>
          </div>

          {/* Feed */}
          <div className="card">
            <div className="section-title">Live Feed</div>
            <div className="feed-list">
              {feed.length > 0 ? (
                feed.slice(0, 10).map((item, i) => (
                  <div key={i} className="feed-item">
                    <div className="feed-meta">
                      <span className="feed-amount">${item.amount?.toLocaleString()}</span>
                      <span className="feed-cat">{item.category}</span>
                    </div>
                    <span className={`feed-tag ${item.decision?.toLowerCase()}`}>
                      {item.decision || 'PENDING'}
                    </span>
                  </div>
                ))
              ) : (
                <div className="empty">No transactions yet. Run a simulation to see live data.</div>
              )}
            </div>
          </div>
        </div>

        <div className="right-col">
          {/* Health Monitor */}
          <div className="card">
            <div className="section-title">System Status</div>
            <div className="monitor">
              <div className="monitor-row">
                <span className="monitor-label">API STATUS</span>
                <span className={`monitor-val ${health ? 'status-ok' : 'status-err'}`}>
                  {health ? '● ONLINE' : '● OFFLINE'}
                </span>
              </div>
              <div className="monitor-row">
                <span className="monitor-label">Queue Size</span>
                <span className="monitor-val">{health?.queue_size || '0'}</span>
              </div>
              <div className="monitor-row">
                <span className="monitor-label">Results Stored</span>
                <span className="monitor-val">{health?.results_stored || '0'}</span>
              </div>
            </div>
          </div>

          {/* Alerts */}
          <div className="card">
            <div className="section-title">Fraud Alerts</div>
            <div className="alerts-list">
              {alerts.length > 0 ? (
                alerts.slice(0, 5).map((alert, i) => (
                  <div key={i} className="alert-item">
                    <div className="alert-icon">⚠️</div>
                    <div className="alert-text">
                      <div className="alert-title">{alert.reason || 'Fraud Detected'}</div>
                      <div className="alert-score">Risk: {(alert.score * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty">No fraud alerts yet.</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
