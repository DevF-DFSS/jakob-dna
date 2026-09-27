# MVSU — Minimum Viable Safe Use (private TEST only)

**Status 2026-09-27: not attained; private TEST use is unauthorized.** MVSU means a bounded, reversible experiment with synthetic or clearly non-sensitive data and an explicit time-limited allowlist. It does not mean production readiness, general availability, or a $0 cost promise. The first live bootstrap is a prerequisite observation, not private TEST use.

## Invariants that cannot be waived

1. Exact reviewed source commit, parameter/template/artifact/capability/binding hashes and immutable S3 object version; no substitution by a green CI badge.
2. Real, approved non-root operator and CF service-role path with exact PassRole and expiry; current root connector remains read-only. The independent first-write/role-installation boundary is resolved before bootstrap.
3. Namespace and control-plane containment for known legacy principals, including role reuse, Lambda code/config/policy changes, API routes/authorizers/integrations/stages and CloudFormation role reuse. SourceFunctionArn and AssociatedResourceArn must be verified in the actual service path before trusting them.
4. Inert bootstrap and CLOSED runtime before any TEST ingress. Provider/JWT issuer/audience/client/scope and server-owned binding must be configured and shown to reject bad claims. No forged Gateway-shaped event may authenticate a direct invoke.
5. TEST capability has exact approved synthetic principals, at most one hour, no environment/request/human-text override. Ingress throttling stays conservative.
6. Live negative tests for direct unqualified/version/alias invocation and alternate-Lambda/role reuse; wrong/missing source context, unauthorized/wrong-provider requests, and cross-tenant binding. No ability to bypass policy by changing it as an ordinary principal.
7. Artifact integrity/version readback, explicit quarantine and rollback actors, a failure drill, current evidence and a fresh authenticated DevF authorization for each mutation phase and then private use. The offline phase planner always says deployment_authorized=false.

## Defects tolerable inside this boundary

Rough API ergonomics, manual operator steps, modest telemetry/dashboard coverage, low throughput, incomplete performance tuning, and synthetic-data application bugs may be logged and fixed during dogfood. The known cfn-lint 1.40.2 catalog/schema findings remain visible. For the *inert bootstrap*, they do not concern a deployed Lambda resource; they must still be understood against current registry evidence before the runtime phase. A failed write/read/idempotency test is a bug only while containment keeps it within synthetic TEST scope; it cannot be called a successful workload or promoted to real data. State mutation, cross-tenant leakage, auth or integrity bypass, unbounded ingress, or failed quarantine is a boundary failure: stop use.

MVSU requires the seven phase holds in FIRST_USE_PLAN.md, including live B observations once safely testable. It never requires proving a Lambda lifecycle or JWT service behavior before the minimum inert resources exist.
