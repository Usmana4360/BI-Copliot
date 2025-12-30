import React, { useState } from "react";
import axios from "axios";
import { Line, Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend);

export default function QueryConsole({ onMetrics }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const callApi = async (endpoint) => {
    setLoading(true);
    setError("");
    try {
      if (endpoint === "nl2sql") {
        const res = await axios.post("/api/agent/nl2sql", { question });
        setResponse(res.data);
      } else if (endpoint === "evaluate") {
        const res = await axios.post("/api/agent/evaluate", { split: "test" });
        onMetrics(res.data.metrics);
      } else if (endpoint === "schema_drift") {
        const res = await axios.post("/api/agent/schema_drift_eval");
        onMetrics({
          "baseline.answer_set_exact_match": res.data.baseline.answer_set_exact_match,
          "drift.answer_set_exact_match": res.data.drift.answer_set_exact_match,
          "delta_asem": res.data.delta_asem,
        });
      } else if (endpoint === "safety") {
        const res = await axios.post("/api/agent/safety_eval");
        onMetrics({
          guardrail_rate: res.data.guardrail_rate,
          total_dangerous: res.data.total_dangerous,
          blocked_dangerous: res.data.blocked_dangerous,
        });
      }
    } catch (e) {
      console.error(e);
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const renderTable = () => {
    if (!response?.candidates?.length) return null;
    const best = response.candidates.find((c) => c.success) || response.candidates[0];
    if (!best || !best.preview_rows || !best.columns) return null;

    return (
      <table border="1" cellPadding="4" style={{ borderCollapse: "collapse", marginTop: "1rem" }}>
        <thead>
          <tr>
            {best.columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {best.preview_rows.map((row, i) => (
            <tr key={i}>
              {row.map((v, j) => (
                <td key={j}>{String(v)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  const renderChart = () => {
    if (!response?.chart || !response?.candidates?.length) return null;
    const best = response.candidates.find((c) => c.success) || response.candidates[0];
    if (!best || !best.preview_rows || !best.columns) return null;

    const { chart_type, x, y } = response.chart;
    const xIdx = best.columns.indexOf(x);
    const yIdx = best.columns.indexOf(y);
    if (xIdx === -1 || yIdx === -1) return null;

    const labels = best.preview_rows.map((r) => String(r[xIdx]));
    const dataValues = best.preview_rows.map((r) => Number(r[yIdx]));

    const data = {
      labels,
      datasets: [
        {
          label: `${y} by ${x}`,
          data: dataValues,
        },
      ],
    };

    const commonProps = {
      data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    };

    return (
      <div style={{ height: "300px", marginTop: "1rem" }}>
        {chart_type === "line" ? <Line {...commonProps} /> : <Bar {...commonProps} />}
      </div>
    );
  };

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <textarea
        rows={3}
        style={{ width: "100%", padding: "0.5rem" }}
        placeholder="Ask a question about your data..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
        <button disabled={loading} onClick={() => callApi("nl2sql")}>
          Run Query
        </button>
        <button disabled={loading} onClick={() => callApi("evaluate")}>
          Evaluate (test)
        </button>
        <button disabled={loading} onClick={() => callApi("schema_drift")}>
          Schema Drift Eval
        </button>
        <button disabled={loading} onClick={() => callApi("safety")}>
          Safety Eval
        </button>
      </div>
      {loading && <div>Working...</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      {response && (
        <div style={{ marginTop: "1rem" }}>
          <h3>Chosen SQL</h3>
          <pre style={{ background: "#f5f5f5", padding: "0.5rem" }}>{response.chosen_sql}</pre>
          <div style={{ fontSize: "0.9rem", color: "#777" }}>
            TFT: {response.tft_ms.toFixed(1)} ms | TFR: {response.tfr_ms.toFixed(1)} ms | Total:{" "}
            {response.total_latency_ms.toFixed(1)} ms
          </div>
          {response.explanation && (
            <p style={{ marginTop: "0.5rem", fontStyle: "italic" }}>{response.explanation}</p>
          )}
          {renderTable()}
          {renderChart()}
        </div>
      )}
    </div>
  );
}
