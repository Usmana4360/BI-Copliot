import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";

const API = "http://127.0.0.1:8000";

const KPI_META = {
  oee:             { label: "OEE",             unit: "%",    color: "#7f77dd" },
  mtbf:            { label: "MTBF",            unit: " hrs", color: "#1d9e75" },
  mttr:            { label: "MTTR",            unit: " hrs", color: "#1d9e75" },
  downtime:        { label: "Downtime",        unit: " hrs", color: "#e24b4a" },
  scrap_rate:      { label: "Scrap rate",      unit: "%",    color: "#378add" },
  production_rate: { label: "Production rate", unit: " units", color: "#378add" },
};

const DONUT_COLORS = ["#e24b4a", "#378add", "#1d9e75", "#7f77dd", "#ef9f27"];

export default function DashboardPage() {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const [kpis, setKpis] = useState(null);
  const [trend, setTrend] = useState([]);
  const [downtime, setDowntime] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const headers = { Authorization: `Bearer ${token}` };

  // ✅ Single useEffect only
  useEffect(() => {
    Promise.all([
      axios.get(`${API}/kpis/summary`, { headers }),
      axios.get(`${API}/kpis/oee-trend`, { headers }),
      axios.get(`${API}/kpis/downtime-breakdown`, { headers }),
    ])
    .then(([kpiRes, trendRes, downtimeRes]) => {
      setKpis(kpiRes.data);
      setTrend(trendRes.data);
      setDowntime(downtimeRes.data);
    })
    .catch((e) => {
      setError(e.response?.data?.detail || "Failed to load dashboard data.");
    })
    .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#0f1117", padding: "20px", fontFamily: "sans-serif" }}>

      {/* Top bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ color: "#e2e8f0", fontWeight: 500, fontSize: "16px" }}>BI Copilot</span>
          <span style={{ fontSize: "11px", background: "#1e2330", color: "#7f77dd",
            border: "0.5px solid #534ab7", borderRadius: "20px", padding: "3px 10px" }}>
            Manufacturing
          </span>
        </div>
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button onClick={() => navigate("/")}
            style={{ fontSize: "12px", color: "#94a3b8", background: "#1e2330",
              border: "0.5px solid #2d3748", borderRadius: "6px", padding: "5px 14px", cursor: "pointer" }}>
            AI Query
          </button>
          <button onClick={() => { logout(); navigate("/login"); }}
            style={{ fontSize: "12px", color: "#e24b4a", background: "#1e2330",
              border: "0.5px solid #e24b4a", borderRadius: "6px", padding: "5px 14px", cursor: "pointer" }}>
            Logout
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div style={{ background: "#2a1a1a", border: "0.5px solid #e24b4a", borderRadius: "8px",
          padding: "12px 16px", color: "#e24b4a", fontSize: "13px", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: "#64748b", textAlign: "center", marginTop: "60px" }}>Loading KPIs...</p>
      ) : (
        <>
          {/* KPI Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "16px" }}>
            {kpis && Object.entries(KPI_META).map(([key, meta]) => {
              const value = kpis[key];
              return (
                <div key={key} style={{ background: "#1a1f2e", border: "0.5px solid #2d3748",
                  borderRadius: "10px", padding: "14px 16px" }}>
                  <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "6px",
                    textTransform: "uppercase", letterSpacing: "0.05em" }}>{meta.label}</div>
                  <div style={{ fontSize: "22px", fontWeight: 500, color: "#e2e8f0", marginBottom: "4px" }}>
                    {value != null ? `${value}${meta.unit}` : "—"}
                  </div>
                  <div style={{ height: "3px", background: "#2d3748", borderRadius: "2px", marginTop: "10px" }}>
                    <div style={{ height: "3px", borderRadius: "2px", background: meta.color,
                      width: `${Math.min((value || 0), 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Charts Row */}
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: "12px" }}>

            {/* OEE Trend Bar Chart */}
            <div style={{ background: "#1a1f2e", border: "0.5px solid #2d3748", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "12px", fontWeight: 500 }}>
                OEE trend — last 7 days
              </div>
              {trend.length === 0 ? (
                <p style={{ color: "#475569", fontSize: "12px", textAlign: "center", padding: "40px 0" }}>
                  No production data for last 7 days
                </p>
              ) : (
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={trend} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                    <XAxis dataKey="day" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: "#0f1117", border: "0.5px solid #2d3748",
                        borderRadius: "6px", fontSize: "12px", color: "#e2e8f0" }}
                      cursor={{ fill: "#2d3748" }}
                    />
                    <Bar dataKey="oee" fill="#534ab7" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Downtime Donut */}
            <div style={{ background: "#1a1f2e", border: "0.5px solid #2d3748", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "12px", fontWeight: 500 }}>
                Downtime by cause
              </div>
              {downtime.length === 0 ? (
                <p style={{ color: "#475569", fontSize: "12px", textAlign: "center", padding: "24px 0" }}>
                  No downtime data available
                </p>
              ) : (
                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <PieChart width={90} height={90}>
                    <Pie data={downtime} cx={40} cy={40} innerRadius={26} 
                      outerRadius={40} dataKey="value" strokeWidth={0}>
                      {downtime.map((_, i) => (
                        <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                      ))}
                    </Pie>
                  </PieChart>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {downtime.map((d, i) => (
                      <div key={i} style={{ display: "flex", alignItems: "center", gap: "6px",
                        fontSize: "11px", color: "#94a3b8" }}>
                        <div style={{ width: "8px", height: "8px", borderRadius: "50%",
                          background: DONUT_COLORS[i % DONUT_COLORS.length], flexShrink: 0 }} />
                        {d.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}