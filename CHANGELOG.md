# Changelog

## 3.0.0

- Rebuilt the frontend as a premium light, responsive Vanilla HTML/CSS/JS SPA.
- Added English/Arabic language switching and RTL/LTR behavior.
- Added Overview, Attention Queue, split-view Inbox, Cases and full Case Workspace.
- Added structured Decision Trace with source separation: AI, Shopify, policy, rules and human approval.
- Added human analysis corrections with persistent correction records and audit history.
- Added Automation Lab simulations with safe no-execution guarantees and processing timings.
- Added Customer Signals derived only from persisted operational data.
- Added Policies, read-only Orders, Integrations, Audit Log and Settings pages.
- Added live/demo source indicators.
- Added optional private password authentication with signed expiring session tokens.
- Added global audit endpoint and additive database tables for corrections/simulations.
- Added GitHub Actions CI and portfolio source notice.
- Preserved safety boundaries: no Gmail auto-send, opt-in reviewed manual send only, and no Shopify order mutations.
- Added final premium light design tokens and replaceable logo slot.
- Added LIVE / DEMO / MIXED environment separation and global Cmd/Ctrl + K search.
- Hardened release checks, local verification scripts and Gmail-message database idempotency.

## 2.0.0

- Real Gmail + real Shopify workflow hardening.
- Idempotency, retries, logging, Celery/Redis foundation and production docs.

- GitHub security hardening: removed runtime databases/build artifacts, internalized Redis/PostgreSQL ports, added manual-send feature gating, CodeQL, Dependabot, CSP headers, and expanded release scanning.
