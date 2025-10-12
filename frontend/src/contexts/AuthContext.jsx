import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState(null);
  const [views, setViews] = useState([]);

  // Check if user is authenticated on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/api/auth/me`, {
        withCredentials: true
      });
      setUser(response.data);
      await loadViews();
    } catch (error) {
      console.log('Not authenticated');
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const loadViews = async () => {
    try {
      const response = await axios.get(`${API}/api/views`, {
        withCredentials: true
      });
      setViews(response.data);
      
      // Set default view (Organic)
      const defaultView = response.data.find(v => v.is_default);
      if (defaultView) {
        setCurrentView(defaultView);
      }
    } catch (error) {
      console.error('Error loading views:', error);
    }
  };

  const login = async (sessionId) => {
    try {
      const response = await axios.post(
        `${API}/api/auth/session-data`,
        { sessionId },
        { withCredentials: true }
      );
      setUser(response.data);
      await loadViews();
      return response.data;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/api/auth/logout`, {}, {
        withCredentials: true
      });
      setUser(null);
      setCurrentView(null);
      setViews([]);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const value = {
    user,
    loading,
    login,
    logout,
    checkAuth,
    currentView,
    setCurrentView,
    views,
    loadViews,
    isAdmin: user?.role === 'super_admin'
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
