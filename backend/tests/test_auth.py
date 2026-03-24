import pytest
from httpx import AsyncClient


# ── helpers ──────────────────────────────────────────────────────────

VALID_USER = {"email": "test@example.com", "password": "secure123", "name": "Test"}


async def register(client: AsyncClient, **overrides) -> dict:
    """Register a user and return the response object."""
    payload = {**VALID_USER, **overrides}
    return await client.post("/api/auth/register", json=payload)


async def login(
    client: AsyncClient,
    email: str = VALID_USER["email"],
    password: str = VALID_USER["password"],
):
    """Login and return the response object."""
    return await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )


async def register_and_login(client: AsyncClient, **overrides) -> str:
    """Register, login, return access_token."""
    await register(client, **overrides)
    resp = await login(
        client,
        overrides.get("email", VALID_USER["email"]),
        overrides.get("password", VALID_USER["password"]),
    )
    return resp.json()["access_token"]


# ── register ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """New user can register with email and password."""
    response = await register(client)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test"
    assert data["subscription_tier"] == "free"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an email that already exists returns 400."""
    await register(client)
    response = await register(client)

    assert response.status_code == 400
    assert "อีเมล" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Password shorter than 8 characters is rejected."""
    response = await register(client, password="short")

    assert response.status_code == 400
    assert "รหัสผ่าน" in response.json()["detail"]


# ── login ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Registered user can login and receives JWT tokens."""
    await register(client)
    response = await login(client)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login with wrong password returns 401."""
    await register(client)
    response = await login(client, password="wrongpass")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client: AsyncClient):
    """Login with unregistered email returns 401."""
    response = await login(client, email="nobody@example.com")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db):
    """Login to a suspended account returns 403."""
    await register(client)
    # Suspend the user directly via DB
    from sqlalchemy import update
    from app.models.user import User

    await db.execute(
        update(User).where(User.email == VALID_USER["email"]).values(is_active=False)
    )
    await db.commit()

    response = await login(client)
    assert response.status_code == 403


# ── refresh ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient):
    """Valid refresh token returns new token pair."""
    await register(client)
    login_resp = await login(client)
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Invalid refresh token returns 401."""
    response = await client.post("/api/auth/refresh", json={"refresh_token": "garbage"})

    assert response.status_code == 401


# ── me ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient):
    """Authenticated user can retrieve their profile."""
    token = await register_and_login(client)

    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == VALID_USER["email"]


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Invalid token returns 401 on /me."""
    response = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer garbage"}
    )

    assert response.status_code == 401 or response.status_code == 403


# ── brute force ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_brute_force_lockout(client: AsyncClient):
    """After 5 failed login attempts, subsequent attempts return 429."""
    await register(client)

    # 5 failed attempts
    for _ in range(5):
        resp = await login(client, password="wrongpass")
        assert resp.status_code == 401

    # 6th attempt should be rate-limited
    response = await login(client, password="wrongpass")
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_brute_force_resets_on_success(client: AsyncClient):
    """Successful login resets the brute-force counter."""
    await register(client)

    # 4 failed attempts (under limit)
    for _ in range(4):
        await login(client, password="wrongpass")

    # Successful login resets counter
    resp = await login(client)
    assert resp.status_code == 200

    # 5 more failures should be fine (counter was reset)
    for _ in range(5):
        resp = await login(client, password="wrongpass")
        assert resp.status_code == 401

    # 6th after reset -> locked
    resp = await login(client, password="wrongpass")
    assert resp.status_code == 429
