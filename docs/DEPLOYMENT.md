# Deployment path

## Public portfolio demo

Use:

```env
AI_PROVIDER=rules
SHOPIFY_MODE=mock
GMAIL_MODE=mock
TASKS_MODE=celery
AUTH_MODE=off
ALLOW_LIVE_ACTIONS=false
GMAIL_MANUAL_SEND_ENABLED=false
```

This produces a safe public demo with no private customer data.

## Private live instance

Use a managed environment with:

```env
SHOPIFY_MODE=live
GMAIL_MODE=live
AUTH_MODE=password
TASKS_MODE=celery
ALLOW_LIVE_ACTIONS=false
GMAIL_MANUAL_SEND_ENABLED=false
```

Set a strong `ADMIN_PASSWORD` and a random `SESSION_SECRET` of at least 24 characters.
Set a strong random `POSTGRES_PASSWORD` (the Compose default is only for local development).
Use a managed secret store rather than committing secrets.

## Required production controls

- HTTPS
- PostgreSQL
- Redis/Celery
- managed secrets
- backups
- monitoring/log aggregation
- authenticated private UI
- domain + TLS
- Google/Shopify verification as required by the chosen distribution model

## Additional hardening for a real hosted client deployment

- run application containers as a non-root user after validating OAuth token-file permissions
- use authenticated/TLS managed Redis where required by the hosting environment
- add login rate limiting or enterprise SSO
- use schema migrations (for example Alembic) rather than startup-only table creation
- pin/lock dependencies for reproducible production builds

## Docker

Mock/demo stack:

```powershell
docker compose up --build
```

Live Gmail credentials are intentionally not baked into images. For a private local/container test use the live override after `credentials.json` and `token.json` already exist:

```powershell
docker compose --env-file backend/.env -f docker-compose.yml -f docker-compose.live.yml up --build
```
