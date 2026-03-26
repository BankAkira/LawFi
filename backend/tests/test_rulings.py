"""Ruling detail + bookmarks tests via public HTTP API."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruling import CaseType, Ruling, RulingResult

USER = {"email": "ruling@test.com", "password": "testpass1", "name": "RulingUser"}


async def _auth_headers(client: AsyncClient) -> dict:
    await client.post("/api/auth/register", json=USER)
    resp = await client.post(
        "/api/auth/login",
        json={"email": USER["email"], "password": USER["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _seed_ruling(db: AsyncSession) -> int:
    """Insert one ruling, return its ID."""
    ruling = Ruling(
        ruling_number="999/2565",
        year=2565,
        case_type=CaseType.CIVIL,
        result=RulingResult.UPHELD,
        summary="ทดสอบสรุปย่อ",
        facts="ข้อเท็จจริงทดสอบ",
        issues="ประเด็นทดสอบ",
        judgment="คำวินิจฉัยทดสอบ",
        full_text="เนื้อหาเต็มทดสอบ",
        keywords=["ทดสอบ", "test"],
        referenced_sections=["ป.พ.พ. มาตรา 420"],
        is_processed=True,
    )
    db.add(ruling)
    await db.commit()
    await db.refresh(ruling)
    return ruling.id


# ── ruling detail ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_ruling_by_id(client: AsyncClient, db: AsyncSession):
    """Valid ruling ID returns 200 with all structured fields."""
    ruling_id = await _seed_ruling(db)

    response = await client.get(f"/api/rulings/{ruling_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["ruling_number"] == "999/2565"
    assert data["summary"] == "ทดสอบสรุปย่อ"
    assert data["facts"] == "ข้อเท็จจริงทดสอบ"
    assert data["issues"] == "ประเด็นทดสอบ"
    assert data["judgment"] == "คำวินิจฉัยทดสอบ"
    assert data["case_type"] == "แพ่ง"
    assert data["result"] == "ยืน"
    assert "ป.พ.พ. มาตรา 420" in data["referenced_sections"]
    assert "ทดสอบ" in data["keywords"]


@pytest.mark.asyncio
async def test_get_ruling_invalid_id(client: AsyncClient):
    """Non-existent ruling ID returns 404."""
    response = await client.get("/api/rulings/99999")

    assert response.status_code == 404
    assert "ไม่พบ" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ruling_by_number(client: AsyncClient, db: AsyncSession):
    """Valid ruling number returns 200."""
    await _seed_ruling(db)

    response = await client.get("/api/rulings/number/999/2565")

    assert response.status_code == 200
    assert response.json()["ruling_number"] == "999/2565"


@pytest.mark.asyncio
async def test_get_ruling_invalid_number(client: AsyncClient):
    """Non-existent ruling number returns 404."""
    response = await client.get("/api/rulings/number/0/0000")

    assert response.status_code == 404


# ── bookmarks ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_bookmark(client: AsyncClient, db: AsyncSession):
    """Authenticated user can bookmark a ruling."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    response = await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_bookmark_duplicate(client: AsyncClient, db: AsyncSession):
    """Bookmarking the same ruling twice returns 400."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)
    response = await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_bookmark_status_true(client: AsyncClient, db: AsyncSession):
    """Checking status of a bookmarked ruling returns bookmarked=true."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)
    response = await client.get(f"/api/bookmarks/{ruling_id}/status", headers=headers)

    assert response.status_code == 200
    assert response.json()["bookmarked"] is True


@pytest.mark.asyncio
async def test_bookmark_status_false(client: AsyncClient, db: AsyncSession):
    """Checking status of a non-bookmarked ruling returns bookmarked=false."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    response = await client.get(f"/api/bookmarks/{ruling_id}/status", headers=headers)

    assert response.status_code == 200
    assert response.json()["bookmarked"] is False


@pytest.mark.asyncio
async def test_list_bookmarks(client: AsyncClient, db: AsyncSession):
    """Listing bookmarks returns saved rulings."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)
    response = await client.get("/api/bookmarks/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["ruling_number"] == "999/2565"


@pytest.mark.asyncio
async def test_remove_bookmark(client: AsyncClient, db: AsyncSession):
    """Removing a bookmark returns 200 and it disappears from list."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    await client.post(f"/api/bookmarks/{ruling_id}", headers=headers)
    response = await client.delete(f"/api/bookmarks/{ruling_id}", headers=headers)

    assert response.status_code == 200

    # Verify it's gone
    list_resp = await client.get("/api/bookmarks/", headers=headers)
    assert len(list_resp.json()) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_bookmark(client: AsyncClient, db: AsyncSession):
    """Removing a bookmark that doesn't exist returns 404."""
    ruling_id = await _seed_ruling(db)
    headers = await _auth_headers(client)

    response = await client.delete(f"/api/bookmarks/{ruling_id}", headers=headers)

    assert response.status_code == 404
