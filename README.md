# Playto Pay Payout Engine

Minimal payout engine for merchant balances, payout requests, idempotency, and background settlement.

## Backend

- Django + Django REST Framework
- Huey for background payout processing
- PostgreSQL preferred locally via Docker Compose

### Setup

```powershell
cd "f:\New folder\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_merchants
python manage.py qcluster
```

Run the API server:

```powershell
python manage.py runserver
```

Run the Huey background worker in a separate shell:

```powershell
python -m huey_consumer backend.huey_conf.huey
```

### Local Docker

```powershell
docker compose up --build
```

Then in another shell, run migrations and seed demo data:

```powershell
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_merchants
```

If the dashboard does not load, confirm the backend has merchant data seeded and check the API logs for errors.

The backend will be available at `http://localhost:8000` and the frontend at `http://localhost:5173`.

### Frontend

```powershell
cd "f:\New folder\frontend"
npm install
npm run dev
```

The React app expects the API at `http://localhost:8000`.

## Notes

- `POST /api/v1/payouts/` requires header `Idempotency-Key: <uuid>`
- Dashboard endpoint: `GET /api/v1/merchants/{merchant_id}/dashboard/`

## Tests

```powershell
cd "f:\New folder\backend"
.\.venv\Scripts\Activate.ps1
python manage.py test payouts_app
```

> Note: the concurrency test is skipped on SQLite because SQLite cannot reliably simulate row-level locking. The test is available for PostgreSQL or other databases that support `SELECT ... FOR UPDATE`.
