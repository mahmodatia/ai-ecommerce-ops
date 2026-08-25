# Production Checklist

Before a real merchant deployment:

- [ ] Use PostgreSQL, not local SQLite.
- [ ] Put the dashboard behind authentication.
- [ ] Use HTTPS.
- [ ] Put credentials in a managed secret store.
- [ ] Enable database/storage encryption.
- [ ] Configure backups.
- [ ] Set a retention policy.
- [ ] Enable JSON logs.
- [ ] Configure monitoring and alerts.
- [ ] Run `python scripts/verify.py`.
- [ ] Test all four workflows with merchant-approved test orders.
- [ ] Test duplicate Gmail processing.
- [ ] Test Gmail draft idempotency.
- [ ] Test Shopify/Gmail failure behavior.
- [ ] Confirm Shopify scopes are least-privilege.
- [ ] Confirm Google OAuth access/verification requirements.
- [ ] Keep Gmail automatic sending and Shopify mutations disabled.
- [ ] Keep `GMAIL_MANUAL_SEND_ENABLED=false` unless reviewed manual send is intentionally needed.
- [ ] If manual Gmail send is enabled in production, require `AUTH_MODE=password` or stronger identity controls.
