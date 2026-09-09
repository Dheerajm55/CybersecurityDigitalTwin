# Architecture

## Overview

```
┌─────────────┐      HTTPS/JSON       ┌───────────────────┐
│   Frontend   │  ───────────────────▶ │      Backend        │
│  React + TS  │ ◀─────────────────── │      FastAPI         │
│  Vite/Tailwd │                       └─────────┬──────────┘
└─────────────┘                                  │
                                                   │ SQLAlchemy
                                                   ▼
                                         ┌───────────────────┐
                                         │  PostgreSQL /      │
                                         │  SQLite (default)  │
                                         └─────────┬──────────┘
                                                   │
                              read models into     │
                              an in-memory graph    ▼
                                         ┌───────────────────┐
                                         │  NetworkX Graph     │
                                         │  Engine (Phase 3)   │
                                         └───────────────────┘
```

Everything currently in this build talks to a single relational
database. The "digital twin graph" is not a separate persisted graph
database yet — it is built on demand from the `assets` and
`asset_relationships` tables using NetworkX, which is sufficient for
the graph sizes this application targets (tens to low hundreds of
assets) and avoids running a second database for Phase 1-3.

## Why NetworkX instead of Neo4j (for now)

The master specification calls for Neo4j as the primary graph store.
This build uses NetworkX directly against PostgreSQL/SQLite instead,
for a concrete reason: it lets the entire Phase 1-3 stack run with a
single dependency-light database and zero extra infrastructure, which
matches the spec's own requirement that "the application MUST work
immediately after installation." `NEO4J_URI` / `NEO4J_USERNAME` /
`NEO4J_PASSWORD` are already wired into `.env.example` and
`app/core/config.py` so that a real Neo4j-backed `app/graph/` module
can be dropped in later without changing the API surface — the
`GET /api/twin`, attack-path, and risk endpoints would keep the same
request/response shapes.

## Request flow: "Simulate Compromise"

1. Frontend: user clicks a node, then **Simulate Compromise**.
2. `POST /api/attack-paths/simulate { source_asset_id }`
3. Backend (`app/services/graph_engine.py`):
   - Loads all assets + relationships from the database.
   - Builds a directed NetworkX graph.
   - Assigns each edge a traversal cost derived from the *target* asset's
     security posture (MFA off, internet-exposed, elevated permissions,
     open critical vulnerabilities all lower the cost — i.e., make that
     asset easier for an attacker to move through).
   - If no target is given, finds the highest-`risk_score` node reachable
     from the source via `networkx.descendants`, then computes the
     lowest-cost path to it with `nx.dijkstra_path`.
   - Converts the path into a 0-100 risk score (average asset risk along
     the path, with a bonus for short paths, since a 2-3 hop compromise
     is more dangerous than an 8-hop one) and a plain-language
     explanation list built directly from each asset's actual field
     values (never invented).
4. Response is rendered as-is in the details panel — the frontend does
   no additional "AI" post-processing.

## Deterministic risk engine vs. machine learning

Per Section 14 and Section 40 of the specification, the application
must never depend entirely on AI/ML for its risk numbers. This build's
`app/services/risk_engine.py` implements only the deterministic half:
a transparent, additive scoring function over criticality, exposure,
MFA, permissions, and open vulnerabilities, with every point explained
in a `RiskFactor` list. This is intentionally simple and auditable —
see `ML_MODELS.md` for how the ML models described in the spec are
meant to plug into this same score as an additional signal, once built.

## Data model

See `backend/app/models/models.py` for the full SQLAlchemy schema.
Key tables implemented: `users`, `assets`, `asset_relationships`,
`vulnerabilities`, `security_controls`, `simulations` (schema only,
what-if runs are not currently persisted — see below), `attack_paths`
(schema only, not currently cached), `security_events`.

Tables described in the spec but not yet created: `organizations`,
`projects`, `risk_scores` (history table), `threat_intelligence`,
`model_predictions`, `reports`. These are straightforward additions
once Phases 4-10 are built and is the reason the schema is organized
as one `models.py` module rather than something harder to extend.

### Why what-if simulations aren't persisted

`POST /api/simulations/what-if` mutates the SQLAlchemy objects in
memory to compute a before/after score, then explicitly calls
`db.rollback()` so nothing is written. This was a deliberate simplicity
tradeoff for this build — the `Simulation` table exists and recording
history is a small follow-up (swap the `rollback()` for a `Simulation`
row insert plus a second `rollback()` for the mutated `Asset`).

## Frontend architecture

- **Routing:** `react-router-dom`, all authenticated routes nested under
  a shared `MainLayout` (sidebar + outlet).
- **Data fetching:** `@tanstack/react-query` for all server state; no
  global client-state store is used because nothing in this build needs
  cross-page shared mutable state beyond the auth token (kept in
  `localStorage`, attached via an axios interceptor).
- **Graph rendering:** `reactflow`, with a small deterministic
  layered-layout function (`layoutNodes` in `GraphViewer.tsx`) instead of
  a heavier auto-layout library, since asset graphs in this domain are
  naturally hierarchical (identity → SaaS → cloud → data).
- **Styling:** Tailwind, configured with exactly the restrained palette
  specified in the brief (`tailwind.config.js`). No component library
  (e.g. shadcn) was added, to keep the dependency list minimal as
  instructed.

## Suggested next steps (in spec build order)

1. **Phase 3 completion:** persist computed attack paths to the
   `attack_paths` table (currently computed live on every request,
   which is fine at this data scale but should be cached as the graph
   grows); add BFS/DFS baseline comparisons alongside Dijkstra.
2. **Phase 4:** add `app/ml/risk/` with an XGBoost training script
   (`ml/train_risk_model.py`), fed by the same features already exposed
   in `RiskFactor`; blend its output with the deterministic score behind
   a configurable weight rather than replacing it.
3. **Phase 6:** add `app/graph/neo4j_client.py` behind the same
   `graph_engine` interface, controlled by an environment flag, so
   Neo4j becomes a drop-in replacement for the NetworkX in-memory build
   without changing any API route.
4. **Testing:** `pytest` against `risk_engine.py` and `graph_engine.py`
   (pure functions, easy to unit test with synthetic fixtures) before
   adding frontend tests.
5. **Migrations:** introduce Alembic once the schema needs to evolve
   without dropping data — not required while `Base.metadata.create_all`
   is sufficient for a fresh install.
