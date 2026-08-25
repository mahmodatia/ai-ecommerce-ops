# AI Ops — E-commerce Automation v3.0.0

Final product release for the single-store review-first AI e-commerce operations scope.

## Product UI

- premium light, Apple-inspired B2B operations interface
- replaceable logo slot at `frontend/assets/logo.svg`
- responsive Vanilla HTML/CSS/JS SPA with no build tool
- English/Arabic switching with RTL/LTR support
- Overview, Attention Queue, split Inbox, Cases and Case Workspace
- Automation Lab, Customer Signals, Policies, Orders, Integrations, Audit Log and Settings
- clear LIVE / DEMO / MIXED environment states
- global case/order/customer search with Cmd/Ctrl + K

## AI / operations engineering

- structured Decision Trace separating AI, Shopify, policy, deterministic rules and human review
- persistent Human Corrections and audit records
- safe Automation Lab simulations with no-execution guarantees
- measured pipeline timing breakdowns
- Customer Signals calculated from persisted case data
- idempotent Gmail message processing and Gmail draft creation
- optional private password authentication
- PostgreSQL / Redis / Celery production path
- GitHub Actions CI

## Safety boundary

- Gmail auto-send: disabled; reviewed manual send is opt-in and disabled by default
- Shopify refund/cancel/modify mutations: disabled
- Shopify is authoritative for order facts
- policy supplies constraints
- deterministic rules recommend actions
- human review remains central

## Secrets

The release archive intentionally excludes `.env`, Gmail OAuth files, local databases and `.venv`. Existing local credentials remain on the user's machine when the archive is extracted over the current project.

## Verification

Run:

```powershell
cd backend
python scripts\verify.py
```

The regression evaluation is a deliberately simple mock set and is not a production-accuracy claim.
