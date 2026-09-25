# Isolated V6 live deployment preflight — 2026-09-25

**🚫 BLOCKED: PR #9 is not deployable as-is. No deployment is authorized by this audit.**

Target: PR #9 `f7acf43f1f4a87fbbcda068a94a5037427750b24`. This evidence-only branch preserves PRs #2–#9 and the provider-neutral core. Read `AGENTS.md`, Issue #1 and each PR's body, changed-file list/patches and commit parents. [Lineage](CONVERGENCE.md) separates evidence from implementation; [identity/cost](IDENTITY_COST.md) separates capability, configuration and enforcement.

## Evidence and limits

`evidence.json` contains five timestamped connector response projections and API-call ledgers, observed 2026-09-25 11:40–11:48 UTC. 180 metadata/simulation calls: 177 successful, three Organizations calls returned `AWSOrganizationsNotInUseException`. Discovery covered all 17 enabled regions for Lambda, DynamoDB names, HTTP APIs and Cognito user pools; deeper inspection covered us-east-1/us-east-2, the only regions with those legacy runtimes. Global IAM roles/default policy versions and bucket names were inspected. Connector auto-pagination was used. Scripts in `scripts/` reproduce the queries in the AWS connector sandbox; they are not standalone deployment tools.

Metadata only: configuration environment **names** were projected inside the connector; no secret values were returned, inspected or recorded. No function package URLs/downloads, artifact objects, log events or database items were requested. Preliminary connector validation/operation-name errors produced no useful AWS observations and are excluded from the 180-call evidence ledger. API names inside IAM documents or simulation parameters are permissions being analyzed, not operations executed.

✅ VERIFIED observed caller: account `083127296577`, root ARN. This is not account approval, a deployment role, or evidence about stored credential material. Organizations reports this account is not a member: no organization/SCP inheritance observed. Seven IAM roles have no permission boundary in returned metadata. User/group/session policy closure was not inspected. No identity provider token was requested. No preflight endpoint was exercised. Snapshots can become stale.

## PR #5 → current delta

