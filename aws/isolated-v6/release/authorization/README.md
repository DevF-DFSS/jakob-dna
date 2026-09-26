# PR13 pre-activation authorization contract

Status: OFFLINE MODEL / UNCONFIGURED. Parent PR12 is retained without infrastructure
or runtime edits. This layer distinguishes a technically plausible candidate from
current, independently authenticated authorization evidence. It is not a deployer.

`tools/authorization_gate.py` consumes a versioned record, a separately trusted
expected context, trusted current UTC time, and digests attested by an independent
verification boundary. It has no network, SDK, credential, IAM or deployment code.
The CLI deliberately has no verification adapter and always exits nonzero.
An approval string, content hash, file source label or PASS result is not proof.
Only an independent verifier may populate `verified_digests`; taking them from the
same record/request would destroy the trust boundary and is forbidden. That real
verifier and DevF identity/signature/approval process remain UNRESOLVED.

Required gates are account, region, operator, recovery, effective_authorization,
schema, offline_validation and devf_authorization. Each must include source,
observation time, evidence class, result and the identical full context: account,
region, IAM operator/recovery role ARNs, candidate commit, runtime/bootstrap
template, artifact and binding hashes. Live gates require AWS_LIVE_READ_ONLY;
tests require newly executed LOCAL_EXECUTION; DevF requires HUMAN_AUTHORIZATION.
Historical, synthetic or merely documented results cannot satisfy live gates.
A future live collector must actually inspect its claims; a label is not validation.

Missing/unverified evidence produces UNKNOWN. Malformed, contradictory/duplicate,
failed, future, over-24-hour, wrong-context or blocker-bearing evidence is BLOCKED.
No partial PASS. Boundary age 24 hours is accepted; older fails. The freshness cap
is conservative policy, not evidence that IAM cannot change sooner. Any policy,
identity, artifact or context change invalidates the decision and requires a fresh
review; proof immediately before execution is a separate required control.

COMPLETE means all inputs satisfy this offline contract under its supplied trust
assumptions. **Every result still has deployment_authorized=false.** No current
candidate or checked-in file includes authenticated approval. A future executor
must authenticate explicit scoped DevF authorization, recheck all gates against
actual context and reject drift before any operation. This PR does not implement
that executor or authorize its introduction. An authorization for review, builds,
GitHub publication or AWS reads does not authorize deployment.

The current record intentionally has null context, blockers and no evidence. Do
not populate invented live values. Tests use synthetic 111111111111 identities and
explicit test-only verified digests. Even that positive case cannot deploy.
Evidence manifests should live outside the commit they reference to avoid a
self-referential source hash; their own hashes/review records need independent
retention. The release manifest v1 remains a separate necessary consistency gate;
this contract does not waive PR12's unresolved schema or bootstrap approval gates.

## Non-root recovery operator proposal

Exact proposed role: `/jel-v6-approved/JaKoBV6RecoveryOperator`, not created.
The machine-readable `recovery-operator.json` is an UNCONFIGURED policy template,
not deployable IAM, a grant, or proof of least privilege in a real account.
Trust must name a separately approved federated human principal with enforced
MFA/identity assurance and bounded sessions. No issuer/principal is invented;
root and legacy users/roles are not normal operators. The account/region remain
unapproved. A connector reporting root may support read-only discovery only.

Normal authority reads the two approved stack coordinates and requests reviewed
runtime updates/rollback through the exact PR12 deployment service role. PassRole
is limited to that role and CloudFormation. It cannot pass runtime/recovery roles,
assume publisher/deployer identities, directly invoke Lambda, access application
data, alter legacy infrastructure or repair bootstrap IAM/bucket policies. The
normal role's effective maximum must be bounded to this same scope; no broad
AdministratorAccess is proposed. Parameter placeholders MUST be exact reviewed
ARNs; the template is not safe to attach unrendered. Conditions and handler action
requirements must be validated for actual CF operations before any grant.

Runtime updates can change runtime policy/code through the deployment role: this
is a privileged recovery capability, not a harmless read. Restrict stack control,
review the exact diff, enforce DevF approval and audit who can reuse the existing
service role. IAM alone does not authenticate the contents of a reviewed template.
Neither this normal policy nor its model prevents a sufficiently privileged admin
from altering protections. Operator authorization is a required human/security
boundary and remains unproven, not an automatic exception to containment.

Initial bootstrap and emergency repair are OUTSIDE normal authority. Bootstrap
creates managed boundaries/roles and bucket policy; repair might replace those
policies, correct trust, restore a retained bucket policy or repair a failed stack.
Those actions genuinely require elevated exact-resource, time-limited privileges,
separate review/approval and a restoration plan. They must not be permanently
folded into the normal role or used to bypass runtime principal fences. PR12's
bootstrap execution-as-approved-recovery-role design therefore still requires an
independently approved temporary bootstrap authority. No role is created here,
no existing user modified, and no policy attached. Rollback never implies deleting
retained artifacts/table or removing legacy fences. Unknown recovery rights block.

## Provenance classes and remaining work

- GitHub-observed: PR12 head/tree; PR13 publication when performed.
- Work local execution: checkout blob verification, new tests, lint and builds.
- Synthetic model: gate completeness and policy assumptions in fixtures.
- AWS live evidence: **none collected for this narrowed PR13 scope**. Supplied
  earlier review observations are not independently verified by this PR and cannot
  clear current gates. Inherited PR12 evidence is historical, not freshly executed.

UNRESOLVED: live registry form and alias-scope enforcement; effective IAM/SCP/
boundaries, unsupported management paths, root connector replacement, federated
operator trust, least-privilege bootstrap/emergency grant, DevF verification,
freshness/invalidation collector, release attestation, account/region/provider/
bindings, operational rollback and separate deployment authorization. PR12 fences,
retention and bootstrap/runtime separation are unchanged. No semantic state layer.
