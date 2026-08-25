# AI Ops v3.0.0 — Final local upgrade

Extract this release over the existing working project. The archive deliberately excludes:

```text
backend/.env
backend/credentials.json
backend/token.json
backend/dev.db
backend/.venv/
```

Your existing Gmail/Shopify secrets therefore stay local and are not overwritten.

## Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts\init_db.py
python scripts\verify.py
python scripts\preflight.py
uvicorn app.main:app --reload
```

## Frontend

In a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open `http://127.0.0.1:5500`.

## Recommended current local mode

```env
AI_PROVIDER=rules
SHOPIFY_MODE=live
GMAIL_MODE=live
GMAIL_MANUAL_SEND_ENABLED=false
TASKS_MODE=sync
AUTH_MODE=off
ALLOW_LIVE_ACTIONS=false
```

Keep OpenAI and Celery optional until the final local workflow is accepted.

## Logo

Replace `frontend/assets/logo.svg` with the final logo when ready. The application shell already reserves the correct logo area.
