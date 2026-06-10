import axios from 'axios';
import { API_URL } from '../config/api.config';

const api = axios.create({
  baseURL: API_URL,
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
