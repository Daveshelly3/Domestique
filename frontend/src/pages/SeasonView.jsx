import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function SeasonView() {
  const [stages, setStages] = useState([]);

  useEffect(() => {
    api.stages().then(setStages);
  }, []);

  return (
    <section>
      <h2>Season view</h2>
      <p className="muted small">
        Cumulative points and projection-vs-actual populate here once stage
        results are ingested during the race.
      </p>
      <ul className="riderlist">
        {stages.map((s) => (
          <li key={s.id} className="ridercard small">
            <div className="row">
              <strong>Stage {s.number}</strong>
              <span className={`chip type-${s.type}`}>{s.type}</span>
            </div>
            <span className="muted small">{s.date} · {s.distance_km} km</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
