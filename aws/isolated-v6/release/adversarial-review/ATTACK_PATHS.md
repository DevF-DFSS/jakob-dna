# Attack-path review

Review target PR17 `a272b929e16b1db3e92eee5c3a1fe66c30d86d91`; reviewed 2026-09-26. No path is labelled PROVEN_PATH because no exploit/service execution was attempted. STATICALLY_BLOCKED means the modeled unchanged code/policy blocks that isolated path, not proof of AWS effective enforcement. IAM_SIMULATION is never OBSERVED_LIVE_BEHAVIOR. Source IDs resolve in [sources.json](sources.json); exact live requests/results are in [aws-evidence.json](aws-evidence.json). A/B/C/D are primary buckets defined in [BLOCKER_CLASSIFICATION.md](BLOCKER_CLASSIFICATION.md). Multiple paths can share one blocker.

## P01 — Direct unqualified / $LATEST invocation

**STATICALLY_BLOCKED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

claims.py requires actual invoked_function_arn equal to sandbox alias; FunctionResourcePolicy also denies non-Gateway InvokeFunction across function and :*. AWS Lambda supplies context (source lambda_context).

Limit: This rejects in the unchanged handler even if IAM admitted the call. It does not stop code/config/policy replacement, and AWS policy enforcement is not observed. Current empty registry fails startup earlier.

Next design/test: Retain alias check; negative invoke test only after separate authorization.

## P02 — Direct sandbox alias with forged Gateway-shaped event

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

PR17 identity simulation allows alias invoke; payload authorizer/apiId/stage can be fabricated. Invoking the real alias naturally gives the correct AWS-created context ARN. Full policy intends an explicit Deny.

Limit: No live bypass. Needs missing/removed/mis-evaluated policy; attacker cannot set the actual Lambda context object merely via Invoke payload.

Next design/test: Close management and creation-window paths; then test alias negative invocation.

## P03 — Direct published version invocation

**STATICALLY_BLOCKED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

Actual version ARN differs from configured alias; same local check plus full-policy :* Deny.

Limit: Version-specific AWS evaluation still requires a sandbox. PR17 multi-resource simulation was not per-version proof.

Next design/test: Retain checks and test numeric version separately.

## P04 — Create/use Function URL

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

No URL in candidate; current legacy lambda:* includes URL management. Non-Gateway InvokeFunctionUrl Deny intends to block use.

Limit: Creating a URL alone does not defeat the local JWT/alias checks or explicit invoke Deny. It is a control-plane/exposure path combined with policy/code changes, not standalone proven auth bypass.

Next design/test: Cover URL management in pre-existing namespace containment; test absence/negative access later.

## P05 — Put/DeleteResourcePolicy or AddPermission/RemovePermission

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

Current AWSLambda_FullAccess v7 lambda:*; PR17 simulations and AWS Lambda supported resource-policy list exclude protection of these management actions.

Limit: No future policy exists; Add/RemovePermission alone are not claimed to remove all Deny statements. Put/Delete provide the credible replacement/removal path.

Next design/test: Separately approved identity-side management fence; do not rely only on Lambda resource policy.

## P06 — Code / configuration replacement

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

UpdateFunctionConfiguration is outside the documented Lambda resource-policy list. UpdateFunctionCode/PublishVersion/alias changes are within it, but P05 can remove that protection.

Limit: Configuration changes normally affect $LATEST, not an already published immutable alias target. Config-only mutation is not claimed to rewrite the existing version.

Next design/test: Review full chained control-plane authority, including layers/handlers and code publication.

## P07 — Pass V6 runtime role to an attacker-controlled different Lambda

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

PR18 simulation with iam:PassedToService=lambda.amazonaws.com allows PassRole to hypothetical V6 execution-role ARN; CreateFunction/UpdateConfiguration/Invoke on a different hypothetical function allowed. ExecutionRole trusts Lambda service. RuntimeBoundary and table allow that role GetItem/PutItem without source-function binding; legacy Deny sees role ARN, not originating user.

Limit: New role/function do not exist. No role was passed, no token/credential obtained, no invocation/data read occurred. Simulation does not evaluate future role trust or table policy. Supported chain inference, not observed exploitation.

Next design/test: Next authority-remediation PR must address passing/attaching V6 roles outside their intended function, not just deny actions on the V6 function ARN. Evaluate exact PassRole denial and documented source-function identity restriction; no policy change here.

