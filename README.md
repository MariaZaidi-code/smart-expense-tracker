# Smart Expense Tracker

A full-stack personal finance app to track expenses, categorize spending, set budgets, and visualize insights.

## Features
- User auth (register/login, JWT)
- Add/edit/delete expenses with categories, tags, notes, receipts
- Income tracking
- Budgets per category with alerts
- Recurring expenses
- Reports & charts (daily/weekly/monthly/yearly)
- Export CSV/JSON
- Multi-currency support
- Search & filters

## Tech Stack
- Backend: FastAPI, SQLAlchemy, SQLite/Postgres, JWT
- Frontend: React + Vite, Tailwind, Recharts
- Tests: pytest, Vitest

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API
Docs at http://localhost:8000/docs

## Branches
- `main` — stable
- `qaim` — frontend
- `rameen` — backend
- `maria` — integration
PY