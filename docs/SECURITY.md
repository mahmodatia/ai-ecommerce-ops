# Security and Privacy Notes

## Secrets

Never commit:

- `.env`
- `credentials.json`
- `token.json`
- Shopify Client Secret
- OpenAI API key

They are excluded by `.gitignore`.

## Least privilege

Shopify is read-only in this version.
Gmail is used to read email and create drafts. Automatic sending is disabled. Reviewed manual sending is disabled by default behind `GMAIL_MANUAL_SEND_ENABLED=false`; production manual sending additionally requires `AUTH_MODE=password`.
`ALLOW_LIVE_ACTIONS=false` remains a hard safety boundary for Shopify mutations.

## Customer/order identity guard

Before the decision engine can recommend disclosing order-specific details, the sender email must match the Shopify order customer email. A mismatch, or an order with no customer email available, forces manual review.


## LLM / prompt-injection boundary

Customer email text is treated as untrusted input. The LLM adapter is limited to structured understanding, the prompt explicitly rejects instructions embedded in customer content, deterministic order extraction overwrites model output, Shopify supplies authoritative order facts, and deterministic rules—not the LLM—select business recommendations. No model tool call can directly send email or mutate Shopify.

## PII

The application needs customer email/order information to perform support work.
Logs intentionally avoid message bodies and credentials.

Use the retention cleanup script and choose a retention period appropriate to the client.

## Production gaps that depend on the deployment environment

A real hosted client deployment should additionally provide:

- HTTPS/TLS
- encrypted database/storage volumes
- authenticated dashboard access
- login rate limiting / enterprise SSO where required
- managed secret storage
- backups
- monitoring/alerting
- incident-response process
- OAuth/app verification required by Google/Shopify for public distribution
- non-root application container user after OAuth token-file permissions are designed for the target host
- dependency lock/pinning and automated vulnerability review before production release

These are infrastructure/account controls, not values that should be faked in code.
