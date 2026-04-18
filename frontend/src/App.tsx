import { useState } from 'react';
import './App.css';

interface ParsedDetails {
  year: number;
  manufacturer: string;
  model: string;
  mileage?: number;
  condition?: string;
}

interface ParseResult {
  success: boolean;
  parsed_details?: ParsedDetails;
  error?: string;
}

function App() {
  const [description, setDescription] = useState('');
  const [result, setResult] = useState<ParseResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      // Use environment variable in production, localhost for development
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';
      
      const response = await fetch(`${API_URL}/test-parse`, {
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
    <div className="app">
      <header className="header">
        <div className="logo">
          <span className="logo-icon">🚗</span>
          <span className="logo-text">CarVal Agent</span>
        </div>
      </header>

      <main className="main">
        <div className="hero">
          <h1 className="title">Get Your Car's True Market Value</h1>
          <p className="subtitle">
            Describe your vehicle in plain English. Our AI extracts the details 
            and finds comparable listings instantly.
          </p>
        </div>

        <form className="input-card" onSubmit={handleSubmit}>
          <label className="input-label" htmlFor="car-description">
            Describe Your Vehicle
          </label>
          <textarea
            id="car-description"
            className="input-textarea"
            placeholder="e.g., 2018 Honda Civic with 45,000 miles, excellent condition, clean title..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
          />
          <button
            type="submit"
            className="submit-btn"
            disabled={loading || !description.trim()}
          >
            {loading ? (
              <span className="loading">
                <span className="spinner"></span>
                Analyzing...
              </span>
            ) : (
              'Extract Details'
            )}
          </button>
        </form>

        {result && (
          <div className={`result-card ${result.success ? 'success' : 'error'}`}>
            <h3 className="result-title">
              {result.success ? '✓ Details Extracted' : '✗ Parsing Failed'}
            </h3>
            
            {result.success && result.parsed_details ? (
              <div className="parsed-data">
                <div className="field">
                  <span className="field-label">Year</span>
                  <span className="field-value">{result.parsed_details.year}</span>
                </div>
                <div className="field">
                  <span className="field-label">Make</span>
                  <span className="field-value">{result.parsed_details.manufacturer}</span>
                </div>
                <div className="field">
                  <span className="field-label">Model</span>
                  <span className="field-value">{result.parsed_details.model}</span>
                </div>
                {result.parsed_details.mileage && (
                  <div className="field">
                    <span className="field-label">Mileage</span>
                    <span className="field-value">
                      {result.parsed_details.mileage.toLocaleString()} miles
                    </span>
                  </div>
                )}
                {result.parsed_details.condition && (
                  <div className="field">
                    <span className="field-label">Condition</span>
                    <span className="field-value capitalize">
                      {result.parsed_details.condition}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <p className="error-message">{result.error}</p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
