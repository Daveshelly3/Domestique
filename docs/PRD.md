# PRD — "Domestique" : Tour de France Fantasy by Tissot Strategist

**Owner:** David
**Status:** Draft v0.1 (for review)
**Target launch:** Team-selection open → 4 July 2026 (Grand Départ, Barcelona)
**Last updated:** 21 June 2026

---

## 1. Problem & one-line pitch

The official *Tour de France Fantasy by Tissot* game is a constrained optimization problem dressed as a fantasy game: a budget-limited squad build, a daily points-doubling lever, and a tiny, irreversible pool of transfers across 21 stages. Humans play it on vibes. **Domestique** is a personal decision-support app that learns each stage's profile, projects per-rider fantasy points, and tells you the optimal team to build and exactly when to spend a transfer — maximising total season points.

The app **recommends**; you execute the moves on the Tissot site yourself and keep the app's state in sync manually.

---

## 2. Goals & non-goals

### Goals (v1, by 4 July)
- Recommend the optimal opening 8-rider squad within the 120-star budget and category caps.
- Each stage: recommend the Stage Winner Bonus pick and rider statuses.
- Recommend whether/when to spend each of the 8 transfers, budget-aware.
- Push a notification before every stage deadline.
- Let David manually keep roster, transfers-left, and credits in sync.

### Non-goals (explicitly out for v1)
- **No auto-execution** on the Tissot site (no browser automation against ASO).
- **No multi-user / accounts / sharing** — single-user, just David.
- **Tissot TT time-guess + pre-race quiz optimiser** — lowest priority, deferred to v1.1.
- No betting/odds integration.

---

## 3. The game model (constraints the engine must respect)

Source: official 2026 rules (ASO / fantasybytissot.letour.fr).

| Rule | Value |
|---|---|
| Budget | 120 stars |
| Squad size | Exactly 8 riders (fielding ≤7 in classic mode = 0 points that stage) |
| Category caps | Leaders ≤3, All-rounders ≤5, Sprinters ≤3, Climbers ≤3 |
| Statuses per stage | 1× Stage Winner Bonus (points **doubled**) + 7× Équipiers |
| Transfers | 8 total across the race; a sold rider can only be replaced within freed-up budget |
| Breakaway bonus | +1 point per km a rider is in the break |
| Team time trial | Each qualified rider gets 1/8 of the team's TTT placing points |
| Abandons | Keep points earned before abandon; must spend credits/a transfer to replace |
| Stage 21 caveat | Bonus doubling does **not** apply to final-classification points (GC top-100, end-of-Tour points/KOM/young-rider standings, super-combatif) |
| Status carry-over | Statuses auto-roll to next stage unless changed; editable until stage start |

> The exact base points-per-finish-position scale lives in the game's "Rules" tab and must be captured verbatim into a config file — it is the spine of the projection model.

---

## 4. Objective function

**Maximise expected cumulative season points across all 21 stages.** Because David is chasing the overall ranking (not a single league or stage wins), the engine optimises straight expected value — no variance-dialing or end-game gambling logic in v1.

A rider's **season value** = Σ (expected fantasy points per stage) over all 21 stages, with the bonus-doubling modelled on the stages where that rider is the likely best bonus pick.

---

## 5. System architecture

```
PCS / FirstCycling  ──scrape──▶  Ingest layer  ──▶  Postgres (riders, stages, results, form)
                                                          │
                                                          ▼
                                         Projection engine (rules + ML)
                                         = expected points per rider × stage
                                                          │
                                                          ▼
                                          Optimizer (OR-Tools / PuLP)
                                  ┌───────────────┼────────────────┐
                                  ▼               ▼                ▼
                          Initial squad     Daily bonus +     Transfer-timing
                          (knapsack)        status pick       planner
                                                          │
                                                          ▼
                                FastAPI  ◀──manual state sync──  React PWA (phone)
                                   │                                  ▲
                                   └────────── push (deadline) ───────┘
```

