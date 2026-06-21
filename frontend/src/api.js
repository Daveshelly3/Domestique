// Thin API client. Dev proxies /api -> FastAPI (see vite.config.js).
const BASE = import.meta.env.VITE_API_BASE || "/api";

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

async function put(path, body) {
  const r = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

async function post(path) {
  const r = await fetch(`${BASE}${path}`, { method: "POST" });
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}

export const api = {
  squad: () => get("/squad/recommend"),
  stages: () => get("/stages"),
  nextStage: () => get("/stages/next"),
  bonus: (n) => get(`/stages/${n}/bonus`),
  transferAdvice: () => get("/transfers/advice"),
  team: () => get("/team"),
  setTeam: (body) => put("/team", body),
  riders: () => get("/riders"),
  refresh: () => post("/riders/refresh"),
};
