import React from "react";

export default function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  return (
    <div style={{ marginTop: "2rem" }}>
      <h2>Evaluation Metrics</h2>
      <table border="1" cellPadding="4" style={{ borderCollapse: "collapse" }}>
        <tbody>
          {Object.entries(metrics).map(([k, v]) => (
            <tr key={k}>
              <td>{k}</td>
              <td>{typeof v === "number" ? v.toFixed(4) : String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
