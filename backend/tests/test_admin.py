"""Admin API tests."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruling import Ruling
from app.models.user import User

ADMIN = {"email": "admin@test.com", "password": "adminpass", "name": "Admin"}
NORMAL = {"email": "normal@test.com", "password": "userpass1", "name": "Normal"}


async def _make_admin(client: AsyncClient, db: AsyncSession) -> dict:
    """Register admin user, flag as admin, return auth headers."""
    await client.post("/api/auth/register", json=ADMIN)
    # Flag as admin directly
    from sqlalchemy import update

    await db.execute(update(User).where(User.email == ADMIN["email"]).values(is_admin=True))
    await db.commit()

    resp = await client.post(
        "/api/auth/login",
        json={"email": ADMIN["email"], "password": ADMIN["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _make_normal(client: AsyncClient) -> dict:
    """Register normal user, return auth headers."""
    await client.post("/api/auth/register", json=NORMAL)
    resp = await client.post(
        "/api/auth/login",
        json={"email": NORMAL["email"], "password": NORMAL["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_admin_stats_as_admin(client: AsyncClient, db: AsyncSession):
    """Admin can access stats endpoint."""
    headers = await _make_admin(client, db)

    # Seed some data
    db.add(Ruling(ruling_number="ADM/1", year=2565, full_text="test", is_processed=True))
    db.add(
        Ruling(
            ruling_number="ADM/2",
            year=2565,
            full_text="test",
            is_processed=False,
            processing_error="failed",
        )
    )
    await db.commit()

    response = await client.get("/api/admin/stats", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total_users"] >= 1
    assert data["total_rulings"] >= 2
    assert data["processed_rulings"] >= 1
    assert data["failed_rulings"] >= 1


@pytest.mark.asyncio
async def test_admin_stats_as_normal_user(client: AsyncClient, db: AsyncSession):
    """Non-admin user gets 403 on admin endpoint."""
    headers = await _make_normal(client)

    response = await client.get("/api/admin/stats", headers=headers)

    assert response.status_code == 403
