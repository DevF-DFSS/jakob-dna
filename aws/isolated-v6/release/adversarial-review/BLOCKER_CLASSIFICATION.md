# Final blocker classification — PR18

Reviewed candidate: `a272b929e16b1db3e92eee5c3a1fe66c30d86d91`. Evidence/review only. `deployment_authorized=false`.

## Units and reduction

The interrupted checkpoint contained 32 paths with preliminary A/B/C/D tags **13/10/0/9**. Their substance and tags are preserved (full enum names now used in JSON). Path counts are not blocker counts. The final issue register has **15 groups: A=3, B=6, C=3, D=3**. Every group has exactly one primary bucket, explicit phase effects and closure evidence in [blockers.json](blockers.json). A path can inform several distinct lifecycle issues without becoming several prerequisite gates. Production groups are prospective requirements, not newly discovered exploits.

The provisional three-gate model survives because the three properties are independently necessary: A1 constrains untrusted authority; A2 bounds and makes usable the trusted operator; A3 binds that authority to exact phase-specific actions and evidence. None substitutes for another. Substeps are not hidden PASS assumptions. **No gate is presently closed.** Gateway administration, function management and role reuse are children of A1; separate source/context testing is B2.

## Minimum pre-deployment security properties

### A1 — Control who can alter or reuse V6 authority

Waiting for protected resources to exist would expose role-use and policy-attachment windows. This is one upstream authority property, not separate blockers for each API operation.

Required closure: Approve and independently evaluate a complete principal/action/resource/context graph, then separately authorize containment establishment and read-back before creating usable V6 roles/functions/data paths. Cover legacy management, PassRole/alternate Lambda, Gateway mutation, role/boundary replacement, stack operators and rollback windows. Generated API identifiers require an inert-create/inspect/fence hold before routes or traffic. No proposed control is installed in PR18.

Related paths: P02, P04, P05, P06, P07, P08, P11, P14, P15.

### A2 — Establish bounded, usable non-root bootstrap/deployment/recovery authority

Creating resources first and discovering nobody can contain or repair a failure is too late. A policy proposal is not an authenticated operator or usable recovery path.

Required closure: Name independently approved non-root trust/assurance and session limits; render exact normal maximum permissions and PassRole/stack relationships; separately approve temporary bootstrap/publishing/emergency powers, removal/expiry and a fallback for failed-create/retained resources. Confirm the actor can assume the required role and review effective grants before first candidate creation. Initial authority-establishment writes themselves require a separate explicit human-approved operation; this review does not authorize them.

Related paths: P11, P12, P15, P30.

### A3 — Freeze an exact phased release and authenticated evidence/approval procedure

A generic PASS or manifest hash cannot safely authorize unspecified parameters, mutable exports, actors or later phases. The procedure and bounded failure plan must exist before the first write; future observations need not already exist.

Required closure: Bind account/region, both template hashes, source/artifact/binding hashes, stack names/roles/parameters/exports, selected S3 version, tests and exact next allowed mutation set to independent review and explicit DevF consent. Define authenticated evidence acquisition, freshness/drift checks, cost/time/stop limits, lifecycle contingencies and expiry of approval. Formally resolve known validator findings without pretending lint passed. Approve provider/profile and binding before token-capable ingress, not before empty bootstrap. The current template does not itself implement all phase holds.

Related paths: P20, P22, P28, P32.

## Issue register

In the flags below, ingress means ordinary use. Separately authorized synthetic test traffic is the means to obtain B evidence, not a waiver for production or general use. A1/A2/A3 must first make that bounded experiment defensible.

