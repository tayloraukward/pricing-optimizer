import { useState, useEffect } from 'react';
import AmbientBackground from './components/AmbientBackground';
import GlassCard from './components/GlassCard';
import SaveValuationButton from './components/SaveValuationButton';
import SavedValuationsList from './components/SavedValuationsList';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import { useAuth } from './contexts/AuthContext';
import './index.css';

interface ValuationResult {
  fair_price: number;
  price_range_low: number;
  price_range_high: number;
  explanation: string;
  comparable_count: number;
  confidence: 'low' | 'medium' | 'high';
}

interface ValuationResponse {
  success: boolean;
  valuation?: ValuationResult;
  error?: string;
}

interface ParsedDetails {
  year: number;
  manufacturer: string;
  model: string;
  odometer?: number;
  condition?: string;
}

function AppWithAuth() {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<string>('');
  const [showSignIn, setShowSignIn] = useState(false);
  const [showSignUp, setShowSignUp] = useState(false);
  const [showSavedValuations, setShowSavedValuations] = useState(false);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [currentValuationData, setCurrentValuationData] = useState<{
    originalDescription: string;
    parsedDetails: ParsedDetails;
    valuationResult: any;
  } | null>(null);

  const { user, signOut, getAccessToken } = useAuth();

  // Debug user state
  useEffect(() => {
    console.log('👤 AppWithAuth: User state changed:', user ? `Logged in as ${user.email}` : 'Not logged in');
  }, [user]);

  // Listen for show-signin event from SaveValuationButton
  useEffect(() => {
    const handleShowSignIn = () => setShowSignIn(true);
    window.addEventListener('show-signin', handleShowSignIn);
    return () => window.removeEventListener('show-signin', handleShowSignIn);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.user-dropdown')) {
        setShowUserDropdown(false);
      }
    };

    if (showUserDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showUserDropdown]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    setResult(null);
    setProgress('Initializing...');
    setCurrentValuationData(null);

    // Generate unique session ID for this valuation
    const sessionId = crypto.randomUUID();
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

    // Start event stream FIRST (before processing)
    const eventSource = new EventSource(`${API_URL}/events/${sessionId}`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.error) {
        setProgress(`Error: ${data.message}`);
      } else if (data.step === 'complete') {
        setProgress('Complete!');
      } else {
        setProgress(data.message);
      }
    };

    eventSource.onerror = () => {
      console.error(`Event stream error ${console.error()};
      }`);
      eventSource.close();
    };

    try {
      // Add auth token if user is signed in
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (user) {
        const token = getAccessToken();
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }

      // Call API with session_id
      const response = await fetch(`${API_URL}/get-valuation`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ description, session_id: sessionId }),
      });

      const data = await response.json();
      setResult(data);
      
      // Store valuation data for saving
      if (data.success && data.valuation) {
        // Note: In a real implementation, you'd get the parsed details from the API
        // For now, we'll create a simple parsed details object
        const parsedDetails = {
          year: 2020,
          manufacturer: 'Unknown',
          model: 'Vehicle',
          ...extractVehicleDetails(description)
        };
        
        setCurrentValuationData({
          originalDescription: description,
          parsedDetails,
          valuationResult: data.valuation
        });
      }
    } catch (err) {
      setResult({
        success: false,
        error: `Failed to connect to API. Please try again. ${err}`,
      });
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(''), 1000);
      eventSource.close();
    }
  };

  // Simple function to extract vehicle details from description
  const extractVehicleDetails = (desc: string): Partial<ParsedDetails> => {
    const yearMatch = desc.match(/\b(19|20)\d{2}\b/);
    return {
      year: yearMatch ? parseInt(yearMatch[0]) : 2020,
      manufacturer: desc.split(' ')[1] || 'Unknown',
      model: desc.split(' ')[2] || 'Vehicle',
    };
  };

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />
      
      <div className="relative z-10">
        {/* Header with Auth */}
        <header className="sticky top-0 z-50 border-b border-white/6 backdrop-blur-sm bg-white/[0.02]">
          <div className="container mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-semibold text-white tracking-tight">Car Valuation Agent</h1>
              
              <div className="flex items-center gap-4">
                {user ? (
                  <div className="relative user-dropdown">
                    <button
                      onClick={() => setShowUserDropdown(!showUserDropdown)}
                      className="text-sm text-white/70 hover:text-white transition-colors flex items-center gap-2"
                    >
                      {user.email}
                      <svg 
                        className={`w-4 h-4 transition-transform ${showUserDropdown ? 'rotate-180' : ''}`} 
                        fill="none" 
                        viewBox="0 0 24 24" 
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    
                    {showUserDropdown && (
                      <div className="absolute right-0 mt-2 w-48 bg-white/10 backdrop-blur-md border border-white/20 rounded-lg py-1 z-50">
                        <button
                          onClick={() => {
                            setShowSavedValuations(true);
                            setShowUserDropdown(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-white/80 hover:bg-white/10 transition-colors flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                          </svg>
                          Saved Valuations
                        </button>
                        <button
                          onClick={() => {
                            signOut();
                            setShowUserDropdown(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-white/80 hover:bg-white/10 transition-colors flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                          </svg>
                          Sign Out
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={() => setShowSignIn(true)}
                    className="text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-colors"
                  >
                    Sign In
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-6 py-12">
          <div className="max-w-2xl mx-auto mb-8 rounded-2xl border border-amber-400/30 bg-amber-400/10 px-6 py-5 text-center backdrop-blur-sm">
            <p className="text-sm font-mono uppercase tracking-widest text-amber-300 mb-2">
              Temporary Outage
            </p>
            <p className="text-white/85 leading-relaxed">
              The site is currently down while I'm migrating database providers. Expect to be back online before end of week 06/20/2026.
            </p>
          </div>
          <div className="max-w-2xl mx-auto">
            {/* Hero Section */}
            <div className="text-center mb-8">
              <h1 className="text-6xl md:text-7xl font-bold text-gradient mb-8 leading-tight">
                Get Your Car's<br />True Market Value
              </h1>
              <p className="text-2xl md:text-3xl text-white/70 leading-relaxed max-w-2xl mx-auto font-light">
                Describe your vehicle in plain English. Our Agent extracts the details 
                and calculates a price instantly.
              </p>
            </div>

            {/* Input Form */}
            <GlassCard className="p-8 mb-8">
              <form onSubmit={handleSubmit}>
                <label className="block text-sm font-mono tracking-widest uppercase text-white/50 mb-3" htmlFor="car-description">
                  Describe Your Vehicle
                </label>
                <textarea
                  id="car-description"
                  className="form-input w-full resize-none"
                  placeholder="e.g., 2018 Honda Civic with 45,000 miles, excellent condition, clean title..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                />
                <button
                  type="submit"
                  className="btn-primary w-full mt-6"
                  disabled={loading || !description.trim()}
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing...
                    </span>
                  ) : (
                    'Get Valuation'
                  )}
                </button>

                {/* Progress Indicator */}
                {loading && progress && (
                  <div className="mt-6 flex items-center gap-3 text-white/50">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    <span className="text-sm font-medium">{progress}</span>
                  </div>
                )}
              </form>
            </GlassCard>

            {/* Results Card */}
            {result && (
              <GlassCard 
                className={`p-8 ${result.success ? 'border-green-500/30' : 'border-red-500/30'}`}
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    result.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {result.success ? '✓' : '✗'}
                  </div>
                  <h3 className="text-xl font-semibold text-white">
                    {result.success ? 'Valuation Complete' : 'Valuation Failed'}
                  </h3>
                </div>
                
                {result.success && result.valuation ? (
                  <div className="space-y-6">
                    {/* Price Display */}
                    <div className="text-center p-6 bg-gradient-to-br from-green-500/10 to-green-500/5 rounded-2xl border border-green-500/20">
                      <div className="text-sm font-mono tracking-widest uppercase text-green-400 mb-2">
                        Fair Market Price
                      </div>
                      <div className="text-4xl md:text-5xl font-bold text-green-400 leading-none">
                        ${result.valuation.fair_price.toLocaleString()}
                      </div>
                    </div>
                    
                    {/* Price Range */}
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-sm font-mono tracking-widest uppercase text-white/50 mb-1">
                        Price Range
                      </div>
                      <div className="text-lg font-semibold text-white">
                        ${result.valuation.price_range_low.toLocaleString()} - ${result.valuation.price_range_high.toLocaleString()}
                      </div>
                    </div>
                    
                    {/* Analysis */}
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                      <div className="text-sm font-mono tracking-widest uppercase text-white/50 mb-3">
                        Analysis
                      </div>
                      <p className="text-white/70 leading-relaxed">
                        {result.valuation.explanation}
                      </p>
                    </div>

                    {/* Save Button */}
                    {currentValuationData && (
                      <div className="flex justify-end pt-4 border-t border-white/10">
                        <SaveValuationButton
                          parsedDetails={currentValuationData.parsedDetails}
                          valuationResult={currentValuationData.valuationResult}
                          onSaveSuccess={() => {
                            // Optional: Show success message
                            console.log('Valuation saved!');
                          }}
                        />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-red-400 text-2xl">!</span>
                    </div>
                    <p className="text-red-400">{result.error}</p>
                  </div>
                )}
              </GlassCard>
            )}
          </div>
        </main>
      </div>

      {/* Auth Modals */}
      {showSignIn && (
        <SignIn
          onClose={() => setShowSignIn(false)}
          onSwitchToSignUp={() => {
            setShowSignIn(false);
            setShowSignUp(true);
          }}
        />
      )}

      {showSignUp && (
        <SignUp
          onClose={() => setShowSignUp(false)}
          onSwitchToSignIn={() => {
            setShowSignUp(false);
            setShowSignIn(true);
          }}
        />
      )}

      {/* Saved Valuations Modal */}
      {showSavedValuations && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-black/80 backdrop-blur-md border border-white/20 rounded-2xl p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-white">Saved Valuations</h2>
              <button 
                onClick={() => setShowSavedValuations(false)}
                className="text-white/60 hover:text-white text-2xl"
              >
                &times;
              </button>
            </div>
            <SavedValuationsList />
          </div>
        </div>
      )}
    </div>
  );
}

export default AppWithAuth;
