import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", icon: "⊞" },
  { to: "/resumes", label: "Resumes", icon: "📄" },
  { to: "/jobs", label: "Jobs", icon: "💼" },
  { to: "/screening", label: "Screening", icon: "🔍" },
  { to: "/analytics", label: "Analytics", icon: "📊" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

export default function Layout({ children, loading }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const pageTitle = NAV.find((n) =>
    n.to === "/" ? location.pathname === "/" : location.pathname.startsWith(n.to)
  )?.label || "Dashboard";

  return (
    <div className={`app-shell ${collapsed ? "sidebar-collapsed" : ""}`}>
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">
            <span>AI</span>
          </div>
          {!collapsed && (
            <div className="brand-text">
              <strong>TalentScreen</strong>
              <span>AI Recruitment Platform</span>
            </div>
          )}
          <button
            className="collapse-btn"
            onClick={() => setCollapsed((v) => !v)}
            aria-label="Toggle sidebar"
          >
            {collapsed ? "›" : "‹"}
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
            >
              <span className="nav-icon">{icon}</span>
              {!collapsed && <span className="nav-label">{label}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          {!collapsed && <span className="version-tag">v1.0</span>}
        </div>
      </aside>

      <div className="app-main">
        <header className="app-topbar">
          <div className="topbar-left">
            <h1 className="page-title">{pageTitle}</h1>
          </div>
          <div className="topbar-right">
            {loading && <span className="topbar-loading">Loading…</span>}
            <div className="topbar-avatar">
              <span>R</span>
            </div>
          </div>
        </header>

        <main className="app-content">
          {children}
        </main>
      </div>
    </div>
  );
}
