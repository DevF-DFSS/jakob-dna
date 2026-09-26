# PR13 authorization delta — 2026-09-25

Parent: PR12 `1eac1a9b88a53128d52bba11170cb6f6d764905d`.
The accepted recovery directory remains read-only. A separate Git clone was used.
On this case-insensitive filesystem Index.html/index.html collide; the preserved
first clone was not edited. The clean sparse checkout excludes only those two
paths, retains the full parent index/tree, and verified all 94 materialized blobs.

Adds only offline authorization gates, negative tests and a non-root recovery
operator proposal. No runtime/template/boundary edits. Each current evidence item
is bound to account/region/operator/recovery/candidate/artifact/template/binding
context. Missing/unverified evidence is UNKNOWN; stale, contradictory, failed or
wrong-context evidence and unresolved blockers are BLOCKED. A synthetic complete
case remains deployment_authorized=false. The real record has no evidence or
approval. Independently authenticated verification and DevF approval remain absent.

The proposed /jel-v6-approved/JaKoBV6RecoveryOperator has unconfigured federated
trust. Normal policy template limits stack/PassRole relationships; elevated initial
bootstrap and emergency repair require separate temporary authority and review.
Neither policy design nor tests establish live IAM effectiveness or recovery readiness.

No fresh AWS calls were made. Historical/user-supplied live findings cannot clear
these gates. PR12 schema/alias/IAM blockers remain. New tests/lint/build results
and final commit/input/hash verification are recorded in the PR handoff to avoid
self-referential provenance. Historical 231-test claims are not reused as new tests.

No AWS mutation/deployment, credentials/secrets, invocation, data operation,
S3 upload, paid agents, historical merge or semantic state layer. Deployment remains
blocked pending actual current evidence, scoped authority, rollback and explicit
DevF authorization.
