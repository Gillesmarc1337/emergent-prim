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

    // Redirect to Emergent Auth - redirect parameter should point to MAIN APP (dashboard), not login page
    // After auth, user will land at: {redirect}#session_id={session_id}
    const redirectUrl = window.location.origin + '/';  // Main app URL
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
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
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-black">
      {/* Cyber Pirates Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-950 via-slate-900 to-fuchsia-950 opacity-80" />
      
      {/* Animated Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#0ea5e920_1px,transparent_1px),linear-gradient(to_bottom,#0ea5e920_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      
      {/* Glowing Orbs */}
      <div className="absolute top-20 left-20 w-72 h-72 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
      <div className="absolute bottom-20 right-20 w-72 h-72 bg-fuchsia-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse delay-700" />
      
      {/* Skull Icon (Cyber Pirate) */}
      <div className="absolute top-10 right-10 text-cyan-500 opacity-10 text-9xl animate-pulse">
        ☠️
      </div>
      
      <Card className="w-full max-w-lg shadow-2xl relative z-10 border-2 border-cyan-500/30 bg-slate-900/90 backdrop-blur-xl">
        <CardHeader className="text-center space-y-3 pb-8 relative">
          {/* Glitch Effect Line */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500 to-transparent animate-pulse" />
          
          <div className="flex justify-center mb-4">
            <div className="relative">
              <img 
                src="/primelis-logo.jpg" 
                alt="Primelis Logo" 
                className="h-16 w-auto object-contain relative z-10"
                style={{ filter: 'drop-shadow(0 0 10px rgba(6, 182, 212, 0.5))' }}
              />
              <div className="absolute inset-0 bg-cyan-500/20 blur-xl rounded-full" />
            </div>
          </div>
          
          <CardTitle className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-fuchsia-400 to-cyan-400 bg-clip-text text-transparent animate-pulse">
            ☠️ CYBER PIRATES TERMINAL ☠️
          </CardTitle>
          <CardDescription className="text-base text-cyan-300/80 font-mono">
            &gt; CHOOSE YOUR BOARDING METHOD_
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4 px-6 pb-8">
          {error && (
            <Alert variant="destructive" className="mb-4 border-red-500 bg-red-950/50 text-red-300">
              <AlertDescription className="font-mono">⚠️ {error}</AlertDescription>
            </Alert>
          )}

          {/* Primary: Secured Access */}
          <div className="space-y-2">
            <Button
              onClick={handleSecuredAccess}
              disabled={loading || loadingDemo}
              className="w-full h-14 text-base bg-gradient-to-r from-cyan-600 via-fuchsia-600 to-cyan-600 hover:from-cyan-500 hover:via-fuchsia-500 hover:to-cyan-500 shadow-lg shadow-cyan-500/50 border border-cyan-400/50 font-mono text-black font-bold relative overflow-hidden group"
              size="lg"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
              {loading ? (
                <span className="relative z-10">⚡ INITIALIZING...</span>
              ) : (
                <span className="flex items-center justify-center gap-3 font-semibold relative z-10">
                  <Shield className="h-5 w-5" />
                  🏴‍☠️ BOARD THE FLAGSHIP
                </span>
              )}
            </Button>
            <p className="text-xs text-center text-cyan-400/70 font-mono">
              🔒 SECURE_MODE • OAUTH_2.0 • ENCRYPTED_
            </p>
          </div>

          {/* Divider */}
          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-cyan-500/30" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-slate-900 px-2 text-cyan-500 font-mono">OR</span>
            </div>
          </div>

          {/* Secondary: Demo Access */}
          <div className="space-y-2">
            <Button
              onClick={handleDemoAccess}
              disabled={loading || loadingDemo}
              variant="outline"
              className="w-full h-12 text-base border-2 border-amber-400 hover:bg-amber-500/20 hover:border-amber-300 bg-slate-900/50 text-amber-300 font-mono font-semibold shadow-lg shadow-amber-500/20"
              size="lg"
            >
              {loadingDemo ? (
                <span>⚓ LAUNCHING DEMO SHIP...</span>
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
