import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface SavedValuation {
  id: string;
  title: string;
  parsed_car: {
    year: number;
    manufacturer: string;
    model: string;
    price?: number;
    mileage?: number;
  };
  valuation_result: {
    fair_price: number;
    price_range_low: number;
    price_range_high: number;
    confidence: 'low' | 'medium' | 'high';
    explanation: string;
  };
  created_at: string;
}

interface SavedValuationsListProps {
  onSelect?: (valuation: SavedValuation) => void;
}

export default function SavedValuationsList({ onSelect }: SavedValuationsListProps) {
  const [valuations, setValuations] = useState<SavedValuation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user, getAccessToken } = useAuth();

  const API_URL = import.meta.env.VITE_API_URL || '';

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    fetchValuations();
  }, [user]);

  const fetchValuations = async () => {
    try {
      setLoading(true);
      setError('');
      
      const token = getAccessToken();
      
      const response = await fetch(`${API_URL}/valuations`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setValuations(data.valuations || []);
      } else {
        setError('Failed to load saved valuations');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  const deleteValuation = async (id: string) => {
    if (!confirm('Are you sure you want to delete this valuation?')) return;
    
    try {
      const token = getAccessToken();
      
      const response = await fetch(`${API_URL}/valuations/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setValuations(valuations.filter(v => v.id !== id));
      } else {
        alert('Failed to delete valuation');
      }
    } catch (err) {
      alert('Network error');
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(price);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-400 bg-green-500/20 border-green-500/30';
      case 'medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'low': return 'text-red-400 bg-red-500/20 border-red-500/30';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  if (!user) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
        <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">Sign In to Save</h3>
        <p className="text-white/60 text-sm">
          Create an account or sign in to save and view your vehicle valuations.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-white/20 border-t-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
        <p className="text-red-400 mb-3">{error}</p>
        <button 
          onClick={fetchValuations}
          className="text-sm text-red-400 hover:text-red-300 underline"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (valuations.length === 0) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
        <div className="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-6 h-6 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">No Saved Valuations</h3>
        <p className="text-white/60 text-sm">
          You haven't saved any valuations yet. Start by getting a vehicle valuation!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-white">
          Saved Valuations ({valuations.length})
        </h3>
        <button
          onClick={fetchValuations}
          className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {valuations.map((valuation) => (
        <div 
          key={valuation.id}
          className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors group"
        >
          <div className="flex justify-between items-start mb-2">
            <div className="flex-1">
              <h4 className="font-medium text-white mb-1">{valuation.title}</h4>
              <p className="text-sm text-white/60">
                {valuation.parsed_car.year} {valuation.parsed_car.manufacturer} {valuation.parsed_car.model}
              </p>
            </div>
            <div className="flex gap-2">
              {onSelect && (
                <button
                  onClick={() => onSelect(valuation)}
                  className="text-blue-400 hover:text-blue-300 p-1"
                  title="View Details"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
              )}
              <button
                onClick={() => deleteValuation(valuation.id)}
                className="text-red-400 hover:text-red-300 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-white">
                {formatPrice(valuation.valuation_result.fair_price)}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getConfidenceColor(valuation.valuation_result.confidence)}`}>
                {valuation.valuation_result.confidence.toUpperCase()} CONFIDENCE
              </span>
            </div>
            <span className="text-sm text-white/40">
              {formatDate(valuation.created_at)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
