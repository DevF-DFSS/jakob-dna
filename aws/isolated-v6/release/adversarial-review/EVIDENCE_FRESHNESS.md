# Evidence freshness and provenance — PR18

Evidence is valid for its observation and coordinate, not a lease over mutable AWS state. No arbitrary new expiry time is invented. PR13’s 24-hour rejection cap does not guarantee policies stay unchanged for 24 hours. `expected_until=null` in sources.json means no guaranteed lifetime. Classification reconstruction occurred 2026-09-26; it does not refresh AWS observations.

## Interruption and CI correction

See [INTERRUPTION_RECOVERY.md](INTERRUPTION_RECOVERY.md). GitHub run **36252559383** executed **8be77e681ceff13ac8feb19139a358d644547ebc**. The PR16 body’s final-head citation is stale. Run **36252726480** executed **dd0df665ea4bd7512e18597001def8bb798e83e5**, so final PR16 execution exists. Both have conclusion failure. Actual workflow `head_sha` outranks prose; no historical PR was edited. Final PR18 metadata/logs must be independently reconciled after publication.

## Evidence families

Account context for AWS records is `083127296577`, not an approved deployment account. PR18 live/simulation times are one recorded batch-start timestamp; individual per-call timestamps were not captured and are not invented. Public source hashes/URLs/timestamps and the following structured fields are in [sources.json](sources.json).

### caller

- **source:** aws-evidence.json, STS GetCallerIdentity
- **evidence class:** AWS_LIVE_READ_ONLY
- **observed at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **commit coordinate:** e12753aa5103c9020cdfa99be6b51c548faedfca
- **account:** 083127296577
- **region:** global identity; request batch context us-east-1
- **last verified at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** New session/identity/account or changed connector
- **refresh requirement:** Immediately before every approved write phase; record actual acting session
- **limits:** Root was used only for reads; not an approved operator.

### legacy_user

- **source:** aws-evidence.json GetUser/ListAttachedUserPolicies/GetPolicy/GetPolicyVersion
- **evidence class:** AWS_LIVE_READ_ONLY
- **observed at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **commit coordinate:** e12753aa5103c9020cdfa99be6b51c548faedfca
- **account:** 083127296577
- **region:** IAM global
- **last verified at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Attachment/inline/boundary/trust/group/policy version or principal change
- **refresh requirement:** Immediately before authority/bootstrap approval and after any policy change
- **limits:** Targeted user refresh only; three attachments/no boundary; broad inventory inherited, not refreshed.

### roles_boundaries

- **source:** ../auth-containment-preflight/LIVE_EVIDENCE.md
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T16:14:39Z–16:15:39Z
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** IAM global
- **last verified at:** 2026-09-26T16:14:39Z–16:15:39Z
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** New role/user/service-linked role; trust/policy/boundary changes
- **refresh requirement:** Current complete relevant principal/role-use graph before authority approval
- **limits:** Four service-linked roles are distinct; ordinary role counts are historical, not a guarantee against later actors.

### organizations_sessions

- **source:** ../auth-containment-preflight/LIVE_EVIDENCE.md
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T16:17:39Z
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** global organization context
- **last verified at:** 2026-09-26T16:17:39Z
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Organization membership/SCP change, session policy or principal change
- **refresh requirement:** Before authority approval; inspect applicable constraints and actual session provenance
- **limits:** AWSOrganizationsNotInUseException then; no present organization/SCP proof. Session policies not exhaustively established.

### simulation

- **source:** aws-evidence.json four SimulatePrincipalPolicy requests/results
- **evidence class:** IAM_SIMULATION
- **observed at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **commit coordinate:** e12753aa5103c9020cdfa99be6b51c548faedfca
- **account:** 083127296577
- **region:** us-east-1 hypothetical resources; IAM global roles
- **last verified at:** 2026-09-26T16:54:35.854752+00:00 (batch start)
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Any input policy/ARN/action/context/trust/organization/session change
- **refresh requirement:** Repeat exact actual candidate ARN/context simulations before applicable phase; supplement with separately authorized sandbox negatives
- **limits:** No future trust/resource policy/live call is tested. CF-context implicitDeny has MissingContextValues; Gateway POST simulation is not proof of API operation validity.

### gateway

- **source:** ../auth-containment-preflight/LIVE_EVIDENCE.md
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T16:14:39Z–16:15:39Z
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** us-east-1, us-east-2
- **last verified at:** 2026-09-26T16:14:39Z–16:15:39Z
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** API/route/authorizer/integration/stage/deployment or administrative-grant change
- **refresh requirement:** Before bootstrap namespace selection, then after creation and immediately before test ingress
- **limits:** Three legacy HTTP APIs, no authorizers then; no V6 API. PR18 targeted admin simulation is separate from API inventory.

### lambda

- **source:** ../auth-containment-preflight/LIVE_EVIDENCE.md
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T16:14:39Z
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** us-east-1, us-east-2
- **last verified at:** 2026-09-26T16:14:39Z
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Function/alias/version/URL/role/config/policy change
- **refresh requirement:** Before namespace approval and after each candidate lifecycle transition
- **limits:** No V6 function observed in sampled regions then; no global absence proof.

