# Architecture — v3.0.0

## Core rule

```text
LLM / rules understand language
Shopify provides authoritative facts
Policy provides constraints
Deterministic rules choose the recommendation
Humans control sensitive next steps
Gmail creates drafts first; sending requires an explicit human action
```

## Runtime pipeline

```text
Gmail / Demo Message
       ↓
Message cleanup + support filtering
       ↓
Understanding provider (Rules or OpenAI)
       ↓
Deterministic order reference extraction
       ↓
Shopify read-only lookup
       ↓
Policy lookup
       ↓
Deterministic DecisionEngine
       ↓
ReplyGenerator
       ↓
Structured Decision Trace + timings
       ↓
Case persistence
       ↓
Human correction / approval / rejection
       ↓
Gmail Draft creation (real Gmail cases only)
```

## Explainability

Every new case stores a structured trace with these conceptual stages:

1. AI / request understanding
2. Order extraction
3. Shopify verification
4. Policy applied
5. Deterministic rule
6. Recommended action
7. Human approval

This prevents the UI from presenting Shopify facts as model assumptions.

## Human corrections

Corrections are additive audit records. The effective analysis may be recomputed, but the original result is stored in the correction record and remains inspectable.

## Automation Lab

Simulations call the same understanding, Shopify-read, policy, decision and drafting layers but do not persist a customer Case and never send email or execute a Shopify mutation. Timings are recorded for operational observability.

## Customer Signals

Signals are calculated from persisted cases/actions/corrections. The API does not fabricate trend percentages when the data does not support them.

## Persistence

- `cases`: effective operational case state
- `actions`: audit events
- `case_corrections`: before/after human corrections
- `simulations`: Automation Lab history

SQLite remains convenient locally. PostgreSQL is the Docker/deployment target.

## Reliability

- Gmail message IDs provide case idempotency.
- Gmail draft creation is idempotent through the action audit record.
- Shopify transient failures/rate limits are retried.
- Gmail uses client retry support.
- Celery/Redis is available for background jobs.
- request IDs are attached to API responses/logs.

## Security boundary

Optional password authentication can protect a private deployment. Secrets remain backend-only. Public portfolio deployments should use Demo mode with no real customer data.

## External action boundary

Gmail automatic sending remains disabled. The application may optionally send an already reviewed Gmail Draft only when `GMAIL_MANUAL_SEND_ENABLED=true`; production mode additionally requires authentication. Shopify order mutations remain disabled.