## P08 — Gateway route/authorizer/integration replacement

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, IAM_SIMULATION, AWS_LIVE_READ_ONLY

Current AmazonAPIGatewayAdministrator attachment and PR18 hypothetical route PATCH/POST identity simulations allow management. Lambda SourceArn constrains API/stage/path, not authorizer settings or integration integrity.

Limit: Setting auth NONE alone removes claims and V6 fails closed. Redirecting to attacker integration could intercept bearer/payload traffic or deny service; composite compromise is plausible, not exercised. POST simulation is identity evidence, not proof that every modeled resource supports that API operation.

Next design/test: Fence candidate API control-plane authority and verify post-deploy route/integration metadata before any real token.

## P09 — Runtime role edits IAM/policies/boundaries or legacy resources

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

RuntimeBoundary explicit NotAction and NotResource Denies; runtime identity only GetItem/PutItem and logs; tests cover broader synthetic session Allow.

Limit: Boundary does not restrict allowed table calls to conditional PutItem or this particular function. P07 remains. AWS effective policy untested.

Next design/test: Retain boundary; do not call it a role-use restriction.

## P10 — Deployment role changes bootstrap boundaries or legacy resources

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

DeploymentBoundary explicit outside-action/resource Denies exclude boundary mutation, STS assume, legacy function/table/API ARNs and PassRole to other roles/services.

Limit: Depends on attached boundary remaining in place; root/bootstrap authority can replace it. IAM provider lifecycle dependencies are not all exercised.

Next design/test: Review resulting policies and lifecycle behavior in sandbox; no broad permission expansion now.

## P11 — Recovery/stack operator reuses CloudFormation service role to change protections

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

recovery-operator.json grants runtime UpdateStack and ContinueUpdateRollback with exact RoleArn; DeploymentRole can replace V6 code/resource policy and execution-role inline policy. AWS documents reuse of associated service role by other stack operators even without PassRole.

Limit: No role or stack exists. No evidence that the present legacy user has UpdateStack. A future approved recovery session is deliberately privileged, not cryptographically bound to a reviewed template by IAM.

Next design/test: Restrict all stack mutators, authenticate phase-scoped human approval and exact template/parameter set; two-person temporary emergency authority.

## P12 — Publisher becomes deployment/recovery principal

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

PublisherBoundary explicitly denies actions outside four S3 actions and other resources; deployment trust is CloudFormation-only.

Limit: Recovery must separately be granted sts:AssumeRole to publish; normal recovery proposal lacks it. Publisher trust alone does not grant that path through its proposed maximum boundary.

Next design/test: Specify narrow temporary publishing/bootstrap authority before use; no standing escalation.

## P13 — Legacy user directly assumes proposed service roles

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

ExecutionRole and DeploymentRole trust only lambda.amazonaws.com and cloudformation.amazonaws.com respectively. Ordinary user AssumeRole does not satisfy those trusts.

Limit: Does not block passing the execution role to Lambda (P07) or operating a CF stack (P11). Trust and IAM identity grants are distinct.

Next design/test: Retain service trust; inspect role-use paths separately.

## P14 — Function/bucket creation before resource-policy attachment

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

FunctionResourcePolicy depends on Function/Alias; Stage depends on policy. Bucket precedes BucketPolicy. No atomic attachment guarantee; existing identity grants may act in the interval.

Limit: Stage ordering blocks premature Gateway exposure, not IAM access. Empty bindings block current ingest but are not a durable fence once configured.

Next design/test: Install independently enforced legacy/role-use containment before creation; keep initial experiment non-sensitive and ingress closed.

## P15 — Rollback/delete removes policy while protected resource remains

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

Function policy has no Retain; function deletion is separate. Stage dependency helps reverse-order removal but cannot prove no partial failure. Bucket/policy/table retention preserves resources, not complete operability.

Limit: No rollback run; retained policies and resources may outlive roles/stacks. CF automatic rollback is not a complete recovery procedure.

Next design/test: Preapprove bounded quarantine/repair/retention path independent of vulnerable policy; exercise rollback only in authorized sandbox.

## P16 — ResourcePolicy delete-handler DescribeStacks failure

**UNVERIFIED** · bucket B · HISTORICAL_LIVE_EVIDENCE, LOCAL_STATIC_ANALYSIS, INFERRED

PR15 registry delete permissions and PR16 analysis: DeploymentRole boundary denies DescribeStacks; actual provider call/target/context unknown.

Limit: Not a proven creation failure or universal delete failure. Requiring an observed delete before initial creation would be circular.

