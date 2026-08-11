# Company Online Store

Production-oriented monorepo foundation for a Persian-first company catalog and inventory store. It uses Django/DRF with PostgreSQL and Redis-ready settings, plus a Next.js App Router frontend.

## Quick start

1. Copy `.env.example` to `.env` and replace every example secret.
2. Backend: create a virtual environment, install `pip install -r backend/requirements/base.txt`, then run `python backend/manage.py migrate` and `python backend/manage.py runserver`. For an isolated SQLite verification run, use `SQLITE_PATH=:memory:`.
3. Frontend: run `cd frontend`, `npm install`, then `npm run dev`.

Open `http://localhost:3000/fa/` for Persian (RTL), `http://localhost:3000/en/` for English, `http://localhost:8000/admin/` for administration, and `http://localhost:8000/api/schema/` for the OpenAPI schema.

For container development, configure `.env` and run `docker compose up --build`.

See [architecture documentation](docs/ARCHITECTURE.md) and [development documentation](docs/DEVELOPMENT.md).
