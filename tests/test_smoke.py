"""P0 smoke tests: the app boots and the auth + profile path works end to end."""

from __future__ import annotations


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "Kare"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


def test_languages(client):
    r = client.get("/languages")
    codes = {x["code"] for x in r.json()["supported_languages"]}
    assert {"en", "yo", "ha", "ig", "pcm"}.issubset(codes)


def test_register_login_me(client):
    email = "flow@example.com"
    r = client.post("/api/v1/auth/register", json={
        "email": email, "password": "a-good-password",
        "first_name": "Ada", "last_name": "Obi", "preferred_language": "ig",
    })
    assert r.status_code == 201, r.text

    r = client.post("/api/v1/auth/login", json={"email": email, "password": "a-good-password"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"] and body["refresh_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = client.get("/api/v1/patients/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Ada"


def test_register_rejects_duplicate(client):
    payload = {
        "email": "dupe@example.com", "password": "a-good-password",
        "first_name": "A", "last_name": "B",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_protected_route_requires_auth(client):
    assert client.get("/api/v1/patients/me").status_code in (401, 403)


def test_bad_password_rejected(client):
    client.post("/api/v1/auth/register", json={
        "email": "pw@example.com", "password": "correct-horse",
        "first_name": "A", "last_name": "B",
    })
    r = client.post("/api/v1/auth/login", json={"email": "pw@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_wrong_token_rejected(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
