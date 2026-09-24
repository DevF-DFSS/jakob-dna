# Canon delta — 2026-09-24 — proposed isolated V6 migration

Classification: PROPOSED DESIGN; evidence unchanged; no deployment performed.

Read AGENTS.md, Issue #1, PR #3 characterization, PR #4 remediation and PR #5 AWS
compatibility evidence. The live-state anchor remains PR #5's 2026-09-24
04:54–04:57 UTC snapshot. No AWS state was queried or changed for this design.
No secret values were needed, disclosed or rotated.

## Decision proposed for review

Prefer a NEW isolated V6 Lambda/runtime, authenticated API and clean PK:S/SK:S
DynamoDB event table. Keep DFSS-ColdStart, us-os-brain, their routes, tables and
credentials intact. Neither Python-language similarity nor package metadata
proves source/deployment lineage. Historical documents do not override live keys.

Keep canonical ten-field JEL-JKB/6.0 envelope unchanged. Add a separately versioned
transport wrapper with UUIDv4 event_id and submission issued_at. This requires
new implementation beyond PR #4. Server-owned principal-to-tenant/sender binding
is distinct from JWT authentication, SHA-256 content integrity, freshness and
conditional event identity. Accepted receipts imply durable acceptance only.

The clean storage profile intentionally differs from PR #4's userId/timestamp
proposal. No existing record or reader is silently reinterpreted. PR #4 remains
not deployable as-is against the PR #5 snapshot, and is not modified here.

## Preservation and validation

PR #3 remains the characterization baseline; PR #4 the remediation candidate;
PR #5 the compatibility snapshot. This proposal is a separate review branch.
No IaC, automatic deployments, production handlers or migrations are included.
18 synthetic offline model tests passed on 2026-09-24. They are decision
scaffolding, not proof of JWT validation, service atomicity or effective IAM.
See [design](../../designs/isolated-v6-2026-09-24/DESIGN.md) for both decision
matrices, resource/permission requirements, rollback sequence and deployment gates.

## Still unresolved

- 🐈📦 Identity provider/claims, binding authority, scopes and revocation mechanics.
- 🐈📦 Approved accounts/region/residency, owners, budget, retention and recovery goals.
- 🐈📦 Client adoption of wrapper/IDs, freshness and duplicate semantics, reader migration.
- 🐈📦 Legacy source lineage and behavior, actual callers/consumers and import provenance.
- 🐈📦 Payload-reference content authority/integrity; references are not fetched.
- 🐈📦 Real SDK/IAM/JWT/concurrency/load/rollback evidence and future execution needs.

These are open gates, not implicit approvals or claims of compatibility.
