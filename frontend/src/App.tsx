import { useState } from 'react';
import AmbientBackground from './components/AmbientBackground';
import GlassCard from './components/GlassCard';
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

function App() {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<ValuationResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      // Use environment variable in production, localhost for development
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
      
      const response = await fetch(`${API_URL}/get-valuation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description }),
      });

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult({
        success: false,
        error: `Failed to connect to API. Please try again. ${err}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />
      
      <div className="relative z-10">
        <header className="border-b border-white/6 backdrop-blur-sm bg-white/[0.02]">
          <div className="container mx-auto px-6 py-6">
            <h1 className="text-2xl font-semibold text-white tracking-tight">Car Valuation Agent</h1>
          </div>
        </header>

        <main className="container mx-auto px-6 py-24">
          <div className="max-w-2xl mx-auto">
            {/* Hero Section */}
            <div className="text-center mb-16 animate-fade-up">
              <h1 className="text-6xl md:text-7xl font-bold text-gradient mb-8 leading-tight">
                Get Your Car's<br />True Market Value
              </h1>
              <p className="text-2xl md:text-3xl text-foreground leading-relaxed max-w-2xl mx-auto font-light">
                Describe your vehicle in plain English. Our Agent extracts the details 
                and calculates a price instantly.
              </p>
            </div>

            {/* Input Form */}
            <GlassCard className="p-8 mb-8 animate-scale-in" style={{ animationDelay: '0.1s' }}>
              <form onSubmit={handleSubmit}>
                <label className="block text-sm font-mono tracking-widest uppercase text-foreground-subtle mb-3" htmlFor="car-description">
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
              </form>
            </GlassCard>

            {/* Results Card */}
            {result && (
              <GlassCard 
                className={`p-8 animate-scale-in ${result.success ? 'border-green-500/30' : 'border-red-500/30'}`}
                style={{ animationDelay: '0.2s' }}
              >
                <div className="flex items-center gap-3 mb-6">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    result.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {result.success ? '✓' : '✗'}
                  </div>
                  <h3 className="text-xl font-semibold">
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
                    
                    {/* Other Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-background-elevated rounded-xl border border-white/6">
                        <div className="text-sm font-mono tracking-widest uppercase text-foreground-subtle mb-1">
                          Price Range
                        </div>
                        <div className="text-lg font-semibold text-foreground">
                          ${result.valuation.price_range_low.toLocaleString()} - ${result.valuation.price_range_high.toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-background-elevated rounded-xl border border-white/6">
                        <div className="text-sm font-mono tracking-widest uppercase text-foreground-subtle mb-1">
                          Confidence
                        </div>
                        <div className={`confidence-badge confidence-${result.valuation.confidence}`}>
                          {result.valuation.confidence.toUpperCase()}
                        </div>
                      </div>
                      
                      <div className="p-4 bg-background-elevated rounded-xl border border-white/6">
                        <div className="text-sm font-mono tracking-widest uppercase text-foreground-subtle mb-1">
                          Comparables Used
                        </div>
                        <div className="text-lg font-semibold text-foreground">
                          {result.valuation.comparable_count} cars
                        </div>
                      </div>
                    </div>
                    
                    {/* Analysis */}
                    <div className="p-4 bg-background-elevated rounded-xl border border-white/6">
                      <div className="text-sm font-mono tracking-widest uppercase text-foreground-subtle mb-3">
                        Analysis
                      </div>
                      <p className="text-foreground-muted leading-relaxed">
                        {result.valuation.explanation}
                      </p>
                    </div>
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
    </div>
  );
}

export default App;
