import React, { useState } from 'react';
import UploadForm from './components/UploadForm';
import ResultCard from './components/ResultCard';
import './styles/App.css';

function App() {
  // loading: whether an API request is in progress
  const [loading, setLoading] = useState(false);
  // result: the JSON response from the backend
  const [result, setResult] = useState(null);
  // error: error message to show to the user
  const [error, setError] = useState(null);

  return (
    <div className="app-container">
      <header>
        <h1>Conversation Intelligence Dashboard</h1>
        <p className="subtitle">Upload a text or audio file to analyze conversation and risk.</p>
      </header>

      <main>
        <UploadForm
          onStart={() => {
            setLoading(true);
            setError(null);
            setResult(null);
          }}
          onResult={(res) => {
            setLoading(false);
            setResult(res);
          }}
          onError={(err) => {
            setLoading(false);
            setError(err);
          }}
        />

        {loading && <div className="loading">Analyzing... please wait</div>}

        {error && <div className="error">Error: {error}</div>}

        {result && <ResultCard data={result} />}
      </main>

      <footer>
        <small>Local hackathon demo — communicates with backend at http://localhost:8000</small>
      </footer>
    </div>
  );
}

export default App;