| ID | Primary bucket | Issue | Blocks first creation / ordinary ingress / production |
|---|---|---|---|
| A1 | A_PRE_DEPLOYMENT_MUST_CLOSE | Control who can alter or reuse V6 authority | yes / yes / yes |
| A2 | A_PRE_DEPLOYMENT_MUST_CLOSE | Establish bounded, usable non-root bootstrap/deployment/recovery authority | yes / yes / yes |
| A3 | A_PRE_DEPLOYMENT_MUST_CLOSE | Freeze an exact phased release and authenticated evidence/approval procedure | yes / yes / yes |
| B1 | B_SANDBOX_TEST_REQUIRED | Real provider profile, JWT enforcement and claim projection | no / yes / yes |
| B2 | B_SANDBOX_TEST_REQUIRED | Effective invocation, data/resource fences and AWS service context | no / yes / yes |
| B3 | B_SANDBOX_TEST_REQUIRED | Initial provider lifecycle and selected artifact retrieval | no / yes / yes |
| B4 | B_SANDBOX_TEST_REQUIRED | Rollback/delete/retention and ResourcePolicy DescribeStacks lifecycle | no / yes / yes |
| B5 | B_SANDBOX_TEST_REQUIRED | Configuration snapshots and binding revocation transitions | no / yes / yes |
| B6 | B_SANDBOX_TEST_REQUIRED | Tiny sandbox operation, concurrency and cost stop signals | no / yes / yes |
| C1 | C_POST_SANDBOX_BEFORE_PRODUCTION | Production capacity, durability, backup and service objectives | no / no / yes |
| C2 | C_POST_SANDBOX_BEFORE_PRODUCTION | Production revocation, key/identity lifecycle and incident governance | no / no / yes |
| C3 | C_POST_SANDBOX_BEFORE_PRODUCTION | Production caller/data migration and administrative separation | no / no / yes |
| D1 | D_INFORMATIONAL_OR_ACCEPTED_LIMITATION | Root/admin and deliberately trusted release authority limits | no / no / no |
| D2 | D_INFORMATIONAL_OR_ACCEPTED_LIMITATION | Validator/catalog drift versus candidate validity | no / no / no |
| D3 | D_INFORMATIONAL_OR_ACCEPTED_LIMITATION | Evidence lineage and controls that survive the isolated attack | no / no / no |

### B1 — Real provider profile, JWT enforcement and claim projection

Signature rejection and Gateway projection require actual provider/Gateway execution. Demanding them before an empty API exists is circular. Provider selection/approval is an A3 pre-ingress requirement, not execution proof.

Close/test: After A gates and explicit test authorization, use only approved synthetic sandbox identities to test RSA/JWKS rotation, aud AND client_id, sub, token_use=access, exact scope/scopes shapes, exp/iat/optional nbf, extra claims and binding mismatch. Hold general ingress until positive/negative evidence is reviewed.

Limits: No provider approved; absence of sampled Cognito pools does not exclude external providers. All-string claims and scalar aud are provider-selectable constraints, not universal OIDC guarantees.

### B2 — Effective invocation, data/resource fences and AWS service context

Actual qualified-policy/source context and negative enforcement require real isolated resources. Safe tests depend on A1 independent authority containment and A2 recovery, not on prior proof of those exact future resource policies.

Close/test: Under separate test authority, verify metadata and negative unqualified/version/alias/URL invocations, exact Gateway sources, legacy table/index denials, role-use restrictions and allowed service path on synthetic data. Do not treat IAM simulation as execution. No test principal receives standing broad access merely to conduct the test.

Limits: Policy attachment/effective IAM/SCP/session behavior unobserved. Direct same-account access is not disproved by a narrow runtime role.

### B3 — Initial provider lifecycle and selected artifact retrieval

Successful resource creation and service retrieval of the selected S3 version cannot be observed without a bounded create attempt. A1/A2 must already cover partial creation and failure.

Close/test: During controlled creation, inspect ordering, resulting policies, service-role associations and exact object version/hash retrieval. If denied, preserve events, keep ingress closed and analyze actual principal/context before widening any permission.

Limits: S3 delivery service principal/context unknown. Static schema validation is not a live provider trace.

### B4 — Rollback/delete/retention and ResourcePolicy DescribeStacks lifecycle

Provider delete calls and recovery transitions need deployed resources. Requiring a successful delete before first create is circular. A2 still requires usable bounded contingency authority before attempting creation.

Close/test: Authorize a synthetic lifecycle drill with stop/quarantine plan, inspect stack events and actual exercising principal/request where available, test retained resource access and temporary-right removal. Carry PR16 DescribeStacks target/principal/request ambiguity unchanged; no speculative grant.

Limits: Declared delete-handler permission is not observed invocation. Actual delete target/principal and failure-state repair remain unknown. Passing a drill is required before expanding sandbox use beyond the bounded experiment, even though not before first creation.

### B5 — Configuration snapshots and binding revocation transitions

Static evidence already identifies fixed Version/Deployment properties. It is not an initial-create defect. Transition behavior must be corrected/tested before relying on an update or revocation, with ingress stopped if needed.