**Frontend:** **React PWA** (Vite + React) deployed on **Vercel** (already connected). Installable to your phone home screen via "Add to Home Screen" — no App Store, no build pipeline. A service worker handles offline caching + web push.
**Backend:** Python **FastAPI** service — scraping, projection, optimization. Hosted on Railway or Render (Python-friendly, built-in cron). A daily scheduled job refreshes scrape → recomputes projections → queues deadline pushes. (Vercel stays frontend-only; long-running scrape/ML doesn't fit its serverless timeouts.)
**DB:** Postgres via **Supabase** (free tier; also stores web-push subscriptions and gives you a console).
**Optimizer:** Google **OR-Tools** (CP-SAT) or **PuLP** for the integer programs.

---

## 6. Prediction engine (hybrid: rules now, ML later)

**Output:** `expected_points[rider][stage]` — a matrix recomputed daily as form and startlist change.

### v1 — rules baseline (ships by 4 July)
1. **Classify each stage** from its profile (flat / hilly / mountain / summit-finish / ITT / TTT / cobbles) using official route data + elevation/categorised-climb counts.
2. **Map rider archetype → stage suitability** (sprinters score on flat, climbers on summit finishes, GC/all-rounders accrue steady GC-position points, etc.).
3. **Weight by recent form**: results from PCS over a trailing window + 2024/2025 TdF history.
4. Convert an expected finish-position distribution into expected points via the captured scoring scale; add modelled breakaway-km and TTT-split contributions.

### v1.1 — ML refinement (during the race)
- **Training set:** reconstruct historical per-stage fantasy points by scraping past TdF stage results (2021–2025) and re-applying the scoring scale. *(This is the main data-engineering cost; it's why ML is phase 2.)*
- **Model:** gradient-boosted trees (LightGBM/XGBoost) predicting per-rider stage points from features (rider form, archetype, stage type, climbs, distance, team strength, days-since-rest, GC position).
- Slots in behind the same `expected_points` interface — the optimizer doesn't change.

---

## 7. Optimizer (David's priority order)

**P1 — Initial squad (highest leverage).** Integer program: maximise Σ season-value subject to budget ≤120, exactly 8 riders, and the four category caps. OR-Tools CP-SAT solves this exactly in milliseconds. Output: the squad + a couple of ranked alternatives with reasoning.

**P2 — Daily bonus + status.** Pick the bonus rider that maximises *marginal* doubled points for that stage's profile; auto-assign the 7 équipiers. Trivial once projections exist.

**P3 — Transfer-timing planner.** The hard, sequential part. v1 heuristic: trigger a transfer only when projected gain over remaining stages exceeds a threshold **and** budget allows, while **reserving transfers for likely abandons**. v1.1: rollout/DP over the remaining schedule. Always surfaces "transfers left" and the cost of acting now vs. holding.

**P4 — Tissot TT time-guess + quizzes.** Deferred. (TT-guess worth up to 200 bonus pts; quizzes give pre-race bonus credits.)

---

## 8. Data sources & scraping

- **Primary:** ProCyclingStats (startlists, rider form/results, stage profiles) + FirstCycling (cross-check, rider history).
- **Official ASO:** 2026 route (21 stage profiles, distances, climbs) + the in-game scoring scale and star prices (captured once team selection opens).
- **Cadence:** daily refresh; on-demand refresh button in-app.
- **Hygiene:** respect robots.txt / rate-limit politely, cache aggressively, single-user personal use. Build a thin adapter layer so a source change doesn't ripple through the engine.

### 8.1 Phased data availability (build now, update later)

The 2026 Tissot startlist + star prices aren't published yet (they typically drop in the final ~week before 4 July). The app is built to handle this without a rebuild:

| Layer | Available now? | Plan |
|---|---|---|
| 2026 route / stage profiles / deadlines | ✅ Yes | Build against real 2026 data now; finalise stage classifier. |
| Scoring scale | ✅ Yes (in rules) | Capture verbatim into config now. |
| 2026 rider startlist + star prices | ❌ Not yet | Scraper polls; ingest the moment they publish. |

- **Seed dataset:** the **2025 Tour** (startlist, prices, results) acts as a stand-in so the optimizer, projections, and full UI are testable end-to-end before real data exists — and doubles as the first ML training slice.
- **Data-readiness state:** the app shows a clear **"Preview — 2025 data"** vs **"2026 Live"** badge. A scraper job watches for the real startlist/prices; on publish it ingests, flips the badge, and **recomputes every recommendation automatically**. It's a data swap, not a code change.
- **Continuous updates thereafter:** daily refresh keeps form, late withdrawals, and any price tweaks current right up to each deadline.

---

## 9. Mobile app — screens

1. **Squad Builder** — recommended opening 8, swap-to-compare, live budget + cap meters, "why this rider" notes.
2. **Today / Next Stage** — stage profile card, recommended bonus pick, status board, deadline countdown.
3. **Transfer Planner** — transfers remaining, "act now vs hold" recommendation + projected point delta, abandon alerts.
4. **My Team (state sync)** — manually set current roster, transfers used, credits; everything the engine reasons from.
5. **Season view** — cumulative points, per-stage log, projection vs actual.

---

## 10. Notifications
- Push before **each stage deadline** (stage start time). Configurable lead time (e.g. 2h + 30min).
- Delivered via **web push** from a PWA service worker. Works out of the box on Android/Chrome. **iOS caveat:** web push only fires if the PWA is added to the home screen and you're on iOS 16.4+. Fallback if that's flaky: the app also offers one-tap "add all 21 stage deadlines to your calendar."
- Both France/Spain (CEST) and South Africa (SAST) are **UTC+2 in July** → no timezone conversion needed.
- Extra triggers: a rostered rider abandons; startlist/price change affecting the squad; refreshed recommendation available.

---

## 11. Data model (sketch)
- **riders**: id, name, team, archetype, star_price, status (active/abandoned)
- **stages**: id, number, date, start_time, type, distance_km, climb_profile, is_ITT, is_TTT
- **results**: rider_id, stage_id, position, breakaway_km, fantasy_points (actual)
- **projections**: rider_id, stage_id, expected_points, model_version
- **my_team**: rider_id, status (bonus/équipier), date_added
- **transfers**: stage_id, rider_out, rider_in, credits_delta, transfers_remaining

---

## 12. Build plan — 2-week sprint to 4 July

**Week 1 (22–28 June):**
- Capture rules/scoring scale + 2026 route into config. Scraper for PCS startlist + form.
- Rules-based projection engine producing the `expected_points` matrix.
- OR-Tools initial-squad optimizer (P1) working end-to-end in the backend.

**Week 2 (29 June–4 July):**
- React PWA: Squad Builder + My Team + Today screens wired to the backend; installable to home screen.
- Daily bonus/status (P2) + transfer heuristic (P3).
- Push notifications + daily cron. Field-test the opening squad before lock.

**During the race (v1.1):** historical-points reconstruction → ML model → transfer-planner upgrade → TT-guess/quiz helper (P4).

---

## 13. Risks, assumptions, open questions

**Risks**
- *Scope vs runway* — native-mobile + full scope in 2 weeks is tight. Mitigation: rules-first engine, Expo, and a clear cut line: **if time slips, ship P1 + P2 + push by 4 July and add P3 in week 1 of the race.**
- *Scraping fragility / ToS* — keep it personal-use, polite, behind an adapter.
- *Scoring-scale accuracy* — the whole model depends on capturing the exact in-game scale; verify against the first stage's actual points.
- *Startlist/prices not live yet* — team selection opens just before the Grand Départ; the builder can be tested only once prices publish.

**Assumptions to confirm**
- Single-user, personal use (no auth/accounts).
- You'll manually enter team state rather than import from the site.
- "Classic" game mode (not any alternate mode).

**Open questions for you**
1. Backend host — **Railway** or **Render** for the Python service? (Frontend goes on Vercel; the Python scrape/ML/optimizer needs a long-running host alongside it.)
2. Are you OK with the **cut line** above (P1+P2+push guaranteed by 4 July, P3 just after) if week 2 gets tight?
3. ~~iOS/Android/both~~ — resolved: web app / PWA, platform-agnostic. (Just note the iOS web-push caveat in §10.)
