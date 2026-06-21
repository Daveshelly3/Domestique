import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function MyTeam() {
  const [riders, setRiders] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [transfersUsed, setTransfersUsed] = useState(0);
  const [credits, setCredits] = useState(0);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.riders().then(setRiders);
    api.team().then((t) => {
      setSelected(new Set(t.riders.map((r) => r.id)));
      setTransfersUsed(8 - t.transfers_remaining);
      setCredits(t.credits);
    });
  }, []);

  function toggle(id) {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
    setSaved(false);
  }

  async function save() {
    await api.setTeam({
      rider_ids: [...selected],
      transfers_used: Number(transfersUsed),
      credits: Number(credits),
    });
    setSaved(true);
  }

  return (
    <section>
      <h2>My team (state sync)</h2>
      <p className="muted small">
        Keep this in sync with the Tissot site — the engine reasons from it.
        Selected {selected.size}/8.
      </p>

      <div className="inputs">
        <label>Transfers used
          <input type="number" min="0" max="8" value={transfersUsed}
            onChange={(e) => setTransfersUsed(e.target.value)} />
        </label>
        <label>Credits (★)
          <input type="number" step="0.5" value={credits}
            onChange={(e) => setCredits(e.target.value)} />
        </label>
      </div>

      <button className="primary" onClick={save}>Save team state</button>
      {saved && <span className="saved">Saved ✓</span>}

      <ul className="riderlist pick">
        {riders.map((r) => (
          <li key={r.id}
              className={`ridercard small selectable ${selected.has(r.id) ? "picked" : ""}`}
              onClick={() => toggle(r.id)}>
            <span>{r.name}</span>
            <span className="muted">{r.star_price}★ · {r.archetype.replace("_", "-")}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
