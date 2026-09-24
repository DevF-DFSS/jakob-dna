# AWS compatibility canon delta — 2026-09-24

Observed 04:54–04:57 UTC in account 083127296577. Scope: all 17 enabled regions
returned by discovery, read-only control-plane APIs, no invocation or item access.
Source candidate: PR #4, cbe8eeff045802a305a98b78d743328f17403dcf.
Baseline: PR #3, 8b42fd0ebc5850a82e2629006677ad41900c1748. Neither changed.

**🚫 BLOCKED:** PR #4 is not deployable as-is against this snapshot.

New evidence changes:
- **⚠️ MIGRATION REQUIRED:** neither live Lambda has TABLE_NAME.
- **⚠️ MIGRATION REQUIRED:** jakob-memory-store has memoryId:S / timestamp:N
  base keys. userId is a GSI key, not the partition key asserted in older docs.
- **⚠️ MIGRATION REQUIRED:** other live table keys are session_id:S/timestamp:S,
  profileId:S/version:N, and session-id:S with no sort key. None matches PR #4.
- **⚠️ MIGRATION REQUIRED:** portal API kirmld16gb targets DFSS-ColdStart,
  nodejs24.x/index.handler. Python candidate cannot replace it unchanged.
- **✅ COMPATIBLE:** us-os-brain is python3.12 with the candidate handler name;
  this verifies only runtime/handler shape.
- **🚫 BLOCKED:** all three HTTP API routes have NONE authorization and no
  authorizers. Candidate SHA-256 validation is not authenticated ingress.
- **✅ COMPATIBLE:** API Gateway integrations use payload format 2.0 and
  target invoke-policy grants exist; configuration compatibility only.
- **🐈📦 UNRESOLVED:** live package digests are available, but source-to-package
  lineage, effective authorization, producers/readers and rollout target remain
  unproved. IAM simulation returned a placeholder resource ARN.

Historical source claims are retained at their timestamps, not rewritten. No AWS
state, credentials, PR #3 or PR #4 were changed. No secrets or environment values
are recorded. Full matrix, package identity anchors, blockers, migration plan and
sanitized evidence are in audits/aws-compatibility-2026-09-24/AUDIT.md.

Next coordinate: select the intended runtime and a storage/authentication migration
design, then prove compatibility in an isolated environment under separately
scoped authorization before proposing production changes.
