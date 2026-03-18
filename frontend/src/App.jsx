import axios from "axios";
import React, { useState } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, BarElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js';
import { useNavigate } from "react-router-dom";   // ✅ import stays here
import { useAuth } from "./context/AuthContext";   // ✅ moved to top

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
);

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// ---------------------------------------------------------------------------
// SVG icon set
// ---------------------------------------------------------------------------
const Icons = {
  Play: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  CheckCircle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  XCircle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Loader: () => (
    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  BarChart: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Factory: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  ),
  Clock: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
};

// ---------------------------------------------------------------------------
// Suggested manufacturing questions
// ---------------------------------------------------------------------------
const QUICK_QUESTIONS = [
  'Machine downtime by day for the last 30 days',
  'Production lines with lowest OEE this week',
  'Inventory items below reorder point',
  'On-time delivery rate by customer this month',
  'Top 10 work orders by cycle time',
];

// ---------------------------------------------------------------------------
// Chart renderer
// ---------------------------------------------------------------------------
const DataChart = ({ chartSpec }) => {
  if (!chartSpec?.chart_type) return null;
  const { chart_type, labels, datasets } = chartSpec;
  const chartData = { labels, datasets };

  const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' }, title: { display: false } },
    scales: chart_type !== 'pie' ? { y: { beginAtZero: true } } : undefined,
  };

  if (chart_type === 'area') {
    chartData.datasets = chartData.datasets.map(ds => ({ ...ds, fill: true }));
  }

  const renderChart = () => {
    switch (chart_type) {
      case 'bar':   return <Bar  data={chartData} options={baseOptions} />;
      case 'line':  return <Line data={chartData} options={baseOptions} />;
      case 'area':  return <Line data={chartData} options={{ ...baseOptions, elements: { line: { tension: 0.4 } } }} />;
      case 'pie':   return <Pie  data={chartData} options={baseOptions} />;
      default:      return <p className="text-gray-500">Unknown chart type: {chart_type}</p>;
    }
  };

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-purple-600"><Icons.BarChart /></span>
        <h3 className="text-lg font-bold text-gray-800">
          {chart_type.charAt(0).toUpperCase() + chart_type.slice(1)} Chart
        </h3>
      </div>
      <div style={{ height: '380px' }}>{renderChart()}</div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------
