import React, { useState } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const API_BASE = 'http://localhost:8001';

// Simple SVG Icons
const Icons = {
  Play: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Database: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  ),
  CheckCircle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  XCircle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  AlertCircle: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  Loader: () => (
    <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  BarChart: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  TrendingUp: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  Activity: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  FileText: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  Shield: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  Clock: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

// 📊 DataChart Component - Renders Chart.js visualizations
const DataChart = ({ chartSpec }) => {
  if (!chartSpec || !chartSpec.chart_type) return null;

  const { chart_type, labels, datasets } = chartSpec;

  const chartData = {
    labels,
    datasets,
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: false,
      },
    },
    scales: chart_type !== 'pie' ? {
      y: {
        beginAtZero: true,
      },
    } : undefined,
  };

  const areaOptions = {
    ...options,
    elements: {
      line: {
        tension: 0.4,
      },
    },
    plugins: {
      ...options.plugins,
      filler: {
        propagate: true,
      },
    },
  };

  // Add fill configuration for area charts
  if (chart_type === 'area') {
    chartData.datasets = chartData.datasets.map(ds => ({
      ...ds,
      fill: true,
    }));
  }

  const renderChart = () => {
    switch (chart_type) {
      case 'bar':
        return <Bar data={chartData} options={options} />;
      case 'line':
        return <Line data={chartData} options={options} />;
      case 'area':
        return <Line data={chartData} options={areaOptions} />;
      case 'pie':
        return <Pie data={chartData} options={options} />;
      default:
        return <div className="text-gray-500">Unknown chart type: {chart_type}</div>;
    }
  };

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      <div className="flex items-center gap-2 mb-4">
        <div className="text-purple-600">
          <Icons.BarChart />
        </div>
        <h3 className="text-lg font-bold text-gray-800">
          {chart_type.charAt(0).toUpperCase() + chart_type.slice(1)} Chart
        </h3>
      </div>
      <div style={{ height: '400px' }}>
        {renderChart()}
      </div>
    </div>
  );
};