Close/test: Separate remediation should bind published Lambda/API snapshots to all material configuration changes. Test alias/version/route rollout, warm-host bindings and a bounded stop method using synthetic identities before ordinary ingress or any claimed revocation guarantee.

Limits: DependsOn is ordering, not snapshot republishing. Packaged registry changes alter artifact hash but do not provide instantaneous distributed revocation.

### B6 — Tiny sandbox operation, concurrency and cost stop signals

Actual latency, throttling, sanitized telemetry and spend depend on running the sandbox. A3 must already approve bounded volume/duration/stop rules; sustained production load proof is unnecessary for first creation.

Close/test: At minimal authorized volume, verify shared concurrency, throttling/503/rejection/not-found signals, logs contain no payload/claims and costs remain within human-approved limits. Stop on unexpected exposure, logging or spend; do not promise zero cost.

Limits: Quota/cost observations inherited from earlier preflight are not a present allowance. No load or billing test occurred in PR18.

### C1 — Production capacity, durability, backup and service objectives

A finite synthetic human sandbox can stop and retain evidence; production requires concurrency/durability/load/restore/SLO evidence beyond it.

Close/test: Before production, define data retention/backup/restore, capacity and failure budgets, run meaningful load/concurrency/durability/restore tests and approve recurring cost/operational ownership.

Limits: No production workload or SLO approved.

### C2 — Production revocation, key/identity lifecycle and incident governance

Sandbox can use a small synthetic identity set and a tested stop control; production needs defined distributed revocation/session/key compromise responses.

Close/test: Define revocation delay/SLO, JWKS rotation overlap and compromise response, subject/client lifecycle, auditing and incident ownership; verify beyond isolated synthetic cases.

Limits: No instantaneous revocation property is established.

### C3 — Production caller/data migration and administrative separation

Legacy migration is explicitly outside the isolated sandbox; production needs separately approved callers, data classification and rollback/account governance.

Close/test: Approve migration/data governance and stronger account/administrative separation as justified; preserve legacy evidence and obtain new production authorization.

Limits: No production migration authorized; second account not assumed.

### D1 — Root/admin and deliberately trusted release authority limits

Same-account policy cannot constrain an administrator able to replace it. Accepting that declared threat-model limit is distinct from accepting ordinary legacy bypasses.

Close/test: Keep explicit human governance and non-root normal workflow; assess stronger separation for production. Never treat this limit as permission for root writes or standing recovery admin.

Limits: Account-level administrator override remains possible.

### D2 — Validator/catalog drift versus candidate validity

PR15 sampled live ResourceArn schemas and supported policy APIs retire those as independently proven candidate syntax/action defects; pinned1.40.2 diagnostics remain real failed checks. This is not proof of deployment success.

Close/test: Preserve failing pinned result and PR15 newer-validator comparison; future reviewed tool/disposition decision belongs to A3. No suppression, internal schema patch or dependency upgrade in PR18.

Limits: Public HTML contradiction remains visible. PR16 handler authority ambiguity is B4, not resolved by validator modernization.

### D3 — Evidence lineage and controls that survive the isolated attack

Finite model controls and independent execution remain useful but limited. Correcting a stale CI citation does not establish an exploit or erase actual final-head execution.

Close/test: Preserve distinct evidence classes; actual workflow head_sha prevails. PR16 final run36252726480 exists; run36252559383 is historical. Retain strict parser/binding, selected S3 version and maximum-boundary controls while testing AWS effects in B.

Limits: Tests may omit attacks; hashes do not authenticate author or human consent.

## Proposed phased procedure — requirements, not an executable runbook

This describes the smallest defensible sequence to design in a future PR. It does **not** claim the current templates implement independent holds: the runtime template creates its stage/deployment, requires issuer/audience/client parameters, and the current authorization gate always returns false. Fake issuer values or informal bypasses are not acceptable. Either approved provider/configuration must precede runtime creation, or a separately reviewed inert-start design must make the hold enforceable. Authority establishment itself needs a separate approved non-root path; no root write is implied.

### Phase 0 — Authorization/evidence preflight

