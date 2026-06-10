import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://fraudshield-ai-production-78c0.up.railway.app';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const checkHealth = () => api.get('/health');

// Dashboard stats
export const getDashboardStats = () => api.get('/dashboard/stats');

// Get feed
export const getFeed = () => api.get('/dashboard/feed');

// Get alerts
export const getAlerts = () => api.get('/dashboard/alerts');

// Run simulation
export const runSimulation = (data) => api.post('/simulate', data);

// Reset dashboard
export const resetDashboard = () => api.post('/dashboard/reset');

// SSE Stream for simulator
export const createSSEStream = (url) => new EventSource(`${API_BASE_URL}${url}`);

export default api;
