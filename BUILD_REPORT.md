# Build Report — AI Ops v3.0.0

Build date: 2026-08-25

## Verification

- Backend tests: **28 passed**
- Python compile check: **passed**
- Frontend JavaScript syntax: **18 files passed**
- Frontend relative import graph: **passed**
- Regression intent classification: **20/20**
- Regression order extraction: **20/20**
- Release safety scan: **passed**
- Docker Compose / CI YAML parse: **passed**
- Database initialization smoke test: **passed**

The 20/20 regression results use an intentionally simple mock dataset and are not a production-accuracy claim.

## Safety boundary verified

- automatic Gmail sending: disabled; reviewed manual send is opt-in and disabled by default
- Shopify refund/cancel/modify mutations: disabled
- Shopify remains read-only for operational facts
- human approval is required before real Gmail draft creation
- approved draft content is locked before Gmail draft creation

## Packaging

The release archive excludes local runtime/secrets such as `.env`, OAuth credentials/token files, local databases, `.venv`, Python caches and test caches.
