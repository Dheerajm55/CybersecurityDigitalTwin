"""
Shared pytest fixtures for the backend test suite.

Every test gets its own fresh in-memory SQLite database (created and
torn down per test), wired into the app via FastAPI's dependency
override mechanism — never the real `cyber_twin.db` dev file. The
TestClient is instantiated WITHOUT the `with` context manager, which
means FastAPI's startup/shutdown lifecycle (table creation against the
real DATABASE_URL, demo-data seeding, the live-telemetry asyncio loop)
never runs during tests; each test explicitly seeds only what it needs
via the real service functions (ensure_demo_user, seed_database),
against the isolated test session.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.main import app


@pytest.fixture()
def test_db():
    # StaticPool is required for sqlite:///:memory: under a test client:
    # without it, every new connection checked out of the pool gets its
    # own separate empty in-memory database, so a request handled on a
    # different connection than the one that ran create_all() would see
    # no tables at all ("no such table: users").
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(test_db):
    def _override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
