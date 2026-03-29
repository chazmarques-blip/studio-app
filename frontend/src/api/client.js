/**
 * API Client — Centralized axios instance with interceptors.
 * Single point for auth headers, error handling, and request config.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: `${process.env.REACT_APP_BACKEND_URL}/api`,
  timeout: 120000,
});

// Request interceptor: auto-attach auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('studiox_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 globally
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const path = window.location.pathname;
      if (path !== '/login' && path !== '/') {
        localStorage.removeItem('studiox_token');
        localStorage.removeItem('studiox_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
