import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
const TOKEN_KEY = 'enersight_auth_token'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data)
      // If unauthorized, redirect to login
      if (error.response.status === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem('enersight_user')
        window.location.href = '/login'
      }
    } else if (error.request) {
      console.error('Network Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const energyAPI = {
  getReadings: (startDate, endDate, aggregation = 'raw', window = '1h') =>
    api.get('/energy/readings', {
      params: { start_date: startDate, end_date: endDate, aggregation, window }
    }),
  recordReading: (data) => api.post('/energy/readings', data),
  getStatistics: (period = 'week', startDate = null, endDate = null) =>
    api.get('/energy/statistics', {
      params: { period, start_date: startDate, end_date: endDate }
    }),
}

export const predictionsAPI = {
  predict: (data) => api.post('/predictions/predict', data),
  forecast: (historicalData, hours = 24) =>
    api.post('/predictions/forecast', historicalData, { params: { hours } }),
}

export const anomaliesAPI = {
  detect: (hours = 24) => api.get('/anomalies/detect', { params: { hours } }),
  getHistory: (days = 7) => api.get('/anomalies/history', { params: { days } }),
}

export const systemAPI = {
  getHealth: () => api.get('/health', { baseURL: 'http://localhost:8000' }),
  getInfo: () => api.get('/info'),
}

export default api
