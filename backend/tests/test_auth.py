"""
Authentication test suite.

Covers: idempotent seeding (fresh DB, re-run, existing password
preserved), login (success, wrong password, unknown email, disabled
account, email normalization), and /api/auth/me (valid, missing,
malformed, expired token).
"""
import time

from app.core.security import create_access_token, hash_password, verify_password
from app.models.models import User
from app.services.seed import DEMO_EMAIL, DEMO_PASSWORD, ensure_demo_user, seed_database

# ---------- Seeding ----------

def test_fresh_database_creates_demo_user(test_db):
    assert test_db.query(User).count() == 0
    seed_database(test_db)

    users = test_db.query(User).filter(User.email == DEMO_EMAIL).all()
    assert len(users) == 1
    assert users[0].role == "admin"
    assert verify_password(DEMO_PASSWORD, users[0].hashed_password)


def test_seed_can_run_twice_without_duplicating_demo_user(test_db):
    seed_database(test_db)
    seed_database(test_db)

    users = test_db.query(User).filter(User.email == DEMO_EMAIL).count()
    assert users == 1


def test_seed_does_not_duplicate_environment_assets_on_rerun(test_db):
    from app.models.models import Asset

    seed_database(test_db)
    first_count = test_db.query(Asset).count()
    assert first_count > 0

    seed_database(test_db)
    second_count = test_db.query(Asset).count()
    assert second_count == first_count


def test_existing_demo_user_is_not_duplicated_when_other_users_exist(test_db):
    """Regression test for the original bug: seeding used to be skipped
    entirely (including demo-user creation) the moment ANY user row
    existed for any reason. Here we simulate a database that already has
    an unrelated user before the demo user has ever been created, and
    confirm the demo user still gets created exactly once."""
    other = User(email="someone.else@example.com", full_name="Someone Else",
                 hashed_password=hash_password("whatever-not-checked"), role="analyst")
    test_db.add(other)
    test_db.commit()

    seed_database(test_db)

    demo_users = test_db.query(User).filter(User.email == DEMO_EMAIL).all()
    assert len(demo_users) == 1


def test_existing_demo_password_is_not_overwritten(test_db):
    """If an operator has changed the demo account's password, re-running
    seeding must never revert it."""
    custom_hash = hash_password("SomeOperatorChangedThis!")
    test_db.add(User(email=DEMO_EMAIL, full_name="Demo Analyst", hashed_password=custom_hash, role="admin"))
    test_db.commit()

    ensure_demo_user(test_db)

    user = test_db.query(User).filter(User.email == DEMO_EMAIL).first()
    assert user.hashed_password == custom_hash
    assert verify_password("SomeOperatorChangedThis!", user.hashed_password)
    assert not verify_password(DEMO_PASSWORD, user.hashed_password)


# ---------- Login ----------

def test_demo_login_succeeds(client, test_db):
    seed_database(test_db)
    resp = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and len(body["access_token"]) > 0
    assert body["user"]["email"] == DEMO_EMAIL
    assert "hashed_password" not in body["user"]
    assert "password" not in body["user"]


def test_login_normalizes_email_case_and_whitespace(client, test_db):
    seed_database(test_db)
    resp = client.post("/api/auth/login", json={"email": "  Demo@DigitalTwin.Local  ", "password": DEMO_PASSWORD})
    assert resp.status_code == 200


def test_login_wrong_password_returns_401(client, test_db):
    seed_database(test_db)
    resp = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": "WrongPassword123!"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_login_unknown_email_returns_401(client, test_db):
    seed_database(test_db)
    resp = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid email or password"


def test_login_disabled_account_returns_403(client, test_db):
    seed_database(test_db)
    user = test_db.query(User).filter(User.email == DEMO_EMAIL).first()
    user.is_active = False
    test_db.commit()

    resp = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert resp.status_code == 403


# ---------- /api/auth/me ----------

def test_me_works_with_valid_token(client, test_db):
    seed_database(test_db)
    login = client.post("/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    token = login.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == DEMO_EMAIL


def test_me_rejects_missing_token(client, test_db):
    seed_database(test_db)
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_rejects_malformed_token(client, test_db):
    seed_database(test_db)
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-jwt"})
    assert resp.status_code == 401


def test_me_rejects_expired_token(client, test_db):
    seed_database(test_db)
    user = test_db.query(User).filter(User.email == DEMO_EMAIL).first()
    expired_token = create_access_token(subject=user.id, expires_minutes=-1)

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


def test_me_rejects_token_for_deleted_user(client, test_db):
    seed_database(test_db)
    user = test_db.query(User).filter(User.email == DEMO_EMAIL).first()
    token = create_access_token(subject=user.id)

    test_db.delete(user)
    test_db.commit()

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