Next design/test: Carry unchanged PR16 question into bounded lifecycle test with trace and approved contingency; no speculative grant.

## P17 — Provider claim profile/projection does not fit V6

**REQUIRES_LIVE_SANDBOX_TEST** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

Gateway supports aud-or-client_id and scope-or-scp; claims.py requires aud AND client_id, token_use=access, only string-valued claims, scope string matching scopes list, numeric-string times. No provider chosen.

Limit: Failures normally deny access, not grant it. Default Cognito access tokens may lack aud; resource binding and custom scopes require provider/flow decisions. No promise that optional arrays/objects or default extra scopes fit.

Next design/test: Choose explicit provider profile and test projection/negative cases before opening ingress. Bootstrap alone needs no IdP.

## P18 — Valid signature but wrong issuer/audience/client/subject/token-use/scope/time

**STATICALLY_BLOCKED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, LOCAL_TEST

Gateway configured checks plus local exact comparisons, exp/iat and present nbf checks, operation scope and Registry authorize. Existing offline tests cover negative claims/bindings.

Limit: Local test fixtures assume trustworthy projected strings and IAM origin. No local JWT signature verifier. Real cryptography/key rotation is B.

Next design/test: Preserve strict rejection; provider compatibility must be explicit.

## P19 — Revoked/stale binding remains in warm host or old alias version

**PLAUSIBLE_PATH** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

activation._host caches fixed packaged registry; Registry.revoke exists only as local method and no deployed revocation endpoint; published configuration/code immutable until new version.

Limit: No claim of distributed immediate revocation exists. Unexpired tokens and already-authorized operations may outlive a human revocation decision.

Next design/test: Sandbox test registry/version rollout and documented stop method; production revocation SLO/session policy is separate.

## P20 — Synthetic evidence or approval string grants deployment

**STATICALLY_BLOCKED** · bucket A · LOCAL_STATIC_ANALYSIS, LOCAL_TEST

authorization_gate requires externally trusted verified_digests; CLI never has verifier and always exits 1; every output deployment_authorized=false.

Limit: A library caller can supply digests; this is an explicit trust assumption, not evidence authentication. No executor exists. Current design cannot authorize itself and must not be bypassed informally.

Next design/test: Design phase-specific authenticated review procedure before execution, without treating generic CI green as authority.

## P21 — CI green / local tests promoted into AWS proof

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, GITHUB_CI_EXECUTION

ci_evidence outputs deployment_authorized=false; workflow has contents:read, no AWS secrets/OIDC, pinned exact head/actions/dependencies.

Limit: Runner executes candidate-controlled tests, so independent execution is not independent security verification. PR13 gate accepts LOCAL_EXECUTION, not GitHub directly.

Next design/test: Keep source classes; independent reviewer evaluates findings.

## P22 — Release passes hashes but deployment parameters/exports differ

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS

release_manifest v1 lacks bootstrap parameter/export/role mapping; PR13 context hashes bootstrap but does not validate actual stack parameters, role associations or S3/version linkage. PR12 already calls this incomplete.

Limit: No executor or current approved record exists, so no current release bypass. A future manual deploy treating manifest as sufficient could target mismatched stack/context.

Next design/test: Versioned phase release record binds both templates, roles, stack names, parameters, exports and artifact version; exact drift check.

## P23 — Config/route update leaves old Lambda version or API deployment active

**PLAUSIBLE_PATH** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

CandidateVersion uses code hash and fixed description; changing only issuer/client environment changes no Version property. CandidateDeployment has fixed ApiId/Description and AutoDeploy=false. AWS defines immutable version and deployment snapshot.

Limit: Initial-create failure is not implied. Current resources do not exist. Code-hash changes can replace Version; DependsOn is ordering, not an automatic deployment revision.

Next design/test: Future update/revocation PR must bind snapshots to all relevant config; test transitions with synthetic identities before opening ingress.

## P24 — Publisher overwrites an already selected artifact version

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

S3 versioning; runtime pins S3ObjectVersion and Version.CodeSha256; publisher boundary denies delete and bucket-policy change.

Limit: Publisher can add malicious new versions. Approved deployer selecting a new version is trusted release authority; bytes are not independently signed by current tooling.

Next design/test: Bind exact version/hash to phase authorization; verify service retrieval in sandbox.

## P25 — Forged event/header sets AWS service principal or SourceArn

**STATICALLY_BLOCKED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

