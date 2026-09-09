# API Reference

Base URL: `http://localhost:8000/api`

Interactive docs (auto-generated from the FastAPI app, always up to
date with the actual code): `http://localhost:8000/docs`

All routes except `/auth/register` and `/auth/login` require a bearer
token: `Authorization: Bearer <token>`.

## Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account. Returns a token + user. |
| POST | `/auth/login` | Log in. Returns a token + user. |
| GET | `/auth/me` | Current authenticated user. |

## Assets

| Method | Path | Description |
|---|---|---|
| GET | `/assets` | List assets. Query params: `search`, `asset_type`, `criticality`, `risk_class`. |
| POST | `/assets` | Create an asset. Risk score is computed server-side immediately. |
| GET | `/assets/{id}` | Get one asset. |
| PUT | `/assets/{id}` | Update an asset (partial). Risk score is recomputed. |
| DELETE | `/assets/{id}` | Delete an asset and its relationships. |
| POST | `/assets/relationships` | Create a directed edge between two assets. |
| DELETE | `/assets/relationships/{id}` | Delete an edge. |

## Digital Twin

| Method | Path | Description |
|---|---|---|
| GET | `/twin` | Full graph: all nodes (assets) and edges (relationships), for the graph view. |

## Risk & attack paths

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard` | Summary metrics for the dashboard (asset counts, security score, risk distribution). |
| GET | `/risk/assets/{id}` | Explainable risk breakdown for one asset (ordered list of contributing factors). |
| GET | `/attack-paths` | Top-10 ranked critical attack paths across the whole graph (entry points → high-value assets). |
| POST | `/attack-paths/simulate` | Compute the highest-risk path from a given asset. Body: `{ source_asset_id, target_asset_id? }`. If `target_asset_id` is omitted, finds the riskiest reachable target automatically. |

## Vulnerabilities

| Method | Path | Description |
|---|---|---|
| GET | `/vulnerabilities` | List vulnerabilities. Query params: `severity`, `status`, `known_exploited`. |
| POST | `/vulnerabilities` | Create a vulnerability on an asset. Recomputes that asset's risk score. |
| PUT | `/vulnerabilities/{id}/status?status=patched` | Update status; recomputes the linked asset's risk score. |

## Security controls

| Method | Path | Description |
|---|---|---|
| GET | `/controls` | List tracked security controls with estimated risk reduction. |

## Simulations (What-If)

| Method | Path | Description |
|---|---|---|
| POST | `/simulations/what-if` | Body: `{ asset_id, action }`. `action` is one of `enable_mfa`, `remove_excess_permissions`, `patch_vulnerability`, `disable_public_access`. Returns before/after risk. **Nothing is persisted** — the change is computed in memory and rolled back. |

## Events

| Method | Path | Description |
|---|---|---|
| GET | `/events` | Recent security events feed (most recent 20), for the dashboard. |

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check, no auth required. |

## Simulator (Cyber Attack & Defense Simulator)

See `SIMULATOR.md` for the full module documentation, including safety
guarantees and the rules engine. All routes are under `/api/simulator`.

| Method | Path | Description |
|---|---|---|
| GET | `/simulator/components` | The full "+ Add Component" catalog (network/application/cloud/endpoint/security/threat). |
| GET | `/simulator/defense-controls` | The list of applicable defense controls (MFA, least privilege, segmentation, ...). |
| GET | `/simulator/scenarios` | List scenarios. Query params: `category`, `entry_point_type`. |
| GET | `/simulator/templates` | List predefined environment templates (college, cloud, IoT, ...). |
| GET | `/simulator/templates/{id}` | One template's full topology. |
| GET | `/simulator/case-studies` | Real-world case study summaries. |
| GET | `/simulator/case-studies/{id}` | One case study in full. |
| POST | `/simulator/run` | Run one deterministic simulation. Body: `{ scenario_id, entry_point_id, components[], edges[], applied_defenses[] }`. The topology is client-submitted and never touches the real Digital Twin database. |
| POST | `/simulator/optimize-defense` | Ranks each defense control by simulated risk reduction for a given scenario/topology — computed by actually re-running the engine once per control, not a lookup table. |
| POST | `/simulator/predict-paths` | For every threat-side component in a topology, runs every scenario that could plausibly start there and returns the results ranked by risk. |

## Not yet implemented (see README.md status table)

`GET /api/threat-intelligence`, `POST /api/ai/chat`,
`POST /api/ml/predict-risk`, `POST /api/ml/anomaly`,
`POST /api/reports/generate` — these are named in the original
specification but not built in this version. Building them is
straightforward given the existing route/router pattern in
`app/api/routes/`.
