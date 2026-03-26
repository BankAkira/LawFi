"""Search history tests via GET /api/history/."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruling import CaseType, Ruling

USER_A = {"email": "histA@test.com", "password": "testpass1", "name": "UserA"}
USER_B = {"email": "histB@test.com", "password": "testpass1", "name": "UserB"}


async def _auth(client: AsyncClient, user: dict) -> dict:
    await client.post("/api/auth/register", json=user)
    resp = await client.post(
        "/api/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _seed(db: AsyncSession) -> None:
    db.add(
        Ruling(
            ruling_number="H1/2565",
            year=2565,
            case_type=CaseType.CIVIL,
            full_text="ทดสอบประวัติ สัญญา",
            is_processed=True,
        )
    )
    await db.commit()


@pytest.mark.asyncio
async def test_history_empty_for_new_user(client: AsyncClient, db: AsyncSession):
    """New user has no search history."""
    await _seed(db)
    headers = await _auth(client, USER_A)

    response = await client.get("/api/history/", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_history_records_search(client: AsyncClient, db: AsyncSession):
    """After searching, the query appears in history."""
    await _seed(db)
    headers = await _auth(client, USER_A)

    # Perform a search
    await client.post("/api/search/", json={"query": "สัญญา"}, headers=headers)

    # Check history
    response = await client.get("/api/history/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["query"] == "สัญญา"
    assert "created_at" in data[0]


@pytest.mark.asyncio
async def test_history_is_user_scoped(client: AsyncClient, db: AsyncSession):
    """User A's history is not visible to User B."""
    await _seed(db)
    headers_a = await _auth(client, USER_A)
    headers_b = await _auth(client, USER_B)

    # User A searches
    await client.post("/api/search/", json={"query": "สัญญา"}, headers=headers_a)

    # User B's history should be empty
    response = await client.get("/api/history/", headers=headers_b)

    assert response.status_code == 200
    assert response.json() == []