IAM service principal/SourceArn come from AWS request context, not event JSON. Candidate denies non-Gateway context and limits exact source account/API/stage/routes.

Limit: An attacker with allowed alias invoke can forge authorizer event values (P02); they need not forge IAM context if policy is absent. Actual Gateway service context remains untested.

Next design/test: Test actual source-context propagation without conflating IAM context and event fields.

## P26 — Legacy direct table/index access despite resource-policy Deny

**STATICALLY_BLOCKED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, LOCAL_TEST

Table policy explicit dynamodb:* Deny for known legacy role/user ARNs; finite tests include table/index. Explicit Deny overrides broad identity Allow when valid and applicable.

Limit: Blacklist does not cover unrelated/future roles; P07 uses an allowed role. No actual table/enforcement exists.

Next design/test: Refresh principal/role-use graph and test real negative access on synthetic sandbox data after authorization.

## P27 — Root/admin replaces controls

**OUT_OF_SCOPE_ADMIN_OVERRIDE** · bucket D · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION, HISTORICAL_LIVE_EVIDENCE

Same-account threat model explicitly excludes root or sufficient administrators. Connector caller is root for read-only metadata.

Limit: This is a stated trust limit, not a deployable normal operator path. Acknowledgment does not approve root writes.

Next design/test: Approve human governance and non-root ordinary path; separate account may later reduce blast radius.

## P28 — PR16 cited run silently treated as final-head evidence

**PLAUSIBLE_PATH** · bucket D · GITHUB_CI_EXECUTION, LOCAL_STATIC_ANALYSIS

GitHub run 36252559383 headSha is 8be77e681ceff13ac8feb19139a358d644547ebc, while PR16 body calls it final dd0df665... evidence; explains 64 versus 65 inputs. PR17 run 36255623584 matches final a272b929... and 72 inputs.

Limit: Metadata mismatch is verified, not an observed authorization bypass. New exact-commit PR18 execution supersedes inherited execution claims only for tested artifacts.

Next design/test: Record discrepancy here, keep historical PR untouched, reconcile every new final head/run.

## P29 — S3 service artifact retrieval blocked by bucket deny

**UNVERIFIED** · bucket B · LOCAL_STATIC_ANALYSIS, AWS_DOCUMENTATION

DenyOtherPrincipals only excepts approved recovery/publisher/deployment role ARNs; service delivery may have different principal context. CF deployment role GetObjectVersion is modeled.

Limit: No current AWS retrieval trace. Neither success nor certain failure is established. Current bucket is absent.

Next design/test: Test versioned artifact retrieval in first controlled lifecycle; inspect context before any policy widening.

## P30 — Recovery role trust/bootstrap/emergency authority absent or overbroad

**UNVERIFIED** · bucket A · LOCAL_STATIC_ANALYSIS, HISTORICAL_LIVE_EVIDENCE

recovery-operator.json trusted_federated_principal/account/region null; normal policy lacks initial CreateStack/bootstrap IAM/S3 repair. Boundary described but not rendered. No role in PR17 inventory.

Limit: Naming a recovery role does not make it usable. Temporary authority cannot be assumed. Creating an initial non-root authority requires separate human authorization.

Next design/test: Define and independently authorize exact temporary bootstrap/publish/repair path, trust, max boundary, duration and removal; no standing admin grant.

## P31 — Receipt/default-route parsing or sender spoofing bypass

**STATICALLY_BLOCKED** · bucket D · LOCAL_STATIC_ANALYSIS, LOCAL_TEST

Two JWT routes, strict HTTP parser and per-operation scope, server-owned principal binding; no default/ANY. Hash integrity remains distinct from identity auth.

Limit: Synthetic tests prove local behavior only. SHA-256 is unkeyed consistency, not proof of sender identity; authorized compromised principals remain within their granted bindings.

Next design/test: Retain local boundaries; real gateway tests remain B, production abuse controls C.

## P32 — 24-hour evidence label outlives a policy/context change

**PLAUSIBLE_PATH** · bucket A · LOCAL_STATIC_ANALYSIS

PR13 checks age/context equality but cannot detect external policy changes; policy hashes are not context fields and trusted verified_digests are external.

Limit: Freshness is not guaranteed for 24 hours; the clock limit is a rejection cap, not a lease.

Next design/test: Immediate pre-operation reread/diff and invalidate on trust/policy/role/artifact change as part of phase authorization.

Candidate behavior changed: NO. `deployment_authorized=false`.
