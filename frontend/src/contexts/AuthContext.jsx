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

  // Auto-refresh view configs every 30 seconds to detect changes
  useEffect(() => {
    if (!currentView) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await axios.get(`${API}/api/views/${currentView.id}/config`, {
          withCredentials: true
        });
        
        // Only update if config actually changed
        if (JSON.stringify(response.data) !== JSON.stringify(viewConfig)) {
          console.log('View config updated by another admin, refreshing...');
          setViewConfig(response.data);
          // Optionally reload the page or trigger a data refresh
          window.dispatchEvent(new CustomEvent('viewConfigUpdated', { detail: response.data }));
        }
      } catch (error) {
        console.error('Failed to refresh view config:', error);
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(intervalId);
  }, [currentView, viewConfig]);

  // Reload when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && currentView) {
        // Reload view config when user returns to tab
        axios.get(`${API}/api/views/${currentView.id}/config`, {
          withCredentials: true
        })
        .then(response => {
          if (JSON.stringify(response.data) !== JSON.stringify(viewConfig)) {
            setViewConfig(response.data);
            window.dispatchEvent(new CustomEvent('viewConfigUpdated', { detail: response.data }));
          }
        })
        .catch(err => console.error('Failed to reload config:', err));
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [currentView, viewConfig]);

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
      
      if (response.data.length > 0) {
        // Try to restore last selected view from localStorage
        const savedViewId = localStorage.getItem('selectedViewId');
        let viewToLoad = null;
        
        if (savedViewId) {
          // Try to find the saved view
          viewToLoad = response.data.find(v => v.id === savedViewId);
          console.log(`Restoring saved view: ${savedViewId}`, viewToLoad ? '✓' : '✗');
        }
        
        // Fallback to default view if saved view not found
        if (!viewToLoad) {
          viewToLoad = response.data.find(v => v.is_default || v.name === 'Organic') || response.data[0];
          console.log('Using default view:', viewToLoad?.name);
        }
        
        await switchView(viewToLoad);
      }
    } catch (error) {
      console.error('Error loading views:', error);
    }
  };

  const switchView = async (view) => {
    try {
      setCurrentView(view);
      
      // Save selected view to localStorage for persistence
      localStorage.setItem('selectedViewId', view.id);
      console.log('Saved view to localStorage:', view.id, view.name);
      
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

  const login = async (token) => {
    try {
      const response = await axios.post(
        `${API}/api/auth/session-data`,
        { token },
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
    setCurrentView: switchView, // Use switchView instead of setCurrentView directly
    views,
    viewConfig, // Current view's configuration/targets
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
