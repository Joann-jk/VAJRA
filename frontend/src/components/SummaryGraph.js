import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Register chart components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

export default function SummaryGraph({ riskScore = 0 }) {
  // riskScore expected between 0 and 1; convert to percent for display
  const percent = Math.round(riskScore * 100);

  const data = {
    labels: ['Risk Score'],
    datasets: [
      {
        label: 'Risk (%)',
        data: [percent],
        backgroundColor: ['rgba(255,99,132,0.6)'],
      },
    ],
  };

  const options = {
    indexAxis: 'y',
    scales: {
      x: { min: 0, max: 100 },
    },
    plugins: {
      legend: { display: false },
      title: { display: true, text: `Risk score: ${percent}%` },
    },
    responsive: true,
  };

  return (
    <div style={{ maxWidth: '500px' }}>
      <Bar data={data} options={options} />
    </div>
  );
}
