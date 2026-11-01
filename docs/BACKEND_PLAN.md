# Smart Expense Tracker — Backend Plan

Owner: Backend. Frontend is owned by another contributor (out of scope here).

## Vision
A robust REST API for personal finance: auth, expenses, income, categories, budgets, recurring transactions, reports, exports, multi-currency.

## Sprints

### Sprint 1 — Core (Week 1)
- Auth: register/login/me with JWT + bcrypt
- User model, DB setup (SQLite dev, Postgres prod)
- Expense CRUD with filters (date range, category, tag, search)
- Category CRUD with default seed
- Pydantic schemas + validation
- Smoke tests

### Sprint 2 — Budgets & Income (Week 2)
- Income CRUD
- Budgets per category (monthly/yearly) with status & alerts
- Recurring expenses (cron-like scheduler)
- Soft delete + audit fields

### Sprint 3 — Reports & Analytics (Week 3)
- Summary: total income/expense/balance
- By category aggregation
- Trends (daily/weekly/monthly/yearly)
- Top expenses, spending velocity
- Multi-currency conversion (FX rates cached)

### Sprint 4 — Data & Ops (Week 4)
- Export CSV/JSON
- Import from CSV
- Pagination, sorting, filtering standardization
- Rate limiting, structured logging, health/readiness
- Alembic migrations, Postgres support
- Docker + compose

### Sprint 5 — Quality & Release (Week 5)
- Test coverage >=90%
- Integration tests, contract tests
- OpenAPI docs polish
- Security review (input validation, SSRF, secrets)
- CI/CD (lint, test, build, deploy)

## Deliverables
- FastAPI app with OpenAPI at /docs
- SQLite dev DB, Postgres-ready
- Test suite (pytest)
- Docker image
- Documentation

## Acceptance
- All endpoints documented and tested
- >=80% coverage
- No critical security findings
- Docker runs end-to-end
PY