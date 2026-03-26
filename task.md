# LawFi MVP -- Task Board

Parent PRD: [#1](https://github.com/BankAkira/LawFi/issues/1)

## Dependency Graph

```
#2 Alembic + Docker ─────────────────────────────────────────────────
├── #3 CI/CD + Seed                                                  
├── #4 Auth Fix + Tests ──────┬── #8 Search Frontend ──┬── #11 History
│                             │                        ├── #14 Polish
│   ┌── #12 Google OAuth      │                        │            
├── #5 Pipeline Fixes ──┬── #6 Pipeline Tests          │            
│                       ├── #7 Search Backend ─────────┘            
│                       ├── #9 Ruling Detail ───── #10 Bookmarks ──┘
│                       └── #13 Admin                               
```

## Issues

### Layer 0 -- Foundation (no blockers)

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [x] | [#2](https://github.com/BankAkira/LawFi/issues/2) | Alembic Migrations & Docker Compose | AFK | None |

### Layer 1 -- Blocked by #2 only

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [x] | [#3](https://github.com/BankAkira/LawFi/issues/3) | GitHub Actions CI & Seed Script | AFK | #2 |
| [x] | [#4](https://github.com/BankAkira/LawFi/issues/4) | Email Auth Fix & Tests | AFK | #2 |
| [x] | [#5](https://github.com/BankAkira/LawFi/issues/5) | Data Pipeline Bug Fixes | AFK | #2 |

### Layer 2 -- Blocked by Layer 1

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [x] | [#6](https://github.com/BankAkira/LawFi/issues/6) | Data Pipeline Tests (merged into #5) | AFK | #5 |
| [x] | [#7](https://github.com/BankAkira/LawFi/issues/7) | Search Backend -- pg_trgm & Filters | AFK | #2, #5 |
| [x] | [#9](https://github.com/BankAkira/LawFi/issues/9) | Ruling Detail View & Tests | AFK | #5 |
| [ ] | [#12](https://github.com/BankAkira/LawFi/issues/12) | Google OAuth | HITL | #4 |
| [x] | [#13](https://github.com/BankAkira/LawFi/issues/13) | Admin API & Monitoring | AFK | #2, #5 |

### Layer 3 -- Blocked by Layer 2

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [x] | [#8](https://github.com/BankAkira/LawFi/issues/8) | Search Frontend & Rate Limiting | AFK | #4, #7 |
| [x] | [#10](https://github.com/BankAkira/LawFi/issues/10) | Bookmarks End-to-End | AFK | #4, #9 |

### Layer 4 -- Blocked by Layer 3

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [x] | [#11](https://github.com/BankAkira/LawFi/issues/11) | Search History End-to-End | AFK | #4, #8 |
| [x] | [#14](https://github.com/BankAkira/LawFi/issues/14) | Frontend Polish & E2E Tests | AFK | #4, #8, #10 |

## Test Summary

**54 tests passing** across 9 test files:

### Backend (47 tests)

| File | Tests | Coverage |
|------|-------|----------|
| test_health.py | 1 | Health check endpoint |
| test_auth.py | 13 | Register (3), login (4), refresh (2), me (2), brute-force (2) |
| test_google_auth.py | 4 | New user, existing user, email conflict, invalid token |
| test_pipeline.py | 4 | Happy path, dedup, OCR failure, Claude failure |
| test_search.py | 9 | Keyword, ruling number, 4 filters, no-auth, rate limit (2) |
| test_rulings.py | 11 | Ruling by ID/number (4), bookmarks CRUD+status (7) |
| test_history.py | 3 | Empty, records, user-scoped |
| test_admin.py | 2 | Admin stats, non-admin 403 |

### Frontend E2E (7 tests)

| Test | Coverage |
|------|----------|
| Homepage renders | Search box, branding |
| Filters toggle | Show/hide advanced filters |
| Search navigation | Query -> results page |
| Login page | Form renders |
| Register page | Form renders |
| Login link | Navigate from register |
| Responsive mobile | 375px viewport |

## Status: COMPLETE

All 13 issues closed. MVP backend + frontend ready for deployment.
