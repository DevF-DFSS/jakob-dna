# Canon delta — 2026-09-24 — offline AWS V6 candidate

Status: DOCUMENTED / OFFLINE VERIFIED. Source: stacked AWS candidate work from
PR #7 head 401893f24e784795efa900ea32554ab1ca61e64c, following AGENTS.md, Issue #1
and PRs #3–#7. No live AWS evidence was obtained; PR #5 remains a dated snapshot.

Added a separate [AWS candidate](../../aws/isolated-v6/README.md): injected
low-level DynamoDB EventStore, exact immutable event/receipt conversion,
conditional PutItem, strongly consistent GetItem, and sanitized uncertainty
mapping. Provider-neutral reference/isolated-v6 remains unchanged. Persistent
representation stores canonical wrapper_json as a String instead of duplicating
envelope and issued_at; this preserves PR #7 records and requires explicit reader
adoption rather than assuming PR #6's illustrative expanded schema.

Added injectable authentication host boundary. The packaged Lambda handler is
intentionally inactive and returns 503 for all requests; no forged authorizer
context is treated as authentication. Real authentication and SDK composition
must be implemented and reviewed before activation.

CloudFormation models only new sandbox resources: JWT-protected HTTP API routes,
explicit stage/deployment, function/version/alias, PK/SK table, dedicated role,
restricted API Gateway invocation grants, logs and alarms. Resource-policy grants
alone do not rule out same-account identity-policy invocation; IAM/SCP/boundary
and bypass evidence remain necessary. No legacy resources are imported or reused.

Verification 2026-09-24: 127 offline tests passed (86 core + 41 new). Covers fake
client conditional conflicts/strong reads/lost-response recovery, marshalling,
immutability, injected auth failures, template negative tests and deterministic
ZIP creation. Socket creation denied during tests. No claims about real service
behavior, SDK serialization or effective authorization follow from these checks.
CloudFormation schema/compliance tools are unavailable; only structural checks ran.

Build tooling records source commit, runtime/Python target, file/dependency hashes,
artifact SHA-256 and actual tests in external provenance. Source attribution is
caller-supplied and requires independent Git-tree verification; no signed build
attestation or deployed artifact relationship is implied. Runtime dependencies
are standard-library only; a real SDK and trusted host composition remain gates.

🐈📦 UNRESOLVED: real JWT provider/issuer behavior, API Gateway enforcement,
IAM/SCP/boundary evaluation, DynamoDB concurrency/durability, approved AWS
account/region, load/cost, caller migration and production deployment. Also
unresolved: SDK pinning/composition, cfn-lint/cfn-guard validation, binding policy,
retention, operational alarms/rollback, and source/artifact attestation.

PRs #3–#7 and all legacy infrastructure remain intact. No AWS API calls,
deployments, Cognito/OIDC provisioning, paid external agents/services, credential
inspection/exposure/rotation, or legacy mutation occurred. Issue #1 stays open.
