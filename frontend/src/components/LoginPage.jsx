import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { TrendingUp, Shield, Zap } from 'lucide-react';

const LoginPage = () => {
  const { login, loginDemo } = useAuth();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);

  // Check for session_id in URL fragment on mount
  useEffect(() => {
    const handleSessionFromUrl = async () => {
      const hash = window.location.hash;
      if (hash && hash.includes('session_id=')) {
        const sessionId = hash.split('session_id=')[1].split('&')[0];
        
        if (sessionId) {
          setLoading(true);
          try {
            await login(sessionId);
            // Clear the hash from URL
            window.history.replaceState(null, '', window.location.pathname);
          } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed. Please check if you are authorized.');
          } finally {
            setLoading(false);
          }
        }
      }
    };

    handleSessionFromUrl();
  }, [login]);

  const handleSecuredAccess = () => {
    setLoading(true);
    setError(null);

    // Redirect to Emergent Auth
    const redirectUrl = encodeURIComponent(window.location.origin + window.location.pathname);
    window.location.href = `https://auth.emergentagent.com/?redirect_uri=${redirectUrl}`;
  };

  const handleDemoAccess = async () => {
    setLoadingDemo(true);
    setError(null);

    try {
      await loginDemo();
    } catch (err) {
      setError(err.response?.data?.detail || 'Demo login failed. Please try again.');
    } finally {
      setLoadingDemo(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <Card className="w-full max-w-lg shadow-2xl border-blue-200">
        <CardHeader className="text-center space-y-3 pb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-5 rounded-2xl shadow-lg">
              <TrendingUp className="h-14 w-14 text-white" />
            </div>
          </div>
          <CardTitle className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            Sales Analytics Dashboard
          </CardTitle>
          <CardDescription className="text-base text-gray-600">
            Choose your access method
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4 px-6 pb-8">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Primary: Secured Access */}
          <div className="space-y-2">
            <Button
              onClick={handleSecuredAccess}
              disabled={loading || loadingDemo}
              className="w-full h-14 text-base bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg"
              size="lg"
            >
              {loading ? (
                <span>Redirecting...</span>
              ) : (
                <span className="flex items-center justify-center gap-3 font-semibold">
                  <Shield className="h-5 w-5" />
                  ACCESS SECURED TERMINAL
                </span>
              )}
            </Button>
            <p className="text-xs text-center text-gray-500">
              🔒 Production Mode • Google OAuth Authentication
            </p>
          </div>

          {/* Divider */}
          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-white px-2 text-gray-500">Or</span>
            </div>
          </div>

          {/* Secondary: Demo Access */}
          <div className="space-y-2">
            <Button
              onClick={handleDemoAccess}
              disabled={loading || loadingDemo}
              variant="outline"
              className="w-full h-12 text-base border-2 border-amber-400 hover:bg-amber-50 hover:border-amber-500"
              size="lg"
            >
              {loadingDemo ? (
                <span>Creating demo session...</span>
              ) : (
                <span className="flex items-center justify-center gap-2 font-medium text-amber-700">
                  <Zap className="h-4 w-4" />
                  DEMO ACCESS - SKIP AUTH
                </span>
              )}
            </Button>
            <p className="text-xs text-center text-gray-500">
              ⚡ Development Mode • Instant access • 24h session
            </p>
          </div>

          {/* Info Section */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="text-center text-sm text-gray-600 space-y-2">
              <p className="font-semibold text-gray-700">Authorized Users (Production):</p>
              <div className="flex justify-center gap-4 text-xs">
                <span className="px-3 py-1 bg-blue-50 rounded-full">
                  asher@primelis.com <span className="text-gray-500">(Viewer)</span>
                </span>
                <span className="px-3 py-1 bg-indigo-50 rounded-full">
                  remi@primelis.com <span className="text-gray-500">(Admin)</span>
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;
