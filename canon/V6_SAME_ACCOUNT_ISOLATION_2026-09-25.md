# V6 same-account containment delta — 2026-09-25

Status: DOCUMENTED / OFFLINE TESTED / NOT DEPLOYED; schema CONFLICT remains.
Canonical parent: reviewed PR #11 `42cf882bae2fe9ab7020c8c62c7cea189525bc64`.
PR #12 is a new stacked candidate. Historical sibling evidence and PR #9/#11
runtime code remain intact. No deployment authorization exists.

The interrupted work survived as local files (no Git checkout/index/local
commits); it was continued in place. Parent candidate/core snapshots were checked
against saved parent Git blob hashes. Publication uses Git data API with exactly
this parent, not a recreated or rebased historical branch.

## New implementation, not live evidence

- Separate new-resource bootstrap for private/versioned/retained artifact storage,
  empty HTTP API, publisher/deployment roles and bootstrap-owned boundaries.
  Runtime imports exact bootstrap outputs; no artifact/API dependency cycle.
- One full Lambda ResourcePolicy, no Lambda Permission resource. Explicit known
  legacy principal denies use only the 29 documented supported action names;
  Gateway source account/API/sandbox routes restrict alias invocation, and direct
  IAM invocation is explicitly denied in the model.
- Known legacy DynamoDB table/index denies plus unchanged GetItem/PutItem runtime
  permissions. New runtime boundary also explicitly denies other actions/resources.
- S3 deny-by-principal boundary preserves only approved recovery, new publisher
  and deployment roles. Deployment boundary cannot rewrite bootstrap boundaries
  and requires exact runtime boundary at role creation and Lambda-only PassRole.
- Current legacy identities are explicit evidence/configuration, not discovery:
  PR #10 role metadata plus user-provided gateway name with unknown current path.

Resource-policy enforcement is not identity-policy/boundary enforcement.
Unsupported Lambda configuration/policy-replacement paths are NOT claimed blocked
by its resource policy. New boundaries do not alter legacy identity policies.
Root/privileged administrators and trusted deployer policy changes remain outside
containment. Creation windows, effective caller policies and stack/PassRole access
must be reviewed before any deployment. Same-account is not separate-account isolation.

Detailed enforcement matrix, source links, recovery constraints and migration
sequence: [isolation design](../aws/isolated-v6/isolation/DESIGN.md).

## New offline results (distinct from PR #11's historical 206 tests)

231/231 tests pass; zero failures/errors/skips. Core 86, candidate 41,
activation/SDK 50, prior remediation 29, new failed-lint gate 1, isolation 24.
Sockets, SDK HTTP transport and credential resolver are blocked. The finite policy
model is NOT AWS IAM simulation. No service behavior is proven.

Pinned cfn-lint 1.40.2, both templates:
- us-east-1: exit 6, 8 findings (E3006 x1, W3037 x6, W6001 x1).
- auxiliary eu-west-1: exit 4, 7 findings (W3037 x6, W6001 x1).
- Static security contracts pass. No cfn-guard installation/run claimed.

Official CloudFormation syntax says FunctionResourceArn; examples, CDK and the
local eu-west-1 schema say ResourceArn. The latter is provisional in this candidate.
The local us-east-1 schema lacks the new type, and the IAM catalog lacks new policy
management actions. No schema override or warning suppression. This remains
🐈📦 UNRESOLVED, not an authoritative deployability determination.

Ordinary build fails on lint; explicit diagnostic-only build retains failed
lint in provenance and cannot pass the release validator. Final-head two-build
and Git input verification results are recorded in the PR handoff rather than
embedding a self-referential head SHA in this source tree.

SHA-256:
- Runtime ZIP: `964269c33919dbbb3e46f4f12b2685dde834a001bdeffab9261fcc86d6beced3`
  (same as PR #11; no runtime/binding changes).
- Runtime template: `1aa415937400720cd7804c7ad04d3358a489f2e0b2e04f5dc5e9b2014cbc43fa`
- Bootstrap template: `c7b10b8fd7854ccc791b6cfa5663ee76ea83607d974fb4177bc4dfefd8599449`
- Unconfigured bindings: `1e1612ea14057a336f9ef5d66df10b8f569940e1e673c9c92fdf260609d78c6b`

## Still blocked

🐈📦 Authoritative schema resolution; effective IAM/SCP/boundaries and all direct
invocation/unsupported management paths; principal completeness; approved recovery
and stack/PassRole controls; bootstrap attachment windows; new bootstrap/runtime
release attestation; account/region/provider/bindings approval; real Gateway JWT
and context; artifact retrieval; DynamoDB concurrency/durability; monitoring/cost;
release convergence; independently authorized deployment and production migration.

No AWS API calls, deployments/mutations, invocations, item operations, S3 uploads,
secret reads, credential discovery/rotation, legacy changes, paid external agents,
PR merges/closures/rebases or semantic state layer occurred. Public official AWS
documentation and GitHub operations are the only network work in this task.
