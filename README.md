# AI Ops — E-commerce Automation v3.0.0

A review-first AI operations system for Shopify customer support.

It connects Gmail support requests to authoritative Shopify order facts, applies store policy and deterministic rules, shows an explainable Decision Trace, keeps humans in control, and creates Gmail reply drafts. Automatic email sending and Shopify order mutations are disabled. An optional reviewed manual Gmail send can be enabled explicitly for local/private use.

## Supported workflows

1. Where is my order?
2. Return / Refund
3. Missing / Wrong Item
4. Cancel / Modify

## Architecture

```text
Customer Email
    ↓
Gmail ingestion + cleanup
    ↓
AI / rules understanding
    ↓
Deterministic order extraction
    ↓
Shopify read-only facts
    ↓
Policy constraints
    ↓
Deterministic decision engine
    ↓
Explainable Decision Trace
    ↓
Human correction / approval
    ↓
Gmail Draft creation
    ↓ optional explicit operator action
Reviewed manual Gmail send (disabled by default)
```

**Safety boundary:** Gmail auto-send is disabled. Reviewed manual send is opt-in and production-gated by authentication. Shopify order mutations are disabled.

## Final product screens

- Overview
- Attention Queue
- Split-view Support Inbox
- Cases
- Case Workspace
- Automation Lab
- Customer Signals
- Policies
- Read-only Orders
- Integrations
- Audit Log
- Settings

The frontend is Vanilla HTML/CSS/JavaScript with no bundler requirement, full English/Arabic switching, RTL/LTR behavior and responsive layouts.

## What v3.0.0 adds

- premium light product UI
- Review-first Attention Queue
- structured Decision Trace separating AI, Shopify, policy, deterministic rules and human approval
- sender/order identity guard before customer-facing order disclosure
- prompt-injection boundary: customer email is untrusted input; LLM output cannot directly execute actions
- persistent Human Corrections
- Automation Lab simulations with no-execution guarantees
- pipeline processing timings
- Customer Signals derived from real persisted case data
- global operational Audit Log
- safe Integration Center
- optional private password authentication
- GitHub Actions CI
- Docker/PostgreSQL/Redis/Celery production path

## Upgrade the current working project

This ZIP deliberately does **not** include:

```text
backend/.env
backend/credentials.json
backend/token.json
backend/dev.db
backend/.venv/
```

Extract it over the current working project so the existing Gmail/Shopify setup remains on the machine.

Then:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts\init_db.py
python scripts\verify.py
python scripts\preflight.py
uvicorn app.main:app --reload
```

Frontend in another terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```


## Branding / logo

The UI is already wired for a replaceable logo asset. Replace:

```text
frontend/assets/logo.svg
```

with the final square logo when it is ready. If you prefer a PNG/WebP file, update `frontend/js/brand.js` once. The layout does not need to be rebuilt.

## Recommended current live local configuration

```env
AI_PROVIDER=rules
AI_FALLBACK_TO_RULES=true

SHOPIFY_MODE=live
GMAIL_MODE=live
GMAIL_MANUAL_SEND_ENABLED=false

TASKS_MODE=sync
AUTH_MODE=off
ALLOW_LIVE_ACTIONS=false
```

This keeps the currently working real Gmail + real Shopify flow while avoiding paid OpenAI usage and extra background-process complexity during final acceptance testing.

## Demo mode

For a public portfolio deployment:

```env
AI_PROVIDER=rules
SHOPIFY_MODE=mock
GMAIL_MODE=mock
GMAIL_MANUAL_SEND_ENABLED=false
TASKS_MODE=celery
AUTH_MODE=off
ALLOW_LIVE_ACTIONS=false
```

The UI marks this environment as Demo and never pretends mock data is live.

## Optional private authentication

For a private live deployment:

```env
AUTH_MODE=password
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong password>
SESSION_SECRET=<random 24+ character secret>
```

The frontend shows a login screen and API calls use an expiring signed bearer session token.

## OpenAI

The system is deliberately complete with `AI_PROVIDER=rules` first.

When ready to evaluate paid API usage:

```env
AI_PROVIDER=openai
AI_FALLBACK_TO_RULES=true
OPENAI_API_KEY=...
OPENAI_MODEL=<currently supported model>
```

Choose the exact model from current official OpenAI API documentation when activating it, then compare it against the rules baseline on a held-out evaluation set.

## Docker

Demo/mock full stack:

```powershell
docker compose up --build
```

Services:

```text
Nginx frontend
FastAPI backend
PostgreSQL
Redis
Celery worker
optional Celery beat
```

Private live Gmail container test after local OAuth files exist:

```powershell
docker compose --env-file backend/.env -f docker-compose.yml -f docker-compose.live.yml up --build
```

## Verification

```powershell
cd backend
python scripts\verify.py
```

`verify.py` runs tests, regression evaluation and the release safety scan. The mock evaluation is a deliberately simple regression set, not a production accuracy claim.

## Security automation

The public repository includes:

- release safety scanning for accidental runtime files / obvious secrets
- CodeQL static analysis for Python and JavaScript
- Dependabot update checks for Python, GitHub Actions and Docker
- Docker services bound to localhost where host access is needed; PostgreSQL and Redis stay on the internal Compose network

## GitHub readiness

CI is included in `.github/workflows/ci.yml` and runs:

- Python compile check
- pytest
- regression evaluation
- frontend JavaScript syntax checks

See:

- `UPGRADE_FROM_V2.md`
- `docs/FINAL_PRODUCT_SCOPE.md`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/DEPLOYMENT.md`
- `docs/OPENAI_ACTIVATION.md`
- `docs/GITHUB_RELEASE.md`
- `docs/DEMO_SCRIPT.md`

## Scope boundary

This release intentionally does **not** include:

- automatic email sending
- Shopify refund/cancel/modify execution
- carrier API automation
- warehouse inventory automation
- sentiment analytics
- discounts/store-credit execution
- WhatsApp/voice/social channels
- multi-tenant billing/SaaS onboarding

Those are separate product decisions, not unfinished MVP work.

## Portfolio source notice

This repository is intentionally **not** released under an open-source license. See `NOTICE.md`. The code is public for portfolio review and technical evaluation; no general permission is granted for commercial reuse or redistribution.
