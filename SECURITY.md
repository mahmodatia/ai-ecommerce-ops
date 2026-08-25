# Security Policy

This repository is a portfolio/reference implementation. Do not commit live credentials, OAuth tokens, API keys, customer exports, or local databases.

## Supported security posture

- Gmail automatic sending is disabled.
- Reviewed manual Gmail sending is disabled by default and requires an explicit `GMAIL_MANUAL_SEND_ENABLED=true` opt-in.
- In production mode, reviewed manual Gmail sending also requires `AUTH_MODE=password`.
- Shopify order mutations are disabled.
- Public demo mode should use mock Gmail/Shopify data only.
- Live deployments should use HTTPS, managed secrets, protected storage, backups, monitoring, and stronger production identity/access controls.

## Reporting

Please avoid posting secrets or customer data in public issues. If this repository is hosted on GitHub with private vulnerability reporting enabled, use that channel for security reports.
