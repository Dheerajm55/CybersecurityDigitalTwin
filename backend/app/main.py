"""
CDT2 — FastAPI entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000

On startup, creates tables (if missing) and seeds deterministic synthetic
demo data (if the database is empty and SEED_DEMO_DATA=true), so the
application is usable immediately with zero manual setup.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import logging

from app.api.routes import assets, auth, controls, events, live, ml, risk, simulator, twin, vulnerabilities
from app.core.config import get_settings
from app.database.session import Base, SessionLocal, engine
from app.services.live_state import live_state
from app.services.seed import seed_database
from app.services.seed_scenarios import seed_scenarios_and_case_studies

logger = logging.getLogger("cyber_twin")

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="A defensive cybersecurity digital twin: models an organization's digital "
                 "environment as a graph, computes explainable risk scores, simulates "
                 "hypothetical attack paths, and recommends security improvements. "
                 "No offensive capability, real exploitation, or credential storage.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Without this, any unhandled exception raised inside a route (for
    example, a response_model/schema serialization failure) falls through
    to Starlette's default handler, which returns a PLAIN TEXT 500 body
    ("Internal Server Error") rather than JSON. The frontend's error
    handling (see frontend/src/utils/errors.ts) looks for a JSON `detail`
    field and, finding none on a plain-text body, silently falls back to
    a generic per-call message — which is exactly what made a real 500
    (a EmailStr response-validation bug) look identical to "wrong
    password" during a previous debugging pass on this project. Returning
    a real JSON `detail` here means that failure mode can never hide
    behind a generic frontend fallback message again. The client never
    sees the exception type or a stack trace — just a short, safe string
    — full details are still logged server-side for the developer.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Check the backend logs for details."})


app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(twin.router)
app.include_router(risk.router)
app.include_router(vulnerabilities.router)
app.include_router(controls.router)
app.include_router(events.router)
app.include_router(simulator.router)
app.include_router(ml.router)
app.include_router(live.router)


@app.on_event("startup")
async def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.SEED_DEMO_DATA:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()

    # Scenario/case-study catalog sync (Phase 2): idempotent upsert from the
    # static Python catalogs into the database, run on every startup so the
    # database always reflects the current code-defined catalog. Independent
    # of SEED_DEMO_DATA (asset/vuln demo data) since this is catalog data,
    # not organization data.
    db = SessionLocal()
    try:
        seed_scenarios_and_case_studies(db)
    finally:
        db.close()

    task = asyncio.create_task(live.telemetry_loop())
    live_state.set_task(task)


@app.on_event("shutdown")
def on_shutdown() -> None:
    live_state.cancel()


@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