const BICopilot = () => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [activeTab, setActiveTab] = useState('query');

  const callApi = async (endpoint) => {
    setLoading(true);
    setError('');
    try {
      if (endpoint === 'nl2sql') {
        const res = await fetch(`${API_BASE}/agent/nl2sql`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Query failed');
        setResponse(data);
        setActiveTab('results');
      } else if (endpoint === 'evaluate') {
        const res = await fetch(`${API_BASE}/agent/evaluate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ split: 'test' })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Evaluation failed');
        setMetrics(data.metrics);
        setActiveTab('metrics');
      } else if (endpoint === 'schema_drift') {
        const res = await fetch(`${API_BASE}/agent/schema_drift_eval`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Schema drift evaluation failed');
        setMetrics({
          'baseline.answer_set_exact_match': data.baseline.answer_set_exact_match,
          'drift.answer_set_exact_match': data.drift.answer_set_exact_match,
          'delta_asem': data.delta_asem
        });
        setActiveTab('metrics');
      } else if (endpoint === 'safety') {
        const res = await fetch(`${API_BASE}/agent/safety_eval`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Safety evaluation failed');
        setMetrics({
          guardrail_rate: data.guardrail_rate,
          total_dangerous: data.total_dangerous,
          blocked_dangerous: data.blocked_dangerous
        });
        setActiveTab('metrics');
      }
    } catch (e) {
      console.error(e);
      setError(e.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const renderTable = () => {
    if (!response?.candidates?.length) return null;
    const best = response.candidates.find((c) => c.success) || response.candidates[0];
    if (!best || !best.preview_rows || !best.columns) return null;

    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="bg-gradient-to-r from-blue-50 to-purple-50">
              {best.columns.map((c, idx) => (
                <th key={idx} className="px-4 py-3 text-left text-sm font-semibold text-gray-700 border-b-2 border-blue-200">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {best.preview_rows.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                {row.map((v, j) => (
                  <td key={j} className="px-4 py-3 text-sm text-gray-700 border-b border-gray-200">
                    {String(v)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 text-blue-600">
              <Icons.TrendingUp />
            </div>
            <h1 className="text-4xl font-bold text-gray-800">BI Copilot Agent</h1>
          </div>
          <p className="text-gray-600">Natural language to SQL with LangChain + LangGraph + OpenAI</p>
        </div>

        {/* API Connection Status */}
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icons.Activity />
            <span className="text-sm font-semibold text-gray-700">Backend:</span>
            <code className="text-sm text-blue-800">{API_BASE}</code>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-gray-600">Connected</span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
            <div className="text-red-600">
              <Icons.XCircle />
            </div>
            <p className="text-red-800 flex-1">{error}</p>
            <button
              onClick={() => setError('')}
              className="text-red-600 hover:text-red-800 font-bold text-xl"
            >
              ×
            </button>
          </div>
        )}

        {/* Main Query Interface */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="text-blue-600">
              <Icons.TrendingUp />
            </div>
            <h2 className="text-2xl font-bold text-gray-800">Ask Your Data</h2>
          </div>

          <textarea
            rows={4}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && e.ctrlKey && !loading && callApi('nl2sql')}
            placeholder="e.g., Show me total sales by year, What are the top 5 customers by revenue, List all products with inventory below 100..."
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all mb-4"
            disabled={loading}
          />

          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => callApi('nl2sql')}
              disabled={loading || !question.trim()}
              className="flex-1 min-w-[200px] bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
            >
              {loading ? (
                <>
                  <Icons.Loader />
                  Processing...
                </>
              ) : (
                <>
                  <Icons.Play />
                  Run Query
                </>
              )}
            </button>
            <button
              onClick={() => callApi('evaluate')}
              disabled={loading}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
            >
              {loading ? <Icons.Loader /> : <Icons.BarChart />}
              Evaluate
            </button>
            <button
              onClick={() => callApi('schema_drift')}
              disabled={loading}
              className="bg-gradient-to-r from-orange-600 to-orange-700 hover:from-orange-700 hover:to-orange-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
            >
              {loading ? <Icons.Loader /> : <Icons.AlertCircle />}
              Schema Drift
            </button>
            <button
              onClick={() => callApi('safety')}
              disabled={loading}
              className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 disabled:from-gray-400 disabled:to-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-all flex items-center justify-center gap-2 shadow-md hover:shadow-lg"
            >
              {loading ? <Icons.Loader /> : <Icons.Shield />}
              Safety Check
            </button>
          </div>
        </div>

        {/* Tabs */}
        {(response || metrics) && (
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="border-b border-gray-200">
              <nav className="flex">
                {response && (
                  <button
                    onClick={() => setActiveTab('results')}
                    className={`flex-1 px-6 py-4 text-sm font-semibold transition-colors ${
                      activeTab === 'results'
                        ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-center gap-2">
                      <Icons.FileText />
                      Query Results
                    </div>
                  </button>
                )}
                {metrics && (
                  <button
                    onClick={() => setActiveTab('metrics')}
                    className={`flex-1 px-6 py-4 text-sm font-semibold transition-colors ${
                      activeTab === 'metrics'
                        ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50'
                        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-center gap-2">
                      <Icons.BarChart />
                      Metrics
                    </div>
                  </button>
                )}
              </nav>
            </div>

            {/* Results Tab */}
            {activeTab === 'results' && response && (
              <div className="p-8">
                {/* SQL Display */}
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="text-blue-600">
                      <Icons.Database />
                    </div>
                    <h3 className="text-lg font-bold text-gray-800">Generated SQL</h3>
                  </div>
                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-sm text-green-400 font-mono">{response.chosen_sql}</pre>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-blue-600">
                        <Icons.Clock />
                      </div>
                      <span className="text-xs font-semibold text-blue-800">Time to First Token</span>
                    </div>
                    <div className="text-2xl font-bold text-blue-900">{response.tft_ms.toFixed(1)}ms</div>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-purple-600">
                        <Icons.Activity />
                      </div>
                      <span className="text-xs font-semibold text-purple-800">Time to First Result</span>
                    </div>
                    <div className="text-2xl font-bold text-purple-900">{response.tfr_ms.toFixed(1)}ms</div>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="text-green-600">
                        <Icons.CheckCircle />
                      </div>
                      <span className="text-xs font-semibold text-green-800">Total Latency</span>
                    </div>
                    <div className="text-2xl font-bold text-green-900">{response.total_latency_ms.toFixed(1)}ms</div>
                  </div>
                </div>

                {/* Explanation */}
                {response.explanation && (
                  <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
                    <p className="text-gray-700 italic">{response.explanation}</p>
                  </div>
                )}
                {response.chart && (
                  // ✅ Removed fixed height here. Let the component inside determine the height.
                  <div className="mb-8 bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">Data Visualization</h3>
                    <DataChart chartSpec={response.chart} />
                  </div>
                )}
                {/* Data Table */}
                <div className="mb-6">
                  <h3 className="text-lg font-bold text-gray-800 mb-3">Query Results</h3>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    {renderTable()}
                  </div>
                </div>

                {/* 📊 Enhanced Chart Rendering */}
                {response.chart_spec && (
                  <div className="mb-6">
                    <DataChart chartSpec={response.chart_spec} />
                  </div>
                )}
              </div>
            )}

            {/* Metrics Tab */}
            {activeTab === 'metrics' && metrics && (
              <div className="p-8">
                <div className="flex items-center gap-2 mb-6">
                  <div className="text-purple-600">
                    <Icons.BarChart />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-800">Evaluation Metrics</h3>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(metrics).map(([key, value]) => {
                    const isPercentage = typeof value === 'number' && value <= 1 && value >= 0;
                    const displayValue = typeof value === 'number' 
                      ? (isPercentage ? `${(value * 100).toFixed(2)}%` : value.toFixed(4))
                      : String(value);
                    
                    return (
                      <div key={key} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
                        <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
                          {key.replace(/_/g, ' ')}
                        </div>
                        <div className="text-2xl font-bold text-gray-900">{displayValue}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Powered by LangChain + LangGraph + OpenAI • Built with React & Chart.js</p>
        </div>
      </div>
    </div>
  );
};

export default BICopilot;