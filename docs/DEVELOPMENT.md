# Development

## Environment

Copy `.env.example` to `.env`. Django uses `backend/db.sqlite3` as the sole local development database. Never commit `.env`.

## Backend

From the repository root:

```powershell
pip install -r backend/requirements/base.txt
python backend/manage.py check
python backend/manage.py migrate
python backend/manage.py test
```

Create an administrative user with `python backend/manage.py createsuperuser`. Model migrations belong in each application’s `migrations/` package.

## Frontend

```powershell
cd frontend
npm install
npm run lint
npm run build
```

Keep API access in `services/`, types in `types/`, and reusable display components under `components/`. Test both RTL and LTR at the responsive acceptance sizes, especially 763×651.

## Docker

After supplying `.env`, run `docker compose up --build`. The compose stack starts PostgreSQL, Redis, Django, and Next.js. Run migrations in the backend container after initial startup.
