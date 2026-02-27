import axios from 'axios'

// In dev, prefer the Vite proxy (`/api`) to avoid CORS/network errors.
// In production builds, use VITE_API_URL (or fallback to localhost).
const API_BASE_URL = import.meta.env.DEV
  ? '/api'
  : (import.meta.env.VITE_API_URL || 'http://localhost:8000')

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Users API
export const usersAPI = {
  getProfile: () => api.get('/users/me'),
  getScore: (userId) => api.get(`/users/${userId}/score`),
  getTrustGraph: (userId, depth = 2) => api.get(`/users/${userId}/graph?depth=${depth}`),
}

// Communities API
export const communitiesAPI = {
  create: (data) => api.post('/communities', data),
  list: () => api.get('/communities'),
  join: (communityId, data) => api.post(`/communities/${communityId}/join`, data),
  vouch: (communityId, data) => api.post(`/communities/${communityId}/vouch`, data),
  getDashboard: (communityId) => api.get(`/communities/${communityId}/dashboard`),
}

// Loans API
export const loansAPI = {
  apply: (data) => api.post('/loans/apply', data),
  getStatus: (loanId) => api.get(`/loans/${loanId}/status`),
  repay: (loanId, data) => api.post(`/loans/${loanId}/repay`, data),
  getMyLoans: () => api.get('/loans/my-loans'),
}

// Scoring API
export const scoringAPI = {
  compute: (userId) => api.post(`/scoring/compute/${userId}`),
  explain: (userId) => api.get(`/scoring/explain/${userId}`),
}

export default api
