# Playto Pay Payout Engine

Minimal payout engine for merchant balances, payout requests, idempotency, and background settlement.

## Backend

- Django + Django REST Framework
- Django-Q for background payout processing
- SQLite for local development, PostgreSQL supported via `DATABASE_URL`

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
