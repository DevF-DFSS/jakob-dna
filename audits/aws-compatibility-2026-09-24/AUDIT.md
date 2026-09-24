# Read-only AWS compatibility audit against PR #4

Observed 2026-09-24, 04:54:00–04:57:25 UTC. Verdict: **🚫 BLOCKED — PR #4 is not deployable as-is against the observed runtime.**

## Scope, provenance, and safety

Read AGENTS.md, [issue #1](https://github.com/DevF-DFSS/jakob-dna/issues/1),
[PR #3](https://github.com/DevF-DFSS/jakob-dna/pull/3) at
8b42fd0ebc5850a82e2629006677ad41900c1748, and
[PR #4](https://github.com/DevF-DFSS/jakob-dna/pull/4) at
cbe8eeff045802a305a98b78d743328f17403dcf, including its Lambda, protocol profile,
tests, and canon delta. Both remain unchanged. This audit branch starts from
their common recovery base 6cc3649a9801fa7a5f7e14f399e8725190180083.

AWS connector reads inspected account 083127296577 across all 17 regions returned
by DescribeRegions(AllRegions=False). Lambda, DynamoDB, REST API and HTTP/WebSocket
API inventories were read in each region. Two functions, four tables and three
HTTP APIs were returned, all in us-east-1/us-east-2; no REST APIs were returned.
GetFunction, DescribeTable, route/integration/stage/authorizer reads, Lambda
resource policies, execution-role trust/inline/managed policies and policy
simulation supplied the details. Source-named S3 buckets were checked by metadata.
The sanitized evidence and API-call ledger are in evidence.json.

No Lambda or API invocation, DynamoDB item read/write, secret-value read, package
download, AWS mutation, deployment, or credential rotation occurred. Environment
variables were reduced inside the AWS script to names, TABLE_NAME presence, and
matches against listed tables. Environment values and signed package URLs were
never returned or saved. GetFunction's package metadata was retained; Code.Location
was discarded. No policy changes were made.

All findings use these exact classes:
- ✅ COMPATIBLE: the named, bounded contract facet matches observed evidence.
- ⚠️ MIGRATION REQUIRED: a known mismatch or configuration transition is needed.
- 🐈📦 UNRESOLVED: evidence is missing or insufficient; not a success or absence claim.
- 🚫 BLOCKED: deployment must not proceed until the stated prerequisite is resolved.

## Compatibility matrix

| Finding | Classification | Live evidence versus PR #4 | Required action / limitation |
|---|---|---|---|
| Overall deployment | 🚫 BLOCKED | Neither function has TABLE_NAME; no table has the candidate's primary key; all ingress routes use NONE authorization | Resolve target, schema, authorization and migration before release |
| us-os-brain runtime/handler only | ✅ COMPATIBLE | us-east-2; python3.12; lambda_function.lambda_handler; Zip/x86_64 | Matches Python source/handler shape, not package contents or integration behavior |
| DFSS-ColdStart runtime | ⚠️ MIGRATION REQUIRED | us-east-1; nodejs24.x; index.handler; Zip/x86_64 | Python candidate cannot replace this package under unchanged runtime/handler |
| TABLE_NAME configuration | ⚠️ MIGRATION REQUIRED | Absent on both functions; neither GetFunction response reported an environment error | PR #4 returns persistence_failed for otherwise valid envelopes until explicit target is configured |
| Other environment dependencies | 🐈📦 UNRESOLVED | DFSS-ColdStart has no variable names; us-os-brain has GEMINI_API_KEY and SECRET_HANDSHAKE_TOKEN | Values were not inspected; candidate uses neither. Determine existing behavior before replacement; do not infer that legacy handshake protection survives |
| jakob-memory-store base key | ⚠️ MIGRATION REQUIRED | us-east-1: HASH memoryId:S, RANGE timestamp:N | Candidate writes userId, not memoryId. userId-index is a GSI, not the table partition key; a candidate put lacks memoryId |
| DFSS_SessionState key | ⚠️ MIGRATION REQUIRED | us-east-1: HASH session_id:S, RANGE timestamp:S | Both partition attribute and sort-key type conflict with userId:S / timestamp:N |
| jakob-identity-profiles key | ⚠️ MIGRATION REQUIRED | us-east-1: HASH profileId:S, RANGE version:N | Identity table is not an envelope table |
| us-os-memory key | ⚠️ MIGRATION REQUIRED | us-east-2: HASH session-id:S; no sort key | Not compatible with candidate composite key |
| Region resolution | ⚠️ MIGRATION REQUIRED | Candidate creates DynamoDB resource without explicit region; Python function runs in us-east-2 while jakob-memory-store exists in us-east-1 | TABLE_NAME alone does not select another region. Co-locate the chosen target or review an explicit-region change |
| HTTP API event transport | ✅ COMPATIBLE | All three integrations use AWS_PROXY / payload format 2.0 | Candidate supports body/base64 transport. This does not establish V6 caller payload compatibility |
| kirmld16gb route target | ⚠️ MIGRATION REQUIRED | ANY /session → DFSS-ColdStart in us-east-1; $default auto-deploy stage | Portal route reaches the Node.js function, not the Python function |
| qjiuor3yak route target | 🐈📦 UNRESOLVED | ANY /us-os-brain in us-east-1 → us-os-brain in us-east-2; $default auto-deploy | Actual intended replacement target and consumers must be selected; no live invocation performed |
| p9qtqpd8mc route target | 🐈📦 UNRESOLVED | ANY /us-os-brain in us-east-2 → us-os-brain; stages default and v2 auto-deploy | Select intended stage/client migration path; current requests were not sampled |
| Authenticated ingress prerequisite | 🚫 BLOCKED | Every route AuthorizationType=NONE, no API authorizers, execute-api endpoint enabled | PR #4 verifies an unkeyed hash and has no sender authentication. Existing in-function secret checks, if any, would not be inherited by replacement |
| Lambda API invoke policies | ✅ COMPATIBLE | API Gateway service principal and route-scoped SourceArn grants exist for the observed target functions/APIs | Configuration-level match only. No invocation proof; see cross-region note below |
| Lambda role trust | ✅ COMPATIBLE | Both roles trust lambda.amazonaws.com | Trust alone is not effective permission proof |
| Identity-policy PutItem allowance | ✅ COMPATIBLE | Both roles attach AmazonDynamoDBFullAccess; us-os-brain also attaches AmazonDynamoDBFullAccess_v2; policy statements allow dynamodb:* on * | Identity-policy facet only; not an end-to-end service authorization claim |
| Least-privilege dependency plan | ⚠️ MIGRATION REQUIRED | Broad DynamoDB and additional service permissions exceed candidate's narrow write requirement | Plan scoped execution roles for approved resources, preserving existing dependencies until migration is complete |
| Effective authorization | 🐈📦 UNRESOLVED | Simulation returned allowed but a placeholder EvalResourceName instead of any requested concrete table ARN | Do not accept this as per-table proof. SCP/RCP and complete effective access were not established |
| Table resource-policy observations | ✅ COMPATIBLE | GetResourcePolicy returned PolicyNotFoundException for all four tables | No table policy was found by that API. This does not cancel other policy layers |
| Package identity → source | 🐈📦 UNRESOLVED | Live package digest/size/time captured below; no build artifact linked to candidate SHA | Source SHA is not a Lambda ZIP digest. Obtain reproducible build provenance |
| Version/rollback baseline | ⚠️ MIGRATION REQUIRED | Both functions expose only $LATEST; no aliases or function URLs returned | Plan versioned release/rollback without replacing current traffic during validation |
| S3 historical source names | ✅ COMPATIBLE | jakob-asset-store and jakob-backup-vault exist in us-east-1 | Name/region existence only; PR #4 does not use S3; contents/access not tested |
| Historical API 8vkx3p2m1h | 🐈📦 UNRESOLVED | Not returned by REST/HTTP API inventory in the 17 enabled regions/account | No claim about other accounts, disabled regions or historical deletion |
| Historical Lambda names | 🐈📦 UNRESOLVED | JakobWebhookProcessor, JakobMemoryRetriever and jakob-apex-node not in observed inventory | Do not equate them with either live function without deployment evidence |
| Caller/consumer schema | ⚠️ MIGRATION REQUIRED | PR #3 source audit records portal session_id/node/system_state requests; candidate requires exact V6 fields and integrity | Source-level caller mismatch; live traffic composition remains unobserved |
| End-to-end persistence semantics | 🐈📦 UNRESOLVED | Candidate stores envelope references and rejects duplicate sender/millisecond keys | Existing read consumers, multi-event concurrency, reference-content verification and freshness requirements need proof |

### Package and configuration anchors

| Function | Region | CodeSha256 (base64) | ZIP bytes | Last modified |
|---|---|---|---|---|
| DFSS-ColdStart | us-east-1 | oxASv7o2YUrSemT/446BL/wOwSFAB48wVLKegnRWcVc= | 1395 | 2026-07-01T00:51:03Z |
| us-os-brain | us-east-2 | JhkvoF8994yx4+vDTXFULD4+iNXCaafqsJmcrbnoI8M= | 2909 | 2026-06-28T17:51:04Z |

These identity anchors are 🐈📦 UNRESOLVED for candidate lineage. Both configurations
report Active / Successful, 3-second timeout, 128 MB, and no layers in the response.
Those are control-plane observations, not load-test or dependency-availability proof.
Runtime dependency packaging and performance remain 🐈📦 UNRESOLVED.

Execution roles: DFSS-ColdStart-role-io8kh35x and us-os-brain-role-c7v6jeb1.
Both have logging policies and DynamoDB full-access managed policy attachments.
No inline policies or permissions boundaries were returned. Their observed trust
and identity-policy statements are in the sanitized evidence. The simulator's
placeholder result is preserved rather than silently replaced with a guessed ARN.

The cross-region qjiuor3yak grant uses the Lambda's us-east-2 region in its
SourceArn. This is **✅ COMPATIBLE for that region component**, not a mismatch:
AWS documents that cross-region API Gateway invocation uses the function's region
in this condition. See [AWS Lambda API Gateway permissions](https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html).
API identity, path and wildcard stage/method grants were also inspected, but not invoked.

## Exact blockers to deploying PR #4

1. **🚫 BLOCKED — no compatible destination configured.** TABLE_NAME is missing
   on both functions; none of the four actual base-table keys matches PR #4.
   Selecting jakob-memory-store unchanged does not fix it: its required memoryId
   attribute is absent from candidate items.
2. **🚫 BLOCKED — no safe replacement target established.** The portal route
   targets Node.js, while the candidate is Python. The existing Python function
   is in another region from the historically named table and may contain model
   and handshake behavior not reproduced by PR #4.
3. **🚫 BLOCKED — authenticated-ingress prerequisite is unmet for candidate
   replacement.** All observed routes have NONE authorization. API keys or hash
   checks would not prove sender identity; PR #4 does not consume the current
   handshake variable.
4. **🚫 BLOCKED — caller/reader transition is unproved.** Existing source payloads
   fail the strict V6 contract. No evidence demonstrates compatible deployed
   producers, readers, or an agreed migration of legacy identifiers/state.
5. **🚫 BLOCKED — release artifact and rollback gates are incomplete.** No
   candidate build/package digest is mapped to a target function/version. Current
   integrations address unqualified functions and no aliases were returned.
   Approval of code alone is not deployment authorization.

## Proposed migration sequence — plan only

1. **🐈📦 UNRESOLVED → evidence gate:** choose the intended function/API/region and
   document current package behavior and all producers/consumers using sanitized
   evidence. Retain PR #3 and PR #4 as distinct references.
2. **⚠️ MIGRATION REQUIRED:** approve a storage decision. Preferred isolation is a
   new, explicitly named envelope table with userId:S / timestamp:N in the target
   function's region, leaving existing tables intact. Alternative: revise the
   candidate schema and reader contract to intentionally support memoryId. Do not
   treat a GSI as a replacement base key. No table creation is authorized here.
3. **⚠️ MIGRATION REQUIRED:** design authenticated ingress and sender binding,
   scoped role permissions, configuration and dependent secret references without
   exporting or rotating values. Preserve model/handshake dependencies until their
   consumers and retirement plan are known.
4. **⚠️ MIGRATION REQUIRED:** adapt producers to exact V6 serialization; define
   reader mappings, replay/freshness rules and event identity. Define legacy data
   handling explicitly; never invent historical integrity or provenance.
5. **🐈📦 UNRESOLVED → validation gate:** build a reproducible candidate package,
   record source SHA/package digest, pin dependencies, and test with real SDK
   marshalling plus isolated nonproduction resources. Prove invalid envelopes never
   write, valid writes match real keys, conflicts do not overwrite, and unauthorized
   requests fail. These integration tests require separately scoped execution.
6. **⚠️ MIGRATION REQUIRED:** prepare version/alias release and rollback plans,
   explicit API routes/stages and configuration diffs. Validate auto-deploy stage
   consequences; do not replace $LATEST serving current traffic as a test.
7. **🚫 BLOCKED pending explicit change approval:** present the concrete deployment
   and any migration/data-write plan for approval. Only then conduct controlled
   rollout and observe outcomes. This audit performs none of those actions.
8. **🐈📦 UNRESOLVED → evidence gate:** after separately approved validation, record
   dated package-to-function, route and persistence proof before promoting canon
   to deployed/compatible status.

## Assumptions still requiring proof

Every item here is **🐈📦 UNRESOLVED**:
- Which live function is intended to implement JaKoB V6, and whether replacement
  would remove required model calls, handshake checks or response behavior.
- Current package contents, build lineage and exact dependency versions.
- Complete effective authorization including organization controls; the simulator
  output is not resource-specific evidence.
- Existing data semantics, readers, producers, region expectations and tolerable
  interruption/rollback behavior. No item contents or request logs were read.
- Whether sender is a stable authorized identity and whether one event per
  sender/millisecond is sufficient.
- Payload-reference content integrity and authorization, and freshness/replay rules.
- Resources in other accounts, opt-in regions not returned by discovery, and any
  external Apps Script/Gmail producers or custom ingress surfaces.
- Candidate behavior under actual SDK/service integration and performance limits.

## Checks and reproducibility

**✅ COMPATIBLE — offline checks passed:** all 28 tests from the exact PR #4 source
were rerun with mocked SDK interactions; nine new snapshot-classification tests
passed. These validate local behavior and evidence interpretation, not deployed
execution. check_contract.py reads sanitized evidence.json only, with no SDK,
network, or mutation path. It explicitly distinguishes table keys from indexes
and never infers compatibility from absent evidence.

Run: python3 -m unittest discover -s audits/aws-compatibility-2026-09-24 -v
and python3 audits/aws-compatibility-2026-09-24/check_contract.py.
Run candidate tests on PR #4 separately: python3 -m unittest discover -s tests -v.

**🐈📦 UNRESOLVED — tool limitations:** initial scripts hit validation/API naming
errors and an unavailable exception-class binding. Corrected reads completed.
The API ledger includes final successful calls and the four expected
PolicyNotFoundException responses; those are not access-denied failures.
No denied inventory read is being disguised as an empty inventory. Simulation
returned a generic resource placeholder and is explicitly not counted as proof.
