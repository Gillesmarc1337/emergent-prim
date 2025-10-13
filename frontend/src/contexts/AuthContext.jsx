import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentView, setCurrentView] = useState(null);
  const [views, setViews] = useState([]);
  const [viewConfig, setViewConfig] = useState(null); // Store current view's config/targets

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
      // Use the new user-accessible views endpoint
      const response = await axios.get(`${API}/api/views/user/accessible`, {
        withCredentials: true
      });
      setViews(response.data);
      
      // Set first view as default or find Organic view
      if (response.data.length > 0) {
        const defaultView = response.data.find(v => v.is_default || v.name === 'Organic') || response.data[0];
        await switchView(defaultView);
      }
    } catch (error) {
      console.error('Error loading views:', error);
    }
  };

  const switchView = async (view) => {
    try {
      setCurrentView(view);
      
      // Load view configuration/targets
      const configResponse = await axios.get(`${API}/api/views/${view.id}/config`, {
        withCredentials: true
      });
      setViewConfig(configResponse.data);
    } catch (error) {
      console.error('Error loading view config:', error);
      setViewConfig(null);
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

  const loginDemo = async () => {
    try {
      const response = await axios.post(
        `${API}/api/auth/demo-login`,
        {},
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
    loginDemo,
    logout,
    checkAuth,
    currentView,
    setCurrentView,
    views,
    loadViews,
    isAdmin: user?.role === 'super_admin',
    isDemo: user?.is_demo || user?.email === 'demo@primelis.com'
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
