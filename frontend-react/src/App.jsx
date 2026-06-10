import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import SimulatorPage from './pages/SimulatorPage';
import './styles/App.css';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <nav>
      <Link to="/" className="nav-logo">
        <svg className="shield-icon" viewBox="0 0 24 24" width="28" height="28">
          <path d="M12 2L4 6v6c0 5.25 3.5 10.15 8 11.35C16.5 22.15 20 17.25 20 12V6L12 2z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
        FRAUD<span>SHIELD</span>
      </Link>
      <div className="nav-links">
        <Link to="/" className={isActive('/')}>Home</Link>
        <Link to="/simulator" className={isActive('/simulator')}>Simulator</Link>
        <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <div className="grid-bg"></div>
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
