# Interview Notes

## 30-second explanation

I built a single-store AI e-commerce operations system that ingests real Gmail
support messages, extracts intent/order references, reads authoritative order
facts from Shopify GraphQL, applies deterministic business rules and policy,
persists a case, requires human approval, and creates a Gmail reply draft.

## Why not Email -> LLM -> Refund?

Because language models are not an authoritative source for order state,
business policy, or approval. Shopify supplies facts, policy supplies
constraints, deterministic rules decide actions, and humans approve sensitive
operations.

## Production lessons

- Idempotency matters because inbox polling and retries can deliver the same event twice.
- API integrations need retries, timeouts and safe errors.
- OAuth and protected customer data are real engineering work.
- Model confidence is not automatically calibrated.
- A simple rules baseline is useful for evaluation and fallback.
- Draft-first execution is the default. A reviewed manual send can be explicitly enabled, while auto-send remains disabled.
- Multi-tenant SaaS onboarding is a separate architecture from a single-client integration.
