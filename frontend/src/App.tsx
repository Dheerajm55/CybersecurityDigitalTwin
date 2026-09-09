import { Navigate, Route, Routes } from "react-router-dom";
import { ShieldAlert, BarChart3, Bot, FileText, Settings } from "lucide-react";
import MainLayout from "./layouts/MainLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import DigitalTwin from "./pages/DigitalTwin";
import Assets from "./pages/Assets";
import AssetDetails from "./pages/AssetDetails";
import AttackPaths from "./pages/AttackPaths";
import Vulnerabilities from "./pages/Vulnerabilities";
import SecurityControls from "./pages/SecurityControls";
import Simulations from "./pages/Simulations";
import Simulator from "./pages/simulator/Simulator";
import ComingSoon from "./pages/ComingSoon";
import { useAuth } from "./contexts/AuthContext";

/** Shown only while session restoration (the startup /auth/me check) is
 * in flight — never long enough to be distracting on a real network, but
 * critical to avoid either flashing the login page before a valid
 * session is confirmed, or flashing the dashboard before an invalid one
 * is rejected. */
function AuthLoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <div className="flex flex-col items-center gap-3 text-subtext">
        <div className="h-8 w-8 rounded-full border-2 border-border border-t-accent animate-spin" />
        <p className="text-sm">Loading CDT2…</p>
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
}

function RedirectIfAuthenticated({ children }: { children: JSX.Element }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <AuthLoadingScreen />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <RedirectIfAuthenticated>
            <Login />
          </RedirectIfAuthenticated>
        }
      />

      <Route
        element={
          <RequireAuth>
            <MainLayout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/twin" element={<DigitalTwin />} />
        <Route path="/assets" element={<Assets />} />
        <Route path="/assets/:id" element={<AssetDetails />} />
        <Route path="/attack-paths" element={<AttackPaths />} />
        <Route path="/vulnerabilities" element={<Vulnerabilities />} />
        <Route path="/controls" element={<SecurityControls />} />
        <Route path="/simulations" element={<Simulations />} />
        <Route path="/simulator" element={<Simulator />} />

        <Route
          path="/threat-intelligence"
          element={
            <ComingSoon
              title="Threat Intelligence"
              subtitle="MITRE ATT&CK, NVD/CVE, and CISA KEV integration."
              icon={ShieldAlert}
              phaseNote="Planned for Phase 6 — Threat Intelligence ingestion (MITRE ATT&CK, NVD/CVE, CISA KEV, OWASP)."
            />
          }
        />
        <Route
          path="/risk-analysis"
          element={
            <ComingSoon
              title="Risk Analysis"
              subtitle="ML-driven risk modeling, comparison, and explainability."
              icon={BarChart3}
              phaseNote="Planned for Phase 4-5 — XGBoost/LightGBM/Random Forest risk models, Isolation Forest anomaly detection, and SHAP explainability. The deterministic Project Risk Score already powers Assets, Digital Twin, and Attack Paths."
            />
          }
        />
        <Route
          path="/advisor"
          element={
            <ComingSoon
              title="AI Security Advisor"
              subtitle="Ask questions about your environment, grounded in real data."
              icon={Bot}
              phaseNote="Planned for Phase 7-8 — RAG pipeline plus a configurable LLM provider (OpenAI-compatible, Anthropic-compatible, Gemini-compatible, or local Ollama) that reasons only over data returned by the Risk Engine, Digital Twin, and Threat Intelligence modules."
            />
          }
        />
        <Route
          path="/reports"
          element={
            <ComingSoon
              title="Reports"
              subtitle="Generate a full security posture report."
              icon={FileText}
              phaseNote="Planned for Phase 10 — exportable PDF security reports covering asset inventory, risk, attack paths, vulnerabilities, and what-if simulation results."
            />
          }
        />
        <Route
          path="/settings"
          element={
            <ComingSoon
              title="Settings"
              subtitle="Manage your account and environment configuration."
              icon={Settings}
              phaseNote="Account and organization settings will land alongside role-based access control."
            />
          }
        />

        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
