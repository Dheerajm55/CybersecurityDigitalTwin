import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Share2,
  Server,
  Route as RouteIcon,
  ShieldAlert,
  BarChart3,
  FlaskConical,
  Crosshair,
  Bot,
  Bug,
  ShieldCheck,
  FileText,
  Settings as SettingsIcon,
  LogOut,
  Shield,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/twin", label: "Digital Twin", icon: Share2 },
  { to: "/assets", label: "Assets", icon: Server },
  { to: "/attack-paths", label: "Attack Paths", icon: RouteIcon },
  { to: "/threat-intelligence", label: "Threat Intelligence", icon: ShieldAlert },
  { to: "/risk-analysis", label: "Risk Analysis", icon: BarChart3 },
  { to: "/simulations", label: "Simulations", icon: FlaskConical },
  { to: "/simulator", label: "Attack & Defense Simulator", icon: Crosshair },
  { to: "/advisor", label: "AI Security Advisor", icon: Bot },
  { to: "/vulnerabilities", label: "Vulnerabilities", icon: Bug },
  { to: "/controls", label: "Security Controls", icon: ShieldCheck },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export default function MainLayout() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex bg-bg">
      <aside className="w-60 shrink-0 border-r border-border bg-surface flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-border">
          <div className="rounded-md bg-accent/10 p-1.5">
            <Shield size={18} className="text-accent" />
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-text">CDT2</p>
            <p className="text-[11px] text-subtext leading-tight">Cybersecurity Digital Twin</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-3">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 mx-2 mb-0.5 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-accent/10 text-accent font-medium"
                    : "text-subtext hover:bg-bg hover:text-text"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border p-3">
          <div className="flex items-center justify-between px-1">
            <div>
              <p className="text-xs font-medium text-text truncate max-w-[130px]">
                {user?.full_name || "Analyst"}
              </p>
              <p className="text-[11px] text-subtext truncate max-w-[130px]">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="text-subtext hover:text-danger p-1.5 rounded-md hover:bg-bg transition-colors"
              title="Log out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <Outlet />
      </main>
    </div>
  );
}
