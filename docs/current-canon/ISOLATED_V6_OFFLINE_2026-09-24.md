# Canon delta — 2026-09-24 — isolated V6 Phase 1

Status: DOCUMENTED / OFFLINE VERIFIED. Source: new stacked implementation branch
from PR #6 head `8ec33eda8a75e1994257456c3efa1985a31039e7`; engineering checklist
Issue #1; AGENTS.md operating contract. Verification: 86 offline unittest cases
on Python 3.13, including concurrent in-memory conditional inserts. Date of
verification: 2026-09-24. No live runtime verification or cloud changes.

Implemented the exact V6 transport wrapper, strict bounded HTTP/JSON/base64
parsing, PR #4 string-only envelope canonicalization/integrity, UUIDv4 event IDs,
freshness, external trusted principal input, server-owned binding, immutable
store interface, and stable retry/receipt semantics. No real JWT verifier or
DynamoDB adapter is supplied. The new reference implementation lives under
[reference/isolated-v6](../../reference/isolated-v6/README.md).

Authentication, authorization, integrity, freshness and idempotency remain
separate controls. Client-provided authorizer-shaped JSON cannot establish trust.
The trusted principal argument requires a future independently secured host
boundary; a Python type alone is not authentication. Rejected validation,
authorization or freshness cannot reach storage. Accepted state is immutable;
uncertain writes return a retryable error without claiming success.

The storage representation uses immutable canonical wrapper bytes internally;
a future provider adapter must map these to the proposed persisted envelope and
issued_at schema and prove atomic insert/strong-read semantics. In-memory tests
only establish single-process behavior; no persistence beyond process lifetime.

Preserved PR #3 characterization, PR #4 remediation, PR #5 live snapshot and PR #6
design-only branch. No deployment lineage inferred. Issue #1 remains open.

🐈📦 UNRESOLVED: real JWT verification, real DynamoDB concurrency, IAM, API Gateway
configuration, AWS SDK integration, deployment, load testing and cost. Also open:
provider/binding governance, accounts/region, retention/rollback operations,
caller/consumer migration, legacy lineage and payload-reference content integrity.

No AWS calls, deployments, provisioning, credential exposure/rotation, or paid
external AI agents/services were used. Legacy evidence-bearing resources remain
intact; no claim of production readiness follows from this local verification.