### provider

- **source:** ../auth-containment-preflight/LIVE_EVIDENCE.md and CONTRACT.md
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T16:14:39Z
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** us-east-1, us-east-2
- **last verified at:** 2026-09-26T16:14:39Z
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** IdP/client/issuer/keys/scopes/subjects/flow or config change
- **refresh requirement:** Provider selection/approval before real parameters or ingress; actual projection after controlled test authorization
- **limits:** No Cognito pools sampled; external providers not globally inventoried. No tokens generated; provider capability differs from configured behavior.

### registry

- **source:** ../schema-research/registry.json and sources.json; ../describestacks-authority/EVIDENCE.md and sources.json
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** 2026-09-26T13:45:29.451620+00:00 (PR15 registry batch)
- **commit coordinate:** a9de8ce6a646520ad1548b86bd97af9669c5ab27 / dd0df665ea4bd7512e18597001def8bb798e83e5
- **account:** 083127296577
- **region:** us-east-1, us-east-2, eu-west-1 (PR15 sample)
- **last verified at:** 2026-09-26T13:45:29.451620+00:00 (PR15 registry batch)
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Regional type/default version/handler schema/catalog change
- **refresh requirement:** Before selecting actual deployment region and approving template/lifecycle test
- **limits:** No new DescribeType in PR18. ResourceArn evidence does not prove delete-handler requests or permissions.

### recovery

- **source:** ../authorization/recovery-operator.json + PR17 inventory
- **evidence class:** LOCAL_STATIC_ANALYSIS
- **observed at:** 2026-09-26 review; absence inherited from PR17
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** proposed account/region unconfigured
- **last verified at:** 2026-09-26 review; absence inherited from PR17
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Trust/operator/role/grants/session/stack association/emergency plan change
- **refresh requirement:** Before bootstrap, before recovery and after temporary rights expire or are removed
- **limits:** JSON is unconfigured; no usable actor or recovery drill. Read-only connector root is not the recovery path.

### ci

- **source:** sources.json github_workflow_runs; final PR18 PR body/run object
- **evidence class:** GITHUB_CI_EXECUTION
- **observed at:** 2026-09-26T20:26:14Z (PR16 metadata retrieval)
- **commit coordinate:** Actual run head_sha, never PR-body prose
- **account:** Not applicable / no guaranteed expiry
- **region:** Not applicable / no guaranteed expiry
- **last verified at:** 2026-09-26T20:26:14Z (PR16 metadata retrieval)
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Source/dependency/workflow/runner changes or superseded run
- **refresh requirement:** For every final release commit, compare actual run head_sha and check logs/source-input hashes
- **limits:** PR16 run36252726480 exists at final dd0df665; run36252559383 is historical. Failure remains failure. PR18 final evidence pending validation at this checkpoint.

### hashes

- **source:** Git tree + unchanged build.py source_inputs + final diagnostic provenance
- **evidence class:** LOCAL_STATIC_ANALYSIS
- **observed at:** Final validation pending at classification checkpoint
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** Not applicable / no guaranteed expiry
- **region:** Not applicable / no guaranteed expiry
- **last verified at:** Final validation pending at classification checkpoint
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Any source/template/bootstrap/binding/dependency/selected artifact version/parameter change
- **refresh requirement:** Recompute and verify against exact final Git tree; bind actual deployment parameters/exports separately
- **limits:** Hash identifies bytes, not authority; final PR18 result recorded after commit in validation logs and PR body to avoid a self-hash cycle.

### human_authorization

- **source:** ../authorization/current.json; explicit DevF decision absent
- **evidence class:** UNVERIFIED
- **observed at:** 2026-09-26 review
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** Not applicable / no guaranteed expiry
- **region:** Not applicable / no guaranteed expiry
- **last verified at:** 2026-09-26 review
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** No authority yet; future decision expires on changed scope/context or its stated end
- **refresh requirement:** Require authenticated explicit phase-specific consent immediately before named mutation; stop on drift
- **limits:** deployment_authorized=false; tests/checkpoints/CI never supply consent.

### public_documentation

- **source:** sources.json sources; 19 hashed public sources
- **evidence class:** AWS_DOCUMENTATION
- **observed at:** 2026-09-26T16:59:42.749188+00:00–16:59:51.665931+00:00
- **commit coordinate:** Not applicable / no guaranteed expiry
- **account:** Not applicable / no guaranteed expiry
- **region:** Not applicable / no guaranteed expiry
- **last verified at:** 2026-09-26T16:59:42.749188+00:00–16:59:51.665931+00:00
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** AWS docs/catalog/service behavior update
- **refresh requirement:** Recheck substantive claims when choosing final design/provider/region or contrary evidence appears
- **limits:** Documentation is not observed service behavior. Raw downloads cached outside Git; hashes and URLs persist.

### quota_cost

