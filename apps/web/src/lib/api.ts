import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptors for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Portfolio API
export const portfolioApi = {
  getCurrent: () => api.get('/api/portfolio/current'),
  getHistory: (days = 30) => api.get(`/api/portfolio/history?days=${days}`),
  getMetrics: () => api.get('/api/portfolio/metrics'),
  getPnlBreakdown: () => api.get('/api/portfolio/pnl/breakdown'),
  getPositions: () => api.get('/api/portfolio/positions'),
  getAssets: () => api.get('/api/portfolio/assets'),
};

// Trades API
export const tradesApi = {
  getAll: (params?: { status?: string; strategy?: string; chain?: string; page?: number; limit?: number }) =>
    api.get('/api/trades', { params }),
  getById: (id: string) => api.get(`/api/trades/${id}`),
  getStats: () => api.get('/api/trades/stats/summary'),
  getDailyHistory: (days = 30) => api.get(`/api/trades/history/daily?days=${days}`),
};

// Agents API
export const agentsApi = {
  getAll: () => api.get('/api/agents'),
  getById: (id: string) => api.get(`/api/agents/${id}`),
  start: (id: string) => api.post(`/api/agents/${id}/start`),
  stop: (id: string) => api.post(`/api/agents/${id}/stop`),
  pause: (id: string) => api.post(`/api/agents/${id}/pause`),
  getStats: () => api.get('/api/agents/stats/overview'),
  getActions: (id: string) => api.get(`/api/agents/${id}/actions`),
};

// Pools API
export const poolsApi = {
  getAll: (params?: { chain?: string; category?: string; min_tvl?: number; page?: number; limit?: number }) =>
    api.get('/api/pools', { params }),
  getByAddress: (address: string) => api.get(`/api/pools/${address}`),
  getArbitrageOpportunities: (minSpread = 0.5) =>
    api.get(`/api/pools/arbitrage/opportunities?min_spread_percent=${minSpread}`),
  getTopApys: (limit = 10) => api.get(`/api/pools/top/apy?limit=${limit}`),
};

// WebSocket connection
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(private url: string) {}

  connect(onMessage: (data: any) => void) {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;

        // Subscribe to channels
        this.send({ action: 'subscribe', channel: 'prices' });
        this.send({ action: 'subscribe', channel: 'trades' });
        this.send({ action: 'subscribe', channel: 'agents' });
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket closed');
        this.reconnect(onMessage);
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.reconnect(onMessage);
    }
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    this.ws?.close();
  }

  private reconnect(onMessage: (data: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
        this.connect(onMessage);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }
}

export default api;