- **prerequisites:** Approved account/region and exact phase scope; A1/A2 design; authentic DevF review
- **principal:** Independent reviewer + proposed non-root operator, read-only
- **mutation category:** None
- **expected evidence:** Current identity/policy/trust graph, exact source/templates/parameters, risk and stop plan
- **success:** Named next phase authorized for exact coordinate only
- **failure:** Missing/stale/contradictory evidence or approval: BLOCKED
- **rollback:** No mutation to roll back
- **next gate:** Authority establishment approval
- **fresh human authorization:** Required before any subsequent write

### Phase 1 — Establish authority and minimum inert bootstrap

- **prerequisites:** A1/A2 closure for resources being created; A3 exact bootstrap operation; independent approved authority exists
- **principal:** Separately approved non-root bootstrap operator; no root normal workflow
- **mutation category:** Future separately authorized narrow IAM/fence establishment and bootstrap CF creation only
- **expected evidence:** Effective grants/trust/boundaries, API ID, bucket/versioning/policy and exported identities
- **success:** Only reviewed inert resources exist; no usable uncontained role/data/traffic path
- **failure:** Unexpected resource, overbroad authority or partial failure: STOP
- **rollback:** Preapproved quarantine/retention/repair path; do not automatically delete evidence
- **next gate:** Read-back and generated-ID containment
- **fresh human authorization:** Required; not supplied by PR18

### Phase 2 — Inspect bootstrap and refresh exact-ID fences

- **prerequisites:** Phase1 complete or safely stopped; inert API; no sensitive artifacts or routes
- **principal:** Read-only reviewer; separately approved fence operator if a write is required
- **mutation category:** Read-back; any exact-ID policy change needs explicit separate approval
- **expected evidence:** Actual API/bucket/role/export identities and intended-vs-actual diff; no unwanted users of new roles
- **success:** A1 covers actual identities and independent creator/rollback windows
- **failure:** Unknown mutator/reuser or drift: keep ingress closed
- **rollback:** Keep inert; approved containment repair or retention
- **next gate:** Artifact/proposed runtime approval
- **fresh human authorization:** Required for writes, not read-only inspection

### Phase 3 — Publish immutable sandbox artifact

- **prerequisites:** Approved source/build/version intent; private fenced bucket and narrowly usable publisher
- **principal:** Approved actor assuming publisher role for this artifact only
- **mutation category:** Future S3 new object version, no overwrite/delete of selected evidence
- **expected evidence:** Bucket/key/version + independently verified artifact hash and publisher session
- **success:** Selected immutable version bound to release record
- **failure:** Mismatch/retrieval failure: no runtime creation
- **rollback:** Retain unused version; do not select it
- **next gate:** Runtime creation approval
- **fresh human authorization:** Required, exact artifact/version scope

### Phase 4 — Create bounded runtime with ingress held

- **prerequisites:** A1/A2 effective containment; approved regional schema/tool disposition; exact provider parameters if template requires them; reviewed enforceable hold
- **principal:** Approved stack operator passing exact CloudFormation deployment role
- **mutation category:** Future isolated runtime CF create only
- **expected evidence:** Actual roles/boundaries, function/version/alias/table/policies and service retrieval; stack events
- **success:** Runtime correct and ingress held; no legacy mutation
- **failure:** Unexpected grants, failed create or missing protection: STOP
- **rollback:** Preapproved quarantine/failed-create retention/repair, not assumed ContinueUpdateRollback
- **next gate:** Configuration inspection
- **fresh human authorization:** Required; current template combines stage/runtime and needs reviewed phase-hold treatment first

### Phase 5 — Approve provider/profile and exact server binding

- **prerequisites:** Provider capability/flow and administrator approved; synthetic identities only; runtime remains held
- **principal:** Separately approved identity/configuration operator + reviewer
- **mutation category:** Future explicit IdP/config/binding operations only, none authorized here
- **expected evidence:** Issuer/audience/client/scopes, approved subjects/tenant mapping, registry version/hash and actual published config
- **success:** Approved values bind the immutable release; no invented live values
- **failure:** Shape mismatch or unsafe update snapshots: remain held
- **rollback:** Keep held; return to reviewed config/release
- **next gate:** Limited test-ingress authorization
- **fresh human authorization:** Required; move this phase before4 if current template needs real provider values

### Phase 6 — Enable only controlled synthetic test ingress

