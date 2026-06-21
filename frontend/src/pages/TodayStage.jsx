import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function TodayStage() {
  const [stage, setStage] = useState(null);
  const [bonus, setBonus] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api
      .nextStage()
      .then((s) => {
        setStage(s);
        return api.bonus(s.number);
      })
      .then(setBonus)
      .catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="error">{err}</p>;
  if (!stage) return <p className="muted">Loading next stage…</p>;

  return (
    <section>
      <h2>Next stage — #{stage.number}</h2>
      <div className="stagecard">
        <div className="row">
          <span className={`chip type-${stage.type}`}>{stage.type}</span>
          <span className="muted">{stage.date}</span>
        </div>
        <p className="muted small">
          {stage.distance_km} km · climb score {stage.climb_points}
          {stage.is_itt ? " · ITT" : ""}{stage.is_ttt ? " · TTT" : ""}
        </p>
        <Countdown date={stage.date} />
      </div>

      <h3>Bonus pick (points doubled)</h3>
      {bonus?.bonus_rider ? (
        <div className="ridercard highlight">
          <strong>{bonus.bonus_rider.name}</strong>
          <span className="muted"> · +{bonus.marginal_doubled_points.toFixed(0)} marginal pts</span>
        </div>
      ) : (
        <p className="muted">Set your roster on My Team to get a bonus recommendation.</p>
      )}

      {bonus?.equipiers?.length > 0 && (
        <>
          <h3>Équipiers</h3>
          <ul className="riderlist">
            {bonus.equipiers.map((r) => (
              <li key={r.id} className="ridercard small">{r.name}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function Countdown({ date }) {
  const target = new Date(`${date}T11:00:00+02:00`); // CEST/SAST both UTC+2
  const ms = target - new Date();
  if (ms <= 0) return <p className="muted small">Deadline passed.</p>;
  const days = Math.floor(ms / 86400000);
  const hrs = Math.floor((ms % 86400000) / 3600000);
  return <p className="countdown">Deadline in {days}d {hrs}h</p>;
}
