import { useEffect, useState } from "react";
import { api } from "../api.js";

const CAPS = { leader: 3, all_rounder: 5, sprinter: 3, climber: 3 };

export default function SquadBuilder() {
  const [squad, setSquad] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.squad().then(setSquad).catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="error">Could not load squad: {err}</p>;
  if (!squad) return <p className="muted">Optimising opening squad…</p>;

  return (
    <section>
      <h2>Recommended opening 8</h2>
      <div className="meters">
        <Meter label="Budget" value={squad.total_cost} max={squad.budget} unit="★" />
        {Object.entries(CAPS).map(([k, cap]) => (
          <Meter key={k} label={k.replace("_", "-")} value={squad.caps_used[k] || 0} max={cap} />
        ))}
      </div>
      <p className="muted">Projected season value: {squad.total_season_value.toFixed(0)} pts</p>

      <ul className="riderlist">
        {squad.riders.map((r) => (
          <li key={r.rider.id} className="ridercard">
            <div className="row">
              <strong>{r.rider.name}</strong>
              <span className="price">{r.rider.star_price}★</span>
            </div>
            <div className="row small">
              <span className={`chip ${r.rider.archetype}`}>{r.rider.archetype.replace("_", "-")}</span>
              <span className="muted">{r.season_value.toFixed(0)} pts</span>
            </div>
            <p className="why">{r.reason}</p>
          </li>
        ))}
      </ul>

      {squad.alternatives?.length > 0 && (
        <details className="alts">
          <summary>Ranked alternatives</summary>
          {squad.alternatives.map((alt, i) => (
            <p key={i} className="muted small">#{i + 2}: {alt.join(", ")}</p>
          ))}
        </details>
      )}
    </section>
  );
}

function Meter({ label, value, max, unit = "" }) {
  const pct = Math.min(100, (value / max) * 100);
  const over = value > max;
  return (
    <div className="meter">
      <div className="meter-label">{label}: {value}{unit} / {max}{unit}</div>
      <div className="meter-track">
        <div className={`meter-fill ${over ? "over" : ""}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