- **prerequisites:** Configuration read-back; approved test plan; containment and recovery still current; B3 successful
- **principal:** Approved exact stack/stage operator
- **mutation category:** Future bounded activation under explicit test authority
- **expected evidence:** Correct stage/route/integration/auth/source/alias, fresh actor and approval
- **success:** Only intended test scope active for approved interval
- **failure:** Drift/exposure: immediately use approved stop control
- **rollback:** Close test ingress using reviewed bounded control
- **next gate:** Authorized positive/negative tests
- **fresh human authorization:** Required; testing permission is not ordinary ingress permission

### Phase 7 — Run positive/negative sandbox tests

- **prerequisites:** Explicit invocation/synthetic data/test-principal authority; B1/B2/B5 test definitions
- **principal:** Approved test identities and constrained negative-test actor
- **mutation category:** Future tightly scoped test invocations/synthetic items, prohibited in PR18
- **expected evidence:** Real JWT/projection/source context/qualified-policy/role-use results, sanitized signals and hashes
- **success:** Expected allows/denies and no unexpected mutation/exposure
- **failure:** Any unsafe Allow, wrong claims/binding or leak: stop and retain evidence
- **rollback:** Close ingress; isolate synthetic state; independent remediation decision
- **next gate:** Lifecycle drill review
- **fresh human authorization:** Required; no real credential/payload capture in evidence

### Phase 8 — Exercise rollback/recovery and remove elevation

- **prerequisites:** Separate approved destructive/lifecycle scope and retained-resource plan; bounded repair authority
- **principal:** Approved recovery operator; emergency elevation only if independently authorized
- **mutation category:** Future sandbox lifecycle/rollback/repair actions, none now
- **expected evidence:** Actual handler/principal/context where observable, retained access, recovery and removal/expiry record
- **success:** Known stop/recovery path works and temporary authority removed
- **failure:** Unknown failed state: quarantine, stop and request exact repair authority
- **rollback:** Use only preapproved contingency; no improvised wildcard grants
- **next gate:** Human review of experiment
- **fresh human authorization:** Required separately from normal deployment

### Phase 9 — Authorize only the next named state

- **prerequisites:** B results reviewed; no unresolved safety failure; exact source/config still valid
- **principal:** DevF + independent reviewer
- **mutation category:** None from this record; any next use/phase requires separate scope
- **expected evidence:** Signed/authenticated decision and evidence references, current hashes and authority
- **success:** Bounded next state explicitly approved or remains blocked
- **failure:** Missing evidence/approval: no progression
- **rollback:** Keep/restore safe held state
- **next gate:** Further sandbox or separate production program
- **fresh human authorization:** Always required; never inferred from green CI

## Blockers retired, reclassified or sharpened

- ResourceArn spelling and policy action names are not independently established candidate defects: PR15 live registry/catalog evidence supersedes pinned-catalog assumptions. The real failing lint/release-tool contract still needs a reviewed A3 disposition; do not falsify a green check.
- PR16 DescribeStacks remains unverified B4 lifecycle behavior, not a proven initial-create failure. A2 must still provide bounded contingency before create.
- Missing provider/binding blocks token-capable ingress, not creation of a deliberately inert API. Provider choice/config approval is an A3 phase prerequisite; actual projection/signature behavior is B1.
- PR16 final execution is not absent: run36252726480 is the true final-head run. P28 is a stale prose citation corrected here.
- Role reuse P07 is a new supported authority concern under A1, independent of invoking the protected Lambda. P08 Gateway control-plane management broadens that same gate, without counting each operation as a new prerequisite.
- P23 fixed snapshots and P19 cached bindings require update/revocation remediation before relying on those transitions. They do not prove first-create failure.
- Root/admin override is D1, not an impossible requirement to contain account root before sandbox. It never excuses a normal legacy-user bypass or root writes.

## Next PR scope

An offline authority-containment and phased-operator design/remediation PR should first close the **design** of A1/A2/A3: exact principal/action/resource graph, role-use controls, API management coverage, bounded bootstrap/recovery/publishing authority, and enforceable inert-start/activation holds with negative tests. Evaluate documented source-function identity restrictions and narrow PassRole containment without presupposing a specific policy. Do not silently attach fences to legacy identities. Any eventual IAM/resource writes need a separate explicit human decision and refreshed evidence. Snapshot/update remediation is a separate small change before B5 tests. Validator modernization and DescribeStacks authority stay separate decisions.

Candidate behavior changed: NO. `deployment_authorized=false`.
