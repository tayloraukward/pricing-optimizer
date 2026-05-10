import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface SaveValuationButtonProps {
  parsedDetails: any;
  valuationResult: any;
  onSaveSuccess?: () => void;
}

export default function SaveValuationButton({ 
  parsedDetails, 
  valuationResult,
  onSaveSuccess 
}: SaveValuationButtonProps) {
  const [showTitleDialog, setShowTitleDialog] = useState(false);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSignIn, setShowSignIn] = useState(false);
  
  const { user, getAccessToken } = useAuth();

  // Debug user state
  useEffect(() => {
    console.log('💾 SaveValuationButton: User state:', user ? `Logged in as ${user.email}` : 'Not logged in');
  }, [user]);

  const handleSaveClick = () => {
    console.log('💾 SaveValuationButton: Save clicked, user:', user ? 'authenticated' : 'not authenticated');
    
    if (!user) {
      console.log('💾 SaveValuationButton: Showing sign-in prompt');
      setShowSignIn(true);
      return;
    }
    
    // Generate a default title from the parsed details
    const defaultTitle = parsedDetails 
      ? `${parsedDetails.year} ${parsedDetails.manufacturer} ${parsedDetails.model}`
      : 'Vehicle Valuation';
    
    setTitle(defaultTitle);
    setShowTitleDialog(true);
  };

  const handleSave = async () => {
    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const API_URL = import.meta.env.VITE_API_URL || '';
      const token = getAccessToken();
      
      console.log('💾 SaveValuationButton: API_URL:', API_URL);
      console.log('💾 SaveValuationButton: Token exists:', !!token);
      
      console.log('💾 SaveValuationButton: Saving data:', { title: title.trim(), parsedDetails, valuationResult });
      
      const response = await fetch(`${API_URL}/valuations/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: title.trim(),
          parsed_car: parsedDetails,
          valuation_result: valuationResult
        })
      });

      console.log('💾 SaveValuationButton: Response status:', response.status);
      
      if (response.ok) {
        setShowTitleDialog(false);
        onSaveSuccess?.();
      } else {
        const data = await response.json();
        console.error('💾 SaveValuationButton: Error response:', data);
        setError(data.detail || 'Failed to save valuation');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Save Button */}
      <button
        onClick={handleSaveClick}
        className="flex items-center gap-2 bg-white/10 hover:bg-white/20 border border-white/20 text-white px-4 py-2 rounded-lg transition-all"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
        Save Valuation
      </button>

      {/* Sign In Prompt Modal */}
      {showSignIn && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 w-full max-w-sm text-center">
            <div className="w-12 h-12 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Sign In Required</h3>
            <p className="text-white/70 mb-4 text-sm">
              Please sign in to save your valuations and access them later.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowSignIn(false)}
                className="flex-1 bg-white/10 hover:bg-white/20 text-white py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowSignIn(false);
                  // Emit event to show sign in modal from parent
                  window.dispatchEvent(new CustomEvent('show-signin'));
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg transition-colors"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Title Dialog */}
      {showTitleDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-white mb-4">Save Valuation</h3>
            
            {error && (
              <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 mb-4">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm text-white/70 mb-1">Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-black/20 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-white/40"
                placeholder="e.g., 2018 Honda Civic EX"
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowTitleDialog(false)}
                className="flex-1 bg-white/10 hover:bg-white/20 text-white py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-500 text-white py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