- **source:** PR10 preflight and candidate throttling/log/retention configuration
- **evidence class:** HISTORICAL_LIVE_EVIDENCE
- **observed at:** Historical PR10 observation; not refreshed in PR18
- **commit coordinate:** a272b929e16b1db3e92eee5c3a1fe66c30d86d91
- **account:** 083127296577
- **region:** candidate region not yet approved
- **last verified at:** Historical PR10 observation; not refreshed in PR18
- **valid at:** Observation/context only; not an authority lease
- **expected until:** Not applicable / no guaranteed expiry
- **invalidated by:** Quota/pricing/free-tier/account usage/retention/volume changes
- **refresh requirement:** Before bounded experiment authorization; observe actual spend/volume during it
- **limits:** No $0 promise and no quota/billing calls in PR18.

## Read-only AWS ledger

PR18 cumulative: **9 attempted / 9 successful / 0 failed**; resumed recovery/classification adds **zero**. Exact requests/results are preserved in [aws-evidence.json](aws-evidence.json). Broader PR17 42/41/1 is inherited historical evidence and is not counted again. Public AWS documentation and GitHub reads are not authenticated AWS API calls.

| # | API | Purpose/result |
|---|---|---|
| 1 | STS GetCallerIdentity | Root/account metadata, reads only |
| 2 | IAM GetUser | us-os-gateway; no boundary returned |
| 3 | IAM ListAttachedUserPolicies | Three attachments |
| 4 | IAM GetPolicy | AWSLambda_FullAccess default v7 |
| 5 | IAM GetPolicyVersion | v7 document |
| 6 | IAM SimulatePrincipalPolicy | Lambda-service PassRole on hypothetical V6 role: allowed |
| 7 | IAM SimulatePrincipalPolicy | CloudFormation-service PassRole: implicitDeny; missing context limitation |
| 8 | IAM SimulatePrincipalPolicy | Hypothetical alternate-function Create/UpdateConfiguration/Invoke: allowed |
| 9 | IAM SimulatePrincipalPolicy | Hypothetical API route PATCH/POST: allowed; identity evaluation, not API validity/execution |

All simulations use us-os-gateway as PolicySourceArn. They do not model a real future resource, its trust/resource policy, every session/SCP path or a successful exploit. No Lambda was created/invoked, role passed, token issued or table accessed.

## Thirty-one enforcement rows versus thirty-two paths

PR17 matrix has 31 rows with control names, not stable row IDs. The mapping below uses **1-based ordinals bound to exact PR17 commit a272b929** and names. It expresses related analysis, not identity. P14/P24/P29 introduce creation/artifact questions beyond those row labels; paths can map to multiple controls.

| PR17 row / control | Related PR18 paths |
|---|---|
| 1 — JWT signature and RSA JWKS | P17, P18 |
| 2 — issuer iss | P17, P18 |
| 3 — audience aud | P17, P18 |
| 4 — client_id | P17, P18 |
| 5 — subject sub | P17, P18, P31 |
| 6 — access token use | P17, P18 |
| 7 — route scopes | P08, P17, P18 |
| 8 — scope projection | P17, P18 |
| 9 — expiration exp | P17, P18 |
| 10 — issued-at iat | P17, P18 |
| 11 — not-before nbf | P17, P18 |
| 12 — JWT event claim shape | P02, P17, P25 |
| 13 — API ID | P02, P08, P25 |
| 14 — stage | P08, P23, P25 |
| 15 — route/method/path | P08, P23, P31 |
| 16 — qualified alias | P01, P02, P03, P23 |
| 17 — Gateway source account | P25 |
| 18 — Gateway source ARN | P08, P25 |
| 19 — unqualified direct InvokeFunction | P01 |
| 20 — published-version direct InvokeFunction | P03 |
| 21 — alias direct InvokeFunction | P02 |
| 22 — Function URL | P04 |
| 23 — code/config mutation | P06 |
| 24 — resource-policy mutation | P05 |
| 25 — PassRole | P07, P13 |
| 26 — deployment-role use | P10, P11 |
| 27 — known legacy principal access | P05, P07, P08, P26 |
| 28 — recovery path | P11, P15, P16, P30 |
| 29 — tenant/sender/receiver binding | P18, P19, P31 |
| 30 — root/administrator override | P27 |
| 31 — deployment approval | P20, P21, P22, P28, P32 |

Row16’s phrase “context can be forged by direct invoker” is narrowed here: event fields are forgeable; the actual Lambda context ARN is supplied by AWS. Direct alias invocation naturally has the expected ARN. Row25’s no-context PassRole simulation is supplemented, not overwritten, by PR18’s Lambda-context allowed result. These corrections do not edit PR17.

## Immediate pre-authorization refresh set

Read actual caller/session, all relevant identity grants/boundaries/trust and policy versions, applicable organization/session constraints, exact names/role associations and API/provider state for the next phase. Re-evaluate role-use and stack-operator paths, verify unchanged source/parameters and current recovery authority, then obtain explicit phase consent. After each mutation in a future authorized run, read back configuration and stop on drift before the next phase. Refresh only relevant fields, preserving earlier snapshots as lineage.

Candidate behavior changed: NO. `deployment_authorized=false`.
