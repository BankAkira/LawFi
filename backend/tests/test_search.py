"""Search API tests -- exercise POST /api/search/ through the public HTTP interface."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ruling import CaseType, Ruling, RulingResult

USER = {"email": "search@test.com", "password": "testpass1", "name": "Searcher"}


async def _auth_headers(client: AsyncClient) -> dict:
    """Register + login, return Authorization header."""
    await client.post("/api/auth/register", json=USER)
    resp = await client.post(
        "/api/auth/login",
        json={"email": USER["email"], "password": USER["password"]},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _seed_rulings(db: AsyncSession) -> None:
    """Insert sample rulings for search tests."""
    rulings = [
        Ruling(
            ruling_number="100/2565",
            year=2565,
            case_type=CaseType.CIVIL,
            result=RulingResult.UPHELD,
            summary="จำเลยผิดสัญญาซื้อขายที่ดิน",
            facts="โจทก์ทำสัญญาซื้อขายที่ดิน",
            full_text="คำพิพากษาฎีกาที่ 100/2565 สัญญาซื้อขายที่ดิน ละเมิด",
            keywords=["สัญญาซื้อขาย", "ที่ดิน"],
            is_processed=True,
        ),
        Ruling(
            ruling_number="200/2564",
            year=2564,
            case_type=CaseType.CRIMINAL,
            result=RulingResult.REVERSED,
            summary="จำเลยถูกฟ้องฐานฉ้อโกง",
            facts="จำเลยหลอกลวงผู้เสียหาย",
            full_text="คำพิพากษาฎีกาที่ 200/2564 ฉ้อโกง หลอกลวง",
            keywords=["ฉ้อโกง", "หลอกลวง"],
            is_processed=True,
        ),
        Ruling(
            ruling_number="300/2566",
            year=2566,
            case_type=CaseType.LABOR,
            result=RulingResult.MODIFIED,
            summary="นายจ้างเลิกจ้างไม่เป็นธรรม",
            facts="ลูกจ้างถูกเลิกจ้างโดยไม่มีเหตุ",
            full_text="คำพิพากษาฎีกาที่ 300/2566 เลิกจ้าง แรงงาน ค่าชดเชย",
            keywords=["เลิกจ้าง", "แรงงาน", "ค่าชดเชย"],
            is_processed=True,
        ),
    ]
    for r in rulings:
        db.add(r)
    await db.commit()


@pytest.mark.asyncio
async def test_search_by_keyword(client: AsyncClient, db: AsyncSession):
    """Search with a keyword returns rulings that contain it."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/search/",
        json={"query": "สัญญาซื้อขาย"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    numbers = [r["ruling_number"] for r in data["results"]]
    assert "100/2565" in numbers


@pytest.mark.asyncio
async def test_search_by_ruling_number(client: AsyncClient, db: AsyncSession):
    """Search by ruling number returns the exact ruling."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/search/",
        json={"query": "200/2564"},
        headers=headers,
    )

    assert response.status_code == 200
    numbers = [r["ruling_number"] for r in response.json()["results"]]
    assert "200/2564" in numbers


@pytest.mark.asyncio
async def test_search_filter_case_type(client: AsyncClient, db: AsyncSession):
    """Filtering by case_type returns only matching rulings."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/search/",
        json={"query": "คำพิพากษา", "case_type": "อาญา"},
        headers=headers,
    )

    assert response.status_code == 200
    for r in response.json()["results"]:
        assert r["case_type"] == "อาญา"


@pytest.mark.asyncio
async def test_search_filter_year_range(client: AsyncClient, db: AsyncSession):
    """Filtering by year range narrows results."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/search/",
        json={"query": "คำพิพากษา", "year_from": 2565, "year_to": 2566},
        headers=headers,
    )

    assert response.status_code == 200
    for r in response.json()["results"]:
        assert 2565 <= r["year"] <= 2566


@pytest.mark.asyncio
async def test_search_filter_result(client: AsyncClient, db: AsyncSession):
    """Filtering by ruling result returns only matching rulings."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    response = await client.post(
        "/api/search/",
        json={"query": "คำพิพากษา", "result": "กลับ"},
        headers=headers,
    )

    assert response.status_code == 200
    for r in response.json()["results"]:
        assert r["result"] == "กลับ"


@pytest.mark.asyncio
async def test_search_filter_keywords(client: AsyncClient, db: AsyncSession):
    """Filtering by keywords (array overlap) excludes non-matching rulings."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    # Without filter: all 3 rulings match "คำพิพากษา"
    all_resp = await client.post(
        "/api/search/",
        json={"query": "คำพิพากษา"},
        headers=headers,
    )
    assert all_resp.json()["total"] == 3

    # With keyword filter: only the labor ruling has keyword "แรงงาน"
    filtered_resp = await client.post(
        "/api/search/",
        json={"query": "คำพิพากษา", "keywords": ["แรงงาน"]},
        headers=headers,
    )

    assert filtered_resp.status_code == 200
    data = filtered_resp.json()
    assert data["total"] == 1
    assert data["results"][0]["ruling_number"] == "300/2566"


@pytest.mark.asyncio
async def test_search_no_auth_returns_401(client: AsyncClient, db: AsyncSession):
    """Search without authentication returns 401 or 403."""
    response = await client.post(
        "/api/search/",
        json={"query": "test"},
    )

    assert response.status_code in (401, 403)


# ── rate limiting ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_free_user_rate_limited_at_10(client: AsyncClient, db: AsyncSession):
    """Free-tier user is blocked after 10 searches per day."""
    await _seed_rulings(db)
    headers = await _auth_headers(client)

    # 10 searches should succeed
    for i in range(10):
        resp = await client.post(
            "/api/search/",
            json={"query": f"ค้นหา{i}"},
            headers=headers,
        )
        assert resp.status_code == 200, f"Search {i + 1} failed: {resp.status_code}"

    # 11th should be rate limited
    resp = await client.post(
        "/api/search/",
        json={"query": "อีกครั้ง"},
        headers=headers,
    )
    assert resp.status_code == 429
    assert "ขีดจำกัด" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_pro_user_unlimited(client: AsyncClient, db: AsyncSession):
    """Pro-tier user is not rate limited."""
    await _seed_rulings(db)

    # Register as pro user
    pro = {"email": "pro@test.com", "password": "propass12", "name": "ProUser"}
    await client.post("/api/auth/register", json=pro)

    # Upgrade to pro directly in DB
    from sqlalchemy import update

    from app.models.user import User

    await db.execute(update(User).where(User.email == pro["email"]).values(subscription_tier="pro"))
    await db.commit()

    resp = await client.post(
        "/api/auth/login",
        json={"email": pro["email"], "password": pro["password"]},
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # 15 searches -- all should succeed for pro
    for i in range(15):
        resp = await client.post(
            "/api/search/",
            json={"query": f"ค้นหา{i}"},
            headers=headers,
        )
        assert resp.status_code == 200, f"Pro search {i + 1} failed: {resp.status_code}"
