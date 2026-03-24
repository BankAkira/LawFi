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
| [ ] | [#2](https://github.com/BankAkira/LawFi/issues/2) | Alembic Migrations & Docker Compose | AFK | None |

### Layer 1 -- Blocked by #2 only

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [ ] | [#3](https://github.com/BankAkira/LawFi/issues/3) | GitHub Actions CI & Seed Script | AFK | #2 |
| [ ] | [#4](https://github.com/BankAkira/LawFi/issues/4) | Email Auth Fix & Tests | AFK | #2 |
| [ ] | [#5](https://github.com/BankAkira/LawFi/issues/5) | Data Pipeline Bug Fixes | AFK | #2 |

### Layer 2 -- Blocked by Layer 1

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [ ] | [#6](https://github.com/BankAkira/LawFi/issues/6) | Data Pipeline Tests | AFK | #5 |
| [ ] | [#7](https://github.com/BankAkira/LawFi/issues/7) | Search Backend -- pg_trgm & Filters | AFK | #2, #5 |
| [ ] | [#9](https://github.com/BankAkira/LawFi/issues/9) | Ruling Detail View & Tests | AFK | #5 |
| [ ] | [#12](https://github.com/BankAkira/LawFi/issues/12) | Google OAuth | HITL | #4 |
| [ ] | [#13](https://github.com/BankAkira/LawFi/issues/13) | Admin API & Monitoring | AFK | #2, #5 |

### Layer 3 -- Blocked by Layer 2

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [ ] | [#8](https://github.com/BankAkira/LawFi/issues/8) | Search Frontend & Rate Limiting | AFK | #4, #7 |
| [ ] | [#10](https://github.com/BankAkira/LawFi/issues/10) | Bookmarks End-to-End | AFK | #4, #9 |

### Layer 4 -- Blocked by Layer 3

| Status | Issue | Title | Type | Blocked by |
|--------|-------|-------|------|------------|
| [ ] | [#11](https://github.com/BankAkira/LawFi/issues/11) | Search History End-to-End | AFK | #4, #8 |
| [ ] | [#14](https://github.com/BankAkira/LawFi/issues/14) | Frontend Polish & E2E Tests | AFK | #4, #8, #10 |

## User Story Coverage

| User Story | Issue |
|-----------|-------|
| 1. Natural language Thai search | #7 |
| 2. Search by ruling number | #7 |
| 3. Filter by case type | #7 |
| 4. Filter by year range | #7 |
| 5. Filter by ruling result | #7 |
| 6. Relevance score | #8 |
| 7. Summary + keyword tags in results | #8 |
| 8. Structured ruling sections | #9 |
| 9. Referenced law sections | #9 |
| 10. View original PDF | #9 |
| 11. Collapsible full text | #9 |
| 12. Bookmark rulings | #10 |
| 13. View all bookmarks | #10 |
| 14. Remove bookmarks | #10 |
| 15. Search history | #11 |
| 16. Register with email/password | #4 |
| 17. Google OAuth | #12 |
| 18. JWT session persistence | #4 |
| 19. Auto-refresh tokens | #4 |
| 20. Daily search limit message | #8 |
| 21. Tier and limit info | #8 |
| 22. Process 100K+ PDFs | #5, #6 |
| 23. Handle text + scanned PDFs | #5, #6 |
| 24. Graceful failure handling | #5, #6 |
| 25. Incremental pipeline | #5, #6 |
| 26. Health check / monitoring | #13 |
| 27. Alembic migrations | #2 |
| 28. CI/CD via GitHub Actions | #3 |
| 29. Docker Compose full stack | #2 |
| 30. Responsive mobile UI | #14 |

## Suggested Sprint Plan (Solo Dev, 8 Weeks)

### Week 1-2: Foundation
- [x] PRD written and approved (#1)
- [ ] #2 Alembic + Docker
- [ ] #3 CI/CD + Seed
- [ ] #5 Pipeline Bug Fixes (start immediately -- pipeline run takes days)

### Week 3-4: Core Backend
- [ ] #4 Auth Fix + Tests
- [ ] #6 Pipeline Tests
- [ ] #7 Search Backend (pg_trgm)

### Week 5-6: Features
- [ ] #8 Search Frontend + Rate Limiting
- [ ] #9 Ruling Detail + Tests
- [ ] #10 Bookmarks

### Week 7: Integration
- [ ] #11 Search History
- [ ] #12 Google OAuth (HITL)
- [ ] #13 Admin API

### Week 8: Polish
- [ ] #14 Frontend Polish + E2E Tests
- [ ] Final QA and deployment
