import React from 'react';
import SummaryGraph from './SummaryGraph';

/*
  ResultCard
  - Displays the summary, risk_detected, call_outcome, and a graph for risk_score
*/
export default function ResultCard({ data }) {
  if (!data) return null;

  const { metadata = {}, summary = '', risk_analysis = {}, advanced_analysis = {} } = data;

  return (
    <div className="result-card">
      <h2>Analysis Result</h2>

      <div className="meta">
        <strong>Input type:</strong> {metadata.input_type}
      </div>

      <div className="summary">
        <h3>Summary</h3>
        <p>{summary}</p>
      </div>

      <div className="risk">
        <h3>Risk</h3>
        <p>
          <strong>Risk detected:</strong> {String(risk_analysis.risk_detected)}
        </p>
        <p>
          <strong>Call outcome:</strong> {advanced_analysis.call_outcome}
        </p>
      </div>

      <div className="graph">
        <SummaryGraph riskScore={advanced_analysis.risk_score || 0} />
      </div>
    </div>
  );
}
