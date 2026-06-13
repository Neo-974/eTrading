import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL || '';
const api = axios.create({ baseURL });

export const TradingAPI = {
  status: () => api.get('/api/trading/status').then((r) => r.data),
  trades: () => api.get('/api/trading/trades').then((r) => r.data),
  settings: () => api.get('/api/trading/settings').then((r) => r.data),
  saveSettings: (s) => api.post('/api/trading/settings', s).then((r) => r.data),
  indicators: (symbol) => api.get(`/api/trading/indicators/${symbol}`).then((r) => r.data),
  candles: (symbol, count = 50) =>
    api.get(`/api/trading/candles/${symbol}`, { params: { count } }).then((r) => r.data),
  news: () => api.get('/api/trading/news').then((r) => r.data),
  start: () => api.post('/api/trading/start').then((r) => r.data),
  closeAll: () => api.post('/api/trading/close-all').then((r) => r.data),
};

export default api;
