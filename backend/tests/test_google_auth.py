"""Google OAuth tests -- mock the Google token verification at the boundary."""

import pytest
from httpx import AsyncClient

GOOGLE_HEADERS = {
    "X-Test-Google-Email": "guser@gmail.com",
    "X-Test-Google-Name": "Google User",
}


async def _google_login(client: AsyncClient, **header_overrides) -> dict:
    """Call the Google OAuth endpoint with test headers."""
    headers = {**GOOGLE_HEADERS, **header_overrides}
    return await client.post(
        "/api/auth/google",
        json={"id_token": "fake-token"},
        headers=headers,
    )


@pytest.mark.asyncio
async def test_google_new_user_created(client: AsyncClient):
    """Valid Google token for unknown email auto-creates user and returns tokens."""
    resp = await _google_login(client)

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    # Verify created user via /me
    me = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "guser@gmail.com"
    assert me.json()["name"] == "Google User"
    assert me.json()["auth_provider"] == "google"


@pytest.mark.asyncio
async def test_google_existing_user_logs_in(client: AsyncClient):
    """Second Google login with same email returns tokens without duplicate."""
    resp1 = await _google_login(client)
    assert resp1.status_code == 200

    resp2 = await _google_login(client)
    assert resp2.status_code == 200

    # Both tokens should work and reference the same user
    me1 = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {resp1.json()['access_token']}"},
    )
    me2 = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {resp2.json()['access_token']}"},
    )
    assert me1.json()["id"] == me2.json()["id"]


@pytest.mark.asyncio
async def test_google_email_already_registered_with_password(client: AsyncClient):
    """Google login fails if email was registered via email/password."""
    # Register with email/password first
    await client.post(
        "/api/auth/register",
        json={"email": "conflict@test.com", "password": "password123", "name": "Email User"},
    )

    # Try Google login with same email
    resp = await _google_login(client, **{"X-Test-Google-Email": "conflict@test.com"})

    assert resp.status_code == 400
    assert "รหัสผ่าน" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_google_invalid_token_returns_401(client: AsyncClient):
    """Without test headers, an invalid token returns 401 (calls real Google)."""
    # No X-Test-Google-Email header -> hits real Google verification -> fails
    resp = await client.post(
        "/api/auth/google",
        json={"id_token": "totally-invalid-token"},
    )

    assert resp.status_code == 401
