import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "./api.js";
import SquadBuilder from "./pages/SquadBuilder.jsx";
import TodayStage from "./pages/TodayStage.jsx";
import TransferPlanner from "./pages/TransferPlanner.jsx";
import MyTeam from "./pages/MyTeam.jsx";
import SeasonView from "./pages/SeasonView.jsx";

const TABS = [
  { to: "/squad", label: "Squad" },
  { to: "/today", label: "Today" },
  { to: "/transfers", label: "Transfers" },
  { to: "/team", label: "My Team" },
  { to: "/season", label: "Season" },
];

export default function App() {
  const [mode, setMode] = useState("preview_2025");

  useEffect(() => {
    api.team().then((t) => setMode(t.data_mode)).catch(() => {});
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <h1>Domestique</h1>
        <span className={`badge ${mode === "live_2026" ? "live" : "preview"}`}>
          {mode === "live_2026" ? "2026 Live" : "Preview — 2025 data"}
        </span>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/squad" replace />} />
          <Route path="/squad" element={<SquadBuilder />} />
          <Route path="/today" element={<TodayStage />} />
          <Route path="/transfers" element={<TransferPlanner />} />
          <Route path="/team" element={<MyTeam />} />
          <Route path="/season" element={<SeasonView />} />
        </Routes>
      </main>

      <nav className="tabbar">
        {TABS.map((t) => (
          <NavLink key={t.to} to={t.to} className={({ isActive }) => (isActive ? "tab active" : "tab")}>
            {t.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
