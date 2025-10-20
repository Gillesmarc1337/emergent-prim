import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function LoginPage() {
  const { user, login, loginDemo } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [hoveredButton, setHoveredButton] = useState(null);

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
            alert('Authentication failed. Please check if you are authorized.');
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
    // Redirect to Emergent Auth
    const redirectUrl = window.location.origin + '/';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleDemoAccess = async () => {
    setLoadingDemo(true);
    try {
      await loginDemo();
    } catch (err) {
      alert('Demo login failed. Please try again.');
    } finally {
      setLoadingDemo(false);
    }
  };

  // If already logged in, don't show login page
  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#1a1d23] to-[#14161a] flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Subtle background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-blue-900/10 to-purple-900/10 rounded-full opacity-20 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-amber-900/10 to-orange-900/10 rounded-full opacity-20 blur-3xl"></div>
        
        {/* Floating pirate elements - subtle */}
        <div className="absolute top-20 right-20 text-4xl opacity-5 animate-float hidden sm:block">⚔️</div>
        <div className="absolute bottom-32 left-32 text-3xl opacity-5 animate-float hidden sm:block" style={{ animationDelay: '1s' }}>☠️</div>
        <div className="absolute top-40 left-40 text-2xl opacity-5 animate-float hidden md:block" style={{ animationDelay: '2s' }}>🏴‍☠️</div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        .animate-float {
          animation: float 6s ease-in-out infinite;
        }
      `}</style>

      <div className="relative w-full max-w-md z-10 px-4 sm:px-0">
        {/* Logo Section */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="inline-flex items-center justify-center w-24 h-24 sm:w-28 sm:h-28 bg-[#24272e] rounded-3xl shadow-2xl mb-4 sm:mb-6 group hover:shadow-3xl transition-all duration-500">
            <img 
              src="https://www.primelis.com/wp-content/uploads/2023/10/logo-primelis.svg" 
              alt="Primelis Logo"
              className="w-16 h-16 sm:w-20 sm:h-20 object-contain group-hover:scale-110 transition-transform duration-500 invert"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.parentElement.innerHTML = '<span class="text-4xl sm:text-5xl font-bold text-white">P</span>';
              }}
            />
          </div>
          <h1 className="text-5xl sm:text-6xl font-semibold text-white mb-3 tracking-tight">
            Primelis
          </h1>
          <p className="text-slate-400 text-base sm:text-lg font-light flex items-center justify-center gap-2">
            Analytics Dashboard
            <span className="text-xs opacity-50">☠️</span>
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-[#1e2128]/90 backdrop-blur-2xl rounded-3xl shadow-2xl p-6 sm:p-10 border border-[#2a2d35]/50">
          <div className="text-center mb-6 sm:mb-8">
            <h2 className="text-xl sm:text-2xl font-semibold text-white mb-2">
              Welcome aboard
            </h2>
            <p className="text-slate-400 text-sm">
              Choose your authentication method
            </p>
          </div>

          {/* Login Options */}
          <div className="space-y-3">
            {/* Secure Login */}
            <button
              onClick={handleSecuredAccess}
              disabled={loading || loadingDemo}
              onMouseEnter={() => setHoveredButton('secure')}
              onMouseLeave={() => setHoveredButton(null)}
              className="w-full group bg-[#24272e] hover:bg-[#2a2d35] text-white font-medium py-3 sm:py-4 px-4 sm:px-6 rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 sm:gap-3">
                  <span className="text-xl sm:text-2xl">🛡️</span>
                  <div className="text-left">
                    <div className="font-semibold text-sm sm:text-base">Secure Login</div>
                    <div className="text-xs text-slate-400 hidden sm:block">OAuth 2.0 • Encrypted</div>
                  </div>
                </div>
                {hoveredButton === 'secure' && (
                  <span className="text-red-500 animate-pulse hidden sm:inline">⚔️</span>
                )}
              </div>
            </button>

            <div className="flex items-center gap-3 text-slate-500 text-sm py-2">
              <div className="flex-1 h-px bg-[#2a2d35]"></div>
              <span className="text-xs">or</span>
              <div className="flex-1 h-px bg-[#2a2d35]"></div>
            </div>

            {/* Demo Mode */}
            <button
              onClick={handleDemoAccess}
              disabled={loading || loadingDemo}
              onMouseEnter={() => setHoveredButton('demo')}
              onMouseLeave={() => setHoveredButton(null)}
              className="w-full group bg-gradient-to-r from-[#d97706] to-[#ea580c] hover:from-[#b45309] hover:to-[#c2410c] text-white font-medium py-3 sm:py-4 px-4 sm:px-6 rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 sm:gap-3">
                  <span className="text-xl sm:text-2xl">🏴‍☠️</span>
                  <div className="text-left">
                    <div className="font-semibold text-sm sm:text-base">Demo Voyage</div>
                    <div className="text-xs text-amber-100 hidden sm:block">No authentication • 24h session</div>
                  </div>
                </div>
                {hoveredButton === 'demo' && (
                  <span className="text-yellow-300 animate-pulse hidden sm:inline">💰</span>
                )}
              </div>
            </button>
          </div>

          {/* Crew Info */}
          <div className="mt-6 sm:mt-8 pt-6 border-t border-[#2a2d35]">
            <div className="text-center text-xs text-slate-400">
              <p className="mb-2">🏴‍☠️ Authorized Crew</p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-4 font-mono">
                <span className="px-3 py-1 bg-[#24272e] rounded-full text-xs">asher@primelis.com</span>
                <span className="px-3 py-1 bg-[#24272e] rounded-full text-xs">remi@primelis.com</span>
              </div>
            </div>
          </div>
        </div>

        {/* Loading Indicator */}
        {(loading || loadingDemo) && (
          <div className="mt-6 sm:mt-8 text-center">
            <div className="inline-flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-3 bg-[#1e2128]/90 backdrop-blur rounded-full shadow-lg">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <span className="text-xs sm:text-sm text-slate-200 font-medium">Loading...</span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-8 sm:mt-12 text-slate-500 text-xs sm:text-sm font-light">
          <p className="flex items-center justify-center gap-2">
            <span>2025</span>
            <span>•</span>
            <span>Made by</span>
            <span className="font-medium text-slate-300">Minus</span>
            <span>&</span>
            <span className="font-medium text-slate-300">Cortex</span>
            <span className="text-xs">🧠⚡</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
