import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function TransferPlanner() {
  const [advice, setAdvice] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.transferAdvice().then(setAdvice).catch((e) => setErr(e.message));
  }, []);

  if (err) return <p className="error">{err}</p>;
  if (!advice) return <p className="muted">Evaluating transfers…</p>;

  return (
    <section>
      <h2>Transfer planner</h2>
      <p className="muted">Transfers remaining: <strong>{advice.transfers_remaining}</strong> / 8</p>

      <div className={`verdict ${advice.recommend_transfer ? "act" : "hold"}`}>
        {advice.recommend_transfer ? "Act now" : "Hold"}
      </div>

      {advice.rider_out && advice.rider_in && (
        <div className="swap">
          <div className="ridercard small out">OUT · {advice.rider_out.name}</div>
          <div className="arrow">↓</div>
          <div className="ridercard small in">IN · {advice.rider_in.name}</div>
          <p className="muted small">Projected delta: +{advice.projected_gain.toFixed(0)} pts</p>
        </div>
      )}

      <p className="rationale">{advice.rationale}</p>
    </section>
  );
}