Historical reference: [PR #5](https://github.com/DevF-DFSS/jakob-dna/pull/5), head `a4c2c2666345e663e9f0678878b3c0e1abcc6a9a`, September 24 04:54–04:57 UTC. It is not rewritten. `delta.json` mechanically compares common function/table/API fields against that snapshot; raw evidence supports additional observations below.

| Surface | Delta | Classification and observation |
|---|---|---|
| Enabled-region Lambda/table/HTTP API inventory | unchanged | ✅ VERIFIED two functions, four tables, three HTTP APIs in the same regions. No V6 candidate observed. |
| DFSS-ColdStart, east-1 | unchanged | ✅ VERIFIED nodejs24.x/index.handler, 1,395 bytes, digest `oxASv7o2YUrSemT/446BL/wOwSFAB48wVLKegnRWcVc=`, July 1 modification. 128 MB/3 s, no environment names. |
| us-os-brain, east-2 | unchanged | ✅ VERIFIED python3.12/lambda_function.lambda_handler, 2,909 bytes, digest `JhkvoF8994yx4+vDTXFULD4+iNXCaafqsJmcrbnoI8M=`, June 28 modification. 128 MB/3 s; same two environment names, values excluded. |
| Versions/aliases/invoke policy | unchanged | ✅ VERIFIED only $LATEST, no aliases, same API Gateway policy documents. Function URLs newly checked: none. Package digest stability is not source/deployment lineage. |
| DynamoDB keys | unchanged | ✅ VERIFIED DFSS_SessionState: session_id:S + timestamp:S; jakob-identity-profiles: profileId:S + version:N; jakob-memory-store: memoryId:S + timestamp:N; us-os-memory: session-id:S. All ACTIVE/on-demand. |
| HTTP APIs | unchanged | ✅ VERIFIED kirmld16gb ANY /session → ColdStart; qjiuor3yak and p9qtqpd8mc ANY /us-os-brain → brain. Same stages/integrations, no authorizers, NONE authorization. Preserved, not adopted. |
| Legacy role DynamoDB breadth | unchanged observation | ✅ VERIFIED wildcard DynamoDB policies still attached. New concrete-ARN simulation now confirms modeled V6 table access. |
| Additional IAM role | newly observed | ✅ VERIFIED JakobLambdaExecutionRole has broad jakob-* table/index and bucket-prefix permissions; no evidence it was created since PR #5. Not a V6 deployment/execution role. |
| Buckets | unchanged + newly observed | ✅ VERIFIED jakob-asset-store and jakob-backup-vault east-1; dfss-jakob-anchors east-2 newly in scope. All versioning enabled. No bucket/object reuse authorized. |
| Quotas, identity, logs, stacks | newly observed | ✅ VERIFIED Lambda concurrency 10 in each region; no Cognito pools across enabled regions; no IAM OIDC providers; no stacks/metric alarms returned east-1/east-2; legacy log groups have no explicit retention. |
| Resource removals or changes | none found in comparable fields | ✅ VERIFIED common fields unchanged; this is not exhaustive drift detection. |
| PR #5 REST APIs, table resource policies; secret values; code bytes | 🐈📦 | 🐈📦 UNRESOLVED not rechecked/read in this narrower scope. No current absence or stability claim. |

## PR #9 compatibility matrix

| Candidate concern | Result | Evidence / next gate |
|---|---|---|
| Account/region | ⚠️ MIGRATION/DECISION REQUIRED | east-1/east-2 enabled, relevant services observed. Explicit account and region approval absent. Prefer a separate sandbox account for real isolation; no account created. |
| Names/coexistence | ✅ VERIFIED (scoped) | Illustrative stack `jel-v6-sandbox-20260925`: function/API `jel-v6-sandbox-20260925-v6`, table `jel-v6-jel-v6-sandbox-20260925-events`, log `/aws/lambda/jel-v6-sandbox-20260925-v6`. No collisions in observed east-1/east-2 inventories. Generated role name/alias sandbox scoped to new function. Not a global reservation; final names must be rechecked. |
| Python 3.13/x86_64 ZIP | ✅ VERIFIED documented support | [AWS runtime table](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html). No candidate executed; native-platform/runtime behavior remains 🐈📦. |
| ReservedConcurrentExecutions=2 | 🚫 BLOCKED | Both account settings and Service Quotas report total 10. AWS requires leaving 100 unreserved; template cannot satisfy this rule. Future approved quota ≥102 (assuming no other reservations), or separately reviewed concurrency redesign, needed. [Reservation rules](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html). No quota request made. |
| New PK/SK:S table | ✅ VERIFIED design fit | Separate on-demand table matches adapter key design and avoids all legacy key mismatches. No updates/deletes/scans/queries in V6 adapter. Real conditional-write concurrency/durability remains 🐈📦. |
| New HTTP API / JWT routes | ✅ VERIFIED documented feature, 🐈📦 enforcement | POST /v6/events; GET /v6/senders/{sender}/events/{event_id}; sandbox explicit deployment, JWT required. Existing HTTP APIs demonstrate service presence, not JWT verification. No IdP provisioned. |
| Claims/bindings | 🚫 BLOCKED | No configured provider; mandatory nbf and aud mismatch ordinary Cognito access-token profile. Packaged registry is empty/UNCONFIGURED and intentionally fails closed. See identity matrix. |
| V6 execution role | ✅ VERIFIED static scope | New dedicated role, exact new table PutItem/GetItem, specific log-stream CreateLogStream/PutLogEvents. No legacy role reuse. Effective authorization remains 🐈📦. |
| API → alias grant | ✅ VERIFIED static scope | Qualified sandbox alias, API/stage/method/path SourceArn and SourceAccount. No Function URL, ANY/default route or public permission. Does not deny same-account identity-policy invocation. |
| Direct invocation and isolation | 🚫 BLOCKED pending proof | See IAM assessment below; new resource policy alone cannot authenticate an event or exclude all bypass paths. |
| Quotas | ✅ VERIFIED metadata; 🐈📦 complete admission | Two regional concurrency limits are blocking. Returned DDB table limit 2,500, table read/write 40,000; HTTP routes 300/stages 10; CF stacks 2,000. One new table/API/two routes is small. Quota values are not current utilization or admission proof; API request-rate/account-specific limits and future account must be rechecked. |
| Logging/alarms | ⚠️ MIGRATION/DECISION REQUIRED | Candidate log group retention 30 days; Errors/Throttles alarms. No notification destination, API access logs or app-level rejection/503 metric. Caught HTTP 503 can leave Lambda Errors at zero. Define sanitized operational signals and response ownership before activation. |
| Artifact storage | 🚫 BLOCKED | Template requires external versioned S3 bucket/key/version/base64 SHA. Existing three buckets preserved. Approve NEW same-region private versioned artifact bucket, encryption/public-access controls, retention and tightly scoped deployment access. Global name availability unproved; no artifact access performed. |
| Deployment principal / PassRole | 🚫 BLOCKED | No dedicated approved deployer/service role established. Root audit identity is not the deployment plan. Need constrained CloudFormation trust, stack/resource permissions and iam:PassRole for exact new execution role to lambda.amazonaws.com (and CF service role to cloudformation.amazonaws.com where used). |
| Source/artifact lineage | ✅ VERIFIED historical offline candidate; 🐈📦 release | PR #9 records 177 offline tests, cfn-lint 1.40.2 and deterministic SHA `47b9def9dd4fa2579fbff4361a0d2fded1a03e72a057d809d0df2df235f95bdc`. Those are prior results, not rerun here or deployed evidence. Final approved bindings/provider/template require a NEW build and auditable release commit. |

## IAM and direct-invocation assessment

✅ VERIFIED: `SimulatePrincipalPolicy` on each of the two legacy execution roles, using a concrete hypothetical new V6 table ARN in east-1, returned allowed for GetItem/PutItem. No items were accessed. On the proposed alias ARN it returned implicitDeny for InvokeFunction (with unrelated missing context keys), and allowed for DeleteFunction. Simulation does not establish that an API accepts a particular qualified delete target, nor that a future resource policy permits it. It demonstrates broad control-plane permissions worthy of review, not an executed attack.

🚫 BLOCKED: same-account coexistence is mechanically possible without renaming legacy resources, but **security isolation is not established**. Existing wildcard table grants would reach the proposed table unless effective explicit-deny/resource/account controls change that result. The candidate table has no such isolation control. Prefer a separate approved sandbox account, preserving legacy infrastructure. A same-account design needs a separately reviewed new-resource policy and complete principal analysis; do not silently alter legacy roles.

🐈📦 UNRESOLVED: user/group policies, other session grants, future deployment roles and privileged administrators. The observed root principal is an administrative bypass capability; a statement that “only Gateway can invoke” needs a defined threat model excluding/controlling account administration. Alias ARN/API/stage checks in Python can be copied into a forged direct-invoke payload/context path; they are consistency checks, not cryptographic authentication. There is no resource-policy-only proof that direct invocation is denied. Same-account identity allows, unqualified/version/alias ARNs, Function URLs, event sources, role assumption/PassRole and code/config/policy modification paths must all be considered in the selected account. [IAM evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) and [Lambda permissions](https://docs.aws.amazon.com/lambda/latest/dg/permissions-function-services.html).

Future deployment permissions must cover only new stack resources: CF stack lifecycle; Lambda create/config/code/version/alias/permission operations; new-role creation/inline policy/PassRole; new table create/PITR/protection; API/routes/integrations/JWT/stage/deployment; new logs/alarms; exact versioned artifact read. Separate artifact publisher from runtime; runtime does not need S3 or IAM. Some create/list actions lack resource-level scoping: document each exception with account/region/name/tag/PassRole conditions rather than grant administrative wildcards. This paragraph is a requirements inventory, not a deployable IAM policy or authorization proof.

## Exact remaining blockers / exit evidence

1. Approve account/region and isolation threat model; choose separate account or reviewed new-resource controls. Repeat preflight there; deny unauthorized invocation/data access must be proven later under explicit test authorization.
2. Resolve reserved-concurrency quota conflict without affecting legacy availability; no automatic quota or template change in this PR.
3. Choose provider/flow and explicitly revise or satisfy mandatory claims; configure issuer/audience/client/scopes and approved versioned binding registry in a separate implementation review. No weakening happened here.
4. Approve scoped deployment/service role and PassRole, artifact bucket, immutable object version/hash, monitoring/retention/cost budget and final names.
5. Converge source/evidence per CONVERGENCE.md, rerun offline tests/lint/build, record final source and artifact hashes, freeze exact parameters/logical version/deployment IDs.
6. Obtain separate deployment authorization, then separately authorized negative JWT, direct-invoke, receipt/retry/concurrency/durability tests. This audit does not authorize those actions. Keep legacy intact and no caller cutover until verified.

Pattern ≠ fact. Reference ≠ execution. Architecture ≠ deployment. Convergence ≠ proof. Static validation ≠ effective AWS authorization proof.

## Offline validation of this audit

Run `python3 -m unittest discover -s audits/live-preflight-2026-09-25 -p 'test_*.py' -v` from the repository. Nine checks passed locally: executed-operation allowlist; no environment/secret-value fields; complete discovery ledger; real branch parents; simulation separation; 22-row delta; drift/missing-observation behavior; script syntax; credential/presigned-URL pattern scan. These validate audit consistency, not AWS service behavior. `compare.py <PR5-evidence.json> <current-evidence.json>` regenerates the common-field delta; PR #5's evidence must be obtained at its recorded head, not inferred from a newer branch. No runtime tests or CloudFormation deployment validation rerun for this docs-only change. Prior PR #9 validation is identified separately above.

## Resumption review and design alternatives

The local workspace survived the interrupted run, including all five evidence batches, scripts, draft documents and lineage. The workspace directory itself is not a Git checkout: local `git status` and branch inspection returned “not a git repository,” so these were uncommitted generated files, not a hidden activation branch. They are preserved. No repeat AWS inventory was needed to finish this dated snapshot.

Simulation precision: PR #5's historical simulator response contained a generic `${Region}/${Account}/${ResourcePath}` resource pattern and is not per-table proof. The saved September 25 batch5 response instead echoes the concrete **hypothetical** V6 resource names shown in this audit. Neither response proves effective access to a deployed table: the V6 table does not exist, future policies are absent, and simulation cannot close the real-account authorization model. Preserve the old placeholder limitation; do not retroactively upgrade PR #5 evidence.

| Alternative | Technical effect | Present configuration / decision |
|---|---|---|
| Remove positive reserved concurrency in a later candidate | Uses shared unreserved pool; avoids this specific reservation admission constraint | ⚠️ MIGRATION/DECISION REQUIRED. Would share the quota of 10 with legacy runtime; Gateway throttles do not reserve capacity or guarantee cost/availability. No template edit here. |
| Obtain quota increase in chosen account | Quota ≥102 allows reservation 2 while leaving 100, provided other reservations do not consume the difference | ⚠️ MIGRATION/DECISION REQUIRED. Approval/timing not guaranteed; no request made. Recheck actual settings before any later deployment. |
| Clean up legacy IAM wildcard grants | Removes existing broad identity allows if every relevant policy is addressed | ⚠️ MIGRATION/DECISION REQUIRED, outside preservation scope. Requires legacy dependency analysis and separate change authorization; not performed. |
| Explicit deny on NEW V6 DynamoDB resource policy | Can override same-account identity allows for unwanted principals/actions; a narrow Allow alone cannot | ⚠️ MIGRATION/DECISION REQUIRED. Candidate has no resource policy. Review exact principal ARN conditions, authorized runtime/deployer/recovery exceptions, table/index scope and policy-modification bypass. Avoid NotPrincipal+Deny boundary traps. No proposed policy is treated as verified. |
| Permission boundaries / SCP controls | Boundaries constrain attached identities; SCPs constrain covered member-account principals | ⚠️ MIGRATION/DECISION REQUIRED. A boundary on only the NEW role does not constrain OLD roles. None observed on seven roles; account not in Organizations. Requires separately authorized governance changes; resource/session grant exceptions and administrative control matter. |
| Separate sandbox account | Avoids same-account legacy identity grants automatically carrying into V6 without cross-account trust | Recommended design direction, 🐈📦 UNRESOLVED approval/configuration. Still requires constrained admins/deployer, no legacy trust grants, JWT bypass tests, fresh quotas and billing review. Not a proof or account-creation authorization. |

[DynamoDB resource-policy behavior](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/rbac-best-practices.html) explains why identity allows still apply without a table policy. [Boundary evaluation and explicit-deny cautions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html) distinguish role/session permissions and recommend principal-ARN conditions rather than NotPrincipal deny for bounded identities. These are design capabilities, not configured controls in this candidate.
