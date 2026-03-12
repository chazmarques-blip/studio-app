import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('agentflow_token'));
  const [loading, setLoading] = useState(true);

  const setAuthHeader = useCallback((t) => {
    if (t) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${t}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, []);

  useEffect(() => {
    if (token) {
      setAuthHeader(token);
      axios.get(`${API}/auth/me`).then(res => {
        setUser(res.data);
        setLoading(false);
      }).catch(() => {
        localStorage.removeItem('agentflow_token');
        setToken(null);
        setUser(null);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, [token, setAuthHeader]);

  const signUp = async (email, password, fullName) => {
    const { data } = await axios.post(`${API}/auth/signup`, { email, password, full_name: fullName });
    localStorage.setItem('agentflow_token', data.access_token);
    setToken(data.access_token);
    setAuthHeader(data.access_token);
    setUser(data.user);
    return { data, error: null };
  };

  const signIn = async (email, password) => {
    const { data } = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem('agentflow_token', data.access_token);
    setToken(data.access_token);
    setAuthHeader(data.access_token);
    setUser(data.user);
    return { data, error: null };
  };

  const signOut = async () => {
    localStorage.removeItem('agentflow_token');
    setToken(null);
    setUser(null);
    setAuthHeader(null);
  };

  const updateProfile = async (updates) => {
    const { data } = await axios.put(`${API}/auth/profile`, updates);
    setUser(prev => ({ ...prev, ...updates }));
    return data;
  };

  const value = { user, token, loading, signUp, signIn, signOut, updateProfile };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
