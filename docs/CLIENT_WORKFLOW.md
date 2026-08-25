# Client Delivery Workflow

## 1. Discovery
Collect the exact repetitive workflow:
- trigger
- inputs
- systems involved
- business rules
- expected outputs
- exceptions
- actions that require approval

## 2. Workflow Map
Turn discovery into a diagram before implementation.

Example:

```text
Gmail email
→ identify intent/order
→ fetch Shopify order
→ check policy
→ recommend action
→ human approves
→ create reply / execute action
```

## 3. Client Sign-off
Confirm the workflow and edge cases with the client before building.

## 4. Build
Use AI coding tools aggressively for implementation, but keep:
- contracts
- tests
- business rules
- credentials
- security decisions
under engineering control.

## 5. Acceptance Tests
Create real examples with expected outputs and let the client confirm them.

## 6. Deploy + Observe
Add logs, retries, idempotency, metrics, and clear manual fallback.

## 7. Reuse
Repeated client workflows become reusable modules. Only productize after repeated demand appears.