const StatCard = ({ icon, label, value, colorClass }) => (
  <div className={`rounded-lg p-4 border ${colorClass}`}>
    <div className="flex items-center gap-2 mb-1">
      {icon}
      <span className="text-xs font-semibold uppercase tracking-wide">{label}</span>
    </div>
    <div className="text-2xl font-bold">{value}</div>
  </div>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const ManufacturingCopilot = () => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();   // ✅ moved INSIDE the component
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');
  // rest of your code unchanged...

  const runQuery = async () => {
  if (!question.trim()) return;
  setLoading(true);
  setError('');
  setResponse(null);
  try {
    const res = await axios.post(
      "http://127.0.0.1:8000/agent/nl2sql",  // ✅ full URL, no /api prefix
      { question },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    setResponse(res.data);  // ✅ axios uses res.data, not res.json()
  } catch (e) {
    // ✅ axios errors come from e.response
    setError(e.response?.data?.detail || e.message || 'An unexpected error occurred.');
  } finally {
    setLoading(false);
  }
};

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && e.ctrlKey && !loading) runQuery();
  };

  const renderTable = () => {
    const r = response?.result;
    if (!r?.success || !r.preview_rows?.length) return null;
    return (
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gradient-to-r from-blue-50 to-indigo-50">
              {r.columns.map((c, i) => (
                <th key={i} className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-indigo-200">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {r.preview_rows.map((row, ri) => (
              <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {row.map((v, ci) => (
                  <td key={ci} className="px-4 py-2 text-sm text-gray-700 border-b border-gray-100">
                    {String(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="text-xs text-gray-400 px-4 py-2">
          Showing up to 20 rows · Query time {response.tfr_ms.toFixed(1)} ms
        </p>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 p-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-3">
            <span className="text-blue-700"><Icons.Factory /></span>
            <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">
              Manufacturing BI Copilot
            </h1>
          </div>
          <p className="text-gray-500 text-sm">
            Ask questions about production, downtime, inventory &amp; fulfilment in plain English
          </p>
        </div>
        <div className="flex items-center justify-center gap-3 mt-4">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-5 py-2 rounded-xl transition-colors"
          >
            <Icons.BarChart /> Dashboard
          </button>
          <button
            onClick={() => { logout(); navigate("/login"); }}
            className="text-sm text-gray-400 hover:text-red-500 border border-gray-200 hover:border-red-300 px-5 py-2 rounded-xl transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <span className="text-red-500"><Icons.XCircle /></span>
            <p className="text-red-800 flex-1 text-sm">{error}</p>
            <button onClick={() => setError('')} className="text-red-500 font-bold text-lg leading-none">×</button>
          </div>
        )}

        {/* Query box */}
        <div className="bg-white rounded-2xl shadow-md p-8 mb-6 border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Ask Your Operations Data</h2>

          {/* Quick-pick buttons */}
          <div className="flex flex-wrap gap-2 mb-4">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                onClick={() => setQuestion(q)}
                className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1 rounded-full border border-blue-200 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>

          <textarea
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g. Show machine downtime by day for the last 30 days …   (Ctrl+Enter to run)"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-transparent outline-none text-sm mb-4 resize-none"
            disabled={loading}
          />

          <button
            onClick={runQuery}
            disabled={loading || !question.trim()}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-semibold py-3 px-8 rounded-xl transition-colors shadow-sm"
          >
            {loading ? <><Icons.Loader /> Analysing…</> : <><Icons.Play /> Run Query</>}
          </button>
        </div>

        {/* Results */}
        {response && (
          <div className="space-y-6">

            {/* Safety warning */}
            {response.safety_blocked && (
              <div className="flex items-center gap-3 p-4 bg-yellow-50 border border-yellow-300 rounded-xl text-yellow-800 text-sm">
                <Icons.Shield />
                <span>One or more generated queries were blocked by the safety guardrail.</span>
              </div>
            )}

            {/* Latency stats */}
            <div className="grid grid-cols-3 gap-4">
              <StatCard
                icon={<span className="text-blue-600"><Icons.Clock /></span>}
                label="LLM latency (TFT)"
                value={`${response.tft_ms.toFixed(0)} ms`}
                colorClass="bg-blue-50 border-blue-200 text-blue-900"
              />
              <StatCard
                icon={<span className="text-indigo-600"><Icons.Clock /></span>}
                label="DB latency (TFR)"
                value={`${response.tfr_ms.toFixed(0)} ms`}
                colorClass="bg-indigo-50 border-indigo-200 text-indigo-900"
              />
              <StatCard
                icon={<span className="text-green-600"><Icons.CheckCircle /></span>}
                label="Total latency"
                value={`${response.total_latency_ms.toFixed(0)} ms`}
                colorClass="bg-green-50 border-green-200 text-green-900"
              />
            </div>

            {/* One-sentence insight */}
            {response.explanation && (
              <div className="p-4 bg-blue-50 border-l-4 border-blue-500 rounded-xl text-gray-700 text-sm italic">
                💡 {response.explanation}
              </div>
            )}

            {/* SQL */}
            {response.chosen_sql && (
              <details className="bg-gray-900 text-green-300 rounded-xl p-4 text-xs" open>
                <summary className="cursor-pointer font-semibold text-green-400 mb-2 select-none">
                  Generated SQL
                </summary>
                <pre className="whitespace-pre-wrap">{response.chosen_sql}</pre>
              </details>
            )}

            {/* Chart */}
            {response.chart && <DataChart chartSpec={response.chart} />}

            {/* Table */}
            {response.result?.success
              ? renderTable()
              : response.result?.error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                    <strong>Execution error:</strong> {response.result.error}
                  </div>
                )
            }
          </div>
        )}

        {/* Footer */}
        <p className="mt-12 text-center text-xs text-gray-400">
          Powered by LangChain · LangGraph · OpenAI · FastAPI · React
        </p>
      </div>
    </div>
  );
};

export default ManufacturingCopilot;
