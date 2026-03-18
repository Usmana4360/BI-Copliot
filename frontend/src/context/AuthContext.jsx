import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext(null);
const API = "http://127.0.0.1:8000";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  // ✅ On app load — silently refresh the token if one exists in sessionStorage
  useEffect(() => {
    const stored = sessionStorage.getItem("token");
    if (!stored) {
      setLoading(false);
      return;
    }
    axios.post(
      `${API}/auth/refresh`,
      {},
      { headers: { Authorization: `Bearer ${stored}` } }
    )
    .then(res => {
      // Store the new token — resets the 8-hour clock
      sessionStorage.setItem("token", res.data.access_token);
      setToken(res.data.access_token);
    })
    .catch(() => {
      // Token truly expired — clear it, user must log in again
      sessionStorage.removeItem("token");
      setToken(null);
    })
    .finally(() => setLoading(false));
  }, []);

  const login = (accessToken) => {
    sessionStorage.setItem("token", accessToken);
    setToken(accessToken);
  };

  const logout = () => {
    sessionStorage.removeItem("token");
    setToken(null);
  };

  // ✅ Don't render children until refresh check completes
  // This prevents a flash of the login page on every refresh
  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center",
        justifyContent: "center", background: "#0f1117", color: "#64748b", fontSize: "14px" }}>
        Loading...
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);