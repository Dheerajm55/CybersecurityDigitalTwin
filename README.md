# CDT2 (Cybersecurity Digital Twin)

A defensive cybersecurity web application that models an organization's digital
environment as a graph, computes explainable risk scores, simulates
hypothetical attack paths, and recommends security improvements.

**This is a defensive tool.** It does not perform real credential theft,
phishing delivery, malware, exploitation, privilege escalation, or
unauthorized network attacks. All "attack simulations" are mathematical
graph analysis over asset data you enter or import — never actions against
real systems.

See `information.txt` in the project root for an honest, plain-language
summary of exactly what is and isn't implemented in this build.

---

## What's implemented in this build

This repository currently implements **Phase 1 and Phase 2** of the full
42-section master specification (see `information.txt`), plus working
pieces of Phase 3 (deterministic attack-path engine) and Phase 9
(what-if simulator), so the core demo loop — dashboard → digital twin →
simulate compromise → why? → what-if → risk change — genuinely works
end to end on synthetic data.

| Area | Status |
|---|---|
| React/TypeScript/Vite/Tailwind frontend | ✅ Implemented |
| FastAPI backend, JWT auth, Argon2 hashing | ✅ Implemented |
| PostgreSQL-compatible schema (SQLite by default) | ✅ Implemented |
| Asset CRUD + relationships | ✅ Implemented |
| Digital Twin graph (React Flow) | ✅ Implemented |
| Deterministic "Project Risk Score" engine | ✅ Implemented |
| NetworkX attack-path engine (Dijkstra) | ✅ Implemented |
| What-If simulator | ✅ Implemented |
| Vulnerability tracking | ✅ Implemented |
| Security controls tracking | ✅ Implemented |
| Synthetic demo data (auto-seeded) | ✅ Implemented |
| Neo4j graph mirror | ⛔ Not built (NetworkX used instead — see ARCHITECTURE.md) |
| ML models (XGBoost, LightGBM, Random Forest, Isolation Forest, Autoencoder) | ⛔ Not built |
| Graph neural networks (GraphSAGE, GAT, GCN) | ⛔ Not built |
| Transformer text classification / sentence embeddings | ⛔ Not built |
| LLM AI Security Advisor + RAG | ⛔ Not built |
| Threat intelligence ingestion (MITRE ATT&CK, NVD/CVE, CISA KEV) | ⛔ Not built |
| **Cyber Attack & Defense Simulator (`/simulator`)** | ✅ Implemented (Phases 1-9 + 2 futuristic features — see `SIMULATOR.md`) |
| PDF report generation | ⛔ Not built |

Everything marked "Not built" has a stub page in the UI explaining what
phase it belongs to, rather than fake or hardcoded output.

---

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt --break-system-packages   # or omit the flag in a venv
cp ../.env.example .env            # edit values as needed; defaults work out of the box
uvicorn app.main:app --reload --port 8000
```

The backend creates its SQLite database file and seeds deterministic
synthetic demo data automatically on first run — no manual setup step
required. A demo login is created:

```
email:    demo@digitaltwin.local
password: DemoPass123!
```

This is a **development/demo credential only** — see "Authentication"
below for how it's seeded and why it's safe to leave in this codebase.

API docs are available at `http://localhost:8000/docs` (FastAPI's
built-in Swagger UI).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` to the
backend at `http://localhost:8000` (see `vite.config.ts`).

### 3. Try the demo flow

1. Sign in with the pre-filled demo credentials on the login screen.
2. **Dashboard** — see the security score and top risky assets.
3. **Digital Twin** — open the graph, click the "Corporate Email Account"
   node, click **Simulate Compromise**. It computes the actual highest-risk
   path (`Email → GitHub → Cloud → Database`) using Dijkstra's algorithm
   over the seeded relationships, and explains why.
4. **Simulations** — pick the Customer Database asset and apply
   "Enable MFA," then "Patch open vulnerabilities," and watch the
   simulated risk score drop, matching the demo flow in the original spec.
5. **Attack & Defense Simulator** (`/simulator`) — click **Templates**,
   load "College Network," click the Attacker node, pick **Credential
   Compromise Simulation**, click **Simulate**. Watch the path animate
   and the target turn red. Click the compromised node and apply
   **Enable MFA** — watch the risk chain drop and the node recover.
   See `SIMULATOR.md` for the full module writeup.

---

## Project structure

```
CDT2/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, startup seeding
│   │   ├── core/                # config, JWT/password security
│   │   ├── database/            # SQLAlchemy session/engine
│   │   ├── models/               # ORM models (assets, vulns, controls, ...)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # risk engine, graph engine, seed data
│   │   ├── scenario_engine/       # data-driven attack scenario library (simulator)
│   │   ├── simulation_engine/     # simulator components, templates, deterministic engine
│   │   ├── case_studies/          # real-world security case study library (simulator)
│   │   ├── api/routes/           # auth, assets, twin, risk, vulnerabilities, controls, events, simulator
│   │   ├── ml/                   # placeholder for Phase 4-5 models
│   │   └── graph/                # placeholder for Neo4j integration
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/                # one file per nav item
│       ├── pages/simulator/       # Cyber Attack & Defense Simulator (/simulator)
│       ├── components/           # GraphViewer, AssetTable, MetricCard, RiskBadge, ...
│       ├── layouts/              # sidebar layout
│       ├── services/api.ts       # typed API client
│       └── types/                # shared TypeScript types
├── data/synthetic/                # reserved for exported synthetic datasets
├── .env.example
├── README.md            (this file)
├── ARCHITECTURE.md
├── ML_MODELS.md
├── SECURITY.md
├── API.md
├── SIMULATOR.md
└── information.txt
```

---

## Environment variables

See `.env.example` at the project root for the full list. Nothing needs
to be filled in to run the app locally — every value has a safe default
or is only required once you build out a later phase (LLM provider,
Neo4j, NVD API key, etc.).

## Database setup

**Default (zero setup):** SQLite file at `backend/cyber_twin.db`, created
automatically.

**PostgreSQL:** set `DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname`
in `.env` before first run. Tables are created automatically via
SQLAlchemy on startup; no separate migration step exists yet in this
build (see ARCHITECTURE.md for the planned Alembic migration path).

## Neo4j setup

Not required to run this build — attack-path analysis uses NetworkX
directly against the relational data. `NEO4J_URI` / `NEO4J_USERNAME` /
`NEO4J_PASSWORD` are reserved in `.env.example` for when a Neo4j mirror
is added (see ARCHITECTURE.md).

---

## Authentication

**Demo credentials** (development only — see below):

```
email:    demo@digitaltwin.local
password: DemoPass123!
```

### How it works

- **Backend**: `POST /api/auth/login` verifies the submitted password
  against an Argon2 hash (`app/core/security.py`) and returns a signed
  JWT (`app/core/security.py::create_access_token`) plus the user
  profile. `GET /api/auth/me` is the single source of truth for "is this
  token still valid, and who does it belong to" — it decodes the JWT,
  re-fetches the user from the database (so a deleted/disabled account
  is rejected even with an otherwise-valid token), and returns 401 for
  anything missing, malformed, or expired. Every protected backend route
  uses the same `get_current_user` dependency (`app/api/deps.py`) — there
  is only one place JWTs get decoded.
- **Frontend**: `AuthContext` (`src/contexts/AuthContext.tsx`) is the
  single source of truth for auth state (`user`, `token`,
  `isAuthenticated`, `isLoading`). On app load it never trusts the
  locally-stored user object on its own — it always calls `GET
  /api/auth/me` to confirm the stored token is still valid before
  treating the session as authenticated. While that check is in flight,
  `App.tsx` shows a loading screen rather than briefly flashing the
  login page or the dashboard. A 401 from *any* API call anywhere in the
  app clears the session and query cache automatically (see the
  `cdt:unauthorized` event in `src/services/api.ts`).
- **Session persistence**: the JWT and last-known user profile are
  stored in `localStorage` under `cdt_token` / `cdt_user`. Refreshing
  the browser re-validates the token via `/auth/me` rather than trusting
  storage blindly.
- **Logout**: clears both `localStorage` keys, clears the auth state,
  and clears TanStack Query's entire cache (so no previous session's
  data can leak into a new one), then navigates to `/login`. There is no
  server-side token revocation — JWTs are stateless — so logout is a
  purely client-side operation, which is standard for this kind of
  short-lived-token setup.

### Demo user seeding — idempotent by design

`app/services/seed.py::ensure_demo_user()` looks the demo account up by
its normalized email (`demo@digitaltwin.local`) on **every** backend
startup:

- **Missing** → it's created with the default password above.
- **Already exists** → it's left untouched, including its password hash
  — so if you've changed the demo account's password, restarting the
  backend will never silently revert it.

This is intentionally decoupled from the larger synthetic demo
environment (assets, vulnerabilities, controls, events), which is seeded
once as a connected unit and gated on whether any `Asset` row already
exists — not on whether any `User` row exists. Older versions of this
seed script gated *all* seeding, including the demo user, on "does any
user exist at all," which meant the demo account could permanently fail
to exist on a database that had, for any unrelated reason, already
acquired a user row. `ensure_demo_user()` fixes that: the demo login
is unconditionally guaranteed to exist after startup, on both a brand
new database and one that's been running for a while.

### Resetting the local development database

```bash
cd backend
rm -f cyber_twin.db          # only affects your local dev SQLite file
uvicorn app.main:app --reload --port 8000   # tables + demo data recreated automatically
```

This is always safe in development — it does **not** affect anything
outside your local `backend/cyber_twin.db` file, and the app is designed
to start up correctly from either a missing or an existing database.

### Production credentials

`demo@digitaltwin.local` / `DemoPass123!` are **development/demo-only**
credentials, hardcoded as the seed default in `app/services/seed.py`.
Do not deploy this application to a shared or public environment without
either removing the demo-seeding step or immediately changing that
account's password through the real login flow — since the seed logic
never overwrites an existing password, changing it once is permanent
across restarts.

### Troubleshooting

| Symptom | Likely cause |
|---|---|
| "Unable to connect to the CDT2 backend" on login | The backend isn't running, or isn't on the port `vite.config.ts`'s dev proxy points at (`http://localhost:8000` by default). |
| "Invalid email or password" for the known demo credentials | The demo user's password was changed at some point (seeding never reverts it) — verify with whoever last had access, or delete the local dev database as above. |
| Login page flashes then jumps to the dashboard, or vice versa | Should not happen — `App.tsx` gates all routing on `AuthContext`'s `isLoading`. If you see this, check that `AuthProvider` wraps `<App />` in `main.tsx`. |
| Logged out unexpectedly while using the app | The JWT expired (default 7 days, see `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env.example`), or the account was deleted/disabled server-side — `/auth/me` rejects both. |
| Backend test suite fails immediately | Make sure `pytest` and `httpx` are installed (`pip install -r requirements.txt`) and that you're running `pytest` from the `backend/` directory. |

---

## Running tests

A backend test suite covering authentication exists at
`backend/tests/` (pytest, run against an isolated in-memory database —
never your real dev database):

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

It covers: fresh-database seeding creates exactly one demo user;
re-running seeding never duplicates it; an existing demo account's
password is never overwritten; login success, wrong password, unknown
email, and disabled accounts; and `/api/auth/me` with a valid, missing,
malformed, expired, or deleted-user token.

No frontend automated test suite exists yet. Frontend changes are
verified via `npm run build` (production build must succeed) and manual
verification of the login/session/logout flows described above. See
`ARCHITECTURE.md` → "Suggested next steps" for a proposed frontend
testing plan (Vitest + React Testing Library).

## Deployment

Not yet configured. The FastAPI app is a standard ASGI app (deployable
behind `uvicorn`/`gunicorn` + any reverse proxy) and the frontend builds
to static files via `npm run build` (deployable to any static host or
served by the backend).
# CybersecurityDigitalTwin
