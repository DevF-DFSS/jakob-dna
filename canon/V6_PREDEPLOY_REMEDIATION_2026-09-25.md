# Canon delta — 2026-09-25: portable pre-deployment remediation

Status: OFFLINE VERIFIED / NOT DEPLOYED. Parent: PR #10 head
c81298bc84a3c58590e9155f0d6e3e40a7c994ff. PR #9 remains historically intact.
Sources: PR #10 dated live preflight, PR #9 candidate, this branch's offline
regression suite and static template validation. No fresh AWS inventory run.

Changes and security rationale:

- Removed positive Lambda reservation. PR #10 observed total/unreserved quota 10;
  AWS requires 100 left unreserved. Candidate now shares unreserved concurrency;
  no quota increase requested. This is not production capacity design. Static
  checks reject any reservation field rather than silently reintroduce it.
- nbf is optional only if absent. Present nbf remains strictly parsed, not future,
  and before expiry. Issuer, audience, client, subject, access token use, approved
  scopes, expiry, issuance time and binding authorization remain fail closed.
  Synthetic resource-bound Cognito-style projected fixtures do not prove a real
  provider or Gateway. aud/projection/flow compatibility still needs verification.
- Stage defaults reduced to rate 1 and burst 2, no overrides. Best-effort route
  throttles do not reserve concurrency or cap total cost. Fixed outcome-only logs
  and rejection/unavailable alarms cover caught 503s; existing Lambda alarms plus
  Gateway 4xx provide complementary visibility. No secret/payload/identity logging.
- Versioned release-manifest validator requires explicit approved fields, local
  hashes, matching provenance and valid bindings; shipped manifest is unapproved
  and bindings remain UNCONFIGURED. A consistent declaration still does not grant
  deployment authorization or authenticate an approver. Independent source-tree
  verification is required; no deployment tooling was added.
- Added legacy API IDs and execution-role name to the static exclusion checks.
  No provider-neutral core, DynamoDB adapter or legacy infrastructure changes.

New validation: 203 offline tests pass (177 prior cases + 26 remediation cases,
with additional negative subcases); cfn-lint 1.40.2 zero findings; static allowlist
and negative tests pass. Socket/SDK HTTP/credential resolution are blocked by the
runner. PR #9's 177 tests/artifact remain historical, not this candidate's result.
Final source coordinate, two-build ZIP/provenance comparison and hashes are recorded
in this PR's handoff and local build outputs after the source commit is created.
Neither offline tests nor static validation prove AWS behavior.

Historical lineage remains #2 → #6 → #7 → #8 → #9 → #10 → this remediation.
PR #3 characterization and PR #5 compatibility evidence remain siblings; no blind
merge. PR #4 remains historical alternative. PR #10's evidence/convergence plan
is unchanged, including the finding that same-account isolation is not proven.
A separate sandbox account remains the preferred direction pending human approval.

🐈📦 UNRESOLVED: approved account/region/identity and binding values, actual Gateway
JWT enforcement and claim projection, effective IAM/SCP/boundaries/direct-invoke
protection, shared-capacity impact, real DynamoDB concurrency/durability, new artifact
storage and deployer/PassRole, notification ownership and alarm/live throttle tests,
revised custom-metric/alarm cost, final release-convergence approval, sandbox
activation and production migration. No semantic state model added.

No AWS service calls/mutations, Lambda/API invocations, DynamoDB item access,
credential discovery/rotation, secret reads, paid external agents, historical PR
merges/closures/rebases/force pushes, deployment or production migration occurred.
