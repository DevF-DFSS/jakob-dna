# Offline AWS isolated V6 deployment candidate — 2026-09-24

Status: DOCUMENTED / OFFLINE VERIFIED; NOT DEPLOYMENT READY. Stacked on PR #7
`401893f24e784795efa900ea32554ab1ca61e64c`. Preserves the provider-neutral core at
`reference/isolated-v6` byte-for-byte. No AWS calls, deployment, provider
provisioning, credential inspection or paid external agents are needed or used.

## Boundaries and modules

`aws_v6/dynamodb.py` implements PR #7's EventStore interface with an injected
**low-level** DynamoDB client (`put_item`, `get_item`, typed conditional exception).
Do not inject a resource client with automatic marshalling. No boto3 import,
client construction, credential-provider access or endpoint discovery occurs.
The host integrator must choose and pin the real SDK later; runtime SDK versions
are not guessed from the Lambda environment.

PutItem uses `attribute_not_exists(#pk) AND attribute_not_exists(#sk)` on PK/SK.
Only the client's typed ConditionalCheckFailedException returns False. Every
other failure or unexpected status, including uncertain commits, becomes a
sanitized StoreUnavailable. GetItem always uses ConsistentRead=true, verifies
returned keys, and strictly decodes immutable records; malformed records fail
closed. Missing Item in a successful response means absent. No update/delete/
scan/query methods are present. No error text is logged or returned.

Marshalling uses explicit low-level AttributeValues. String fields: PK, SK,
profile, request_digest, wrapper_json, principal_ref, binding_version. Receipt is
a Map with String event_id/status and exact integer Number accepted_at_ms.
wrapper_json is lossless canonical UTF-8 JSON converted to a DynamoDB String,
reconstructed as immutable bytes on read. This preserves the exact PR #7 Event
contract; it deliberately does not duplicate envelope/issued_at fields, avoiding
two disagreeing representations. A reader migration must use this schema rather
than assuming the earlier PR #6 illustrative expanded envelope map. Whole-record
schema checks, signed-envelope validation and digest checks detect corruption;
receipt reads do not reapply freshness to historical submissions.

`aws_v6/host.py` exposes LambdaHost with an injected AuthenticationAdapter and
Ingress instance. Trusted deployment code must wire registry, store and clock.
Authentication errors return static 503; missing/untyped identity fails closed
in the unchanged core. The ZIP entry point `aws_v6.host.handler` ALWAYS returns
503 `deployment_candidate_not_activated` and never accesses a store. There is
no environment switch to enable it and no fake JWT decoder. Replacing it with a
reviewed composition root is an explicit deployment gate, not an implied feature.

**authentication ≠ authorization ≠ integrity ≠ freshness ≠ idempotency**

## Authentication and invocation responsibility

| Boundary | Responsibility | Offline evidence limit |
|---|---|---|
| API Gateway JWT authorizer | Verify token signature, issuer, audience, lifetime and route scope; TLS ingress | Template parameters and JWT routes only; no provider/enforcement tested |
| AuthenticationAdapter / host | Supply immutable Principal only from an independently trusted authentication boundary; enforce approved provider claim profile; never use body/header identity as proof | Synthetic adapters only; no default claims extractor |
| Lambda core | Enforce scope and server-owned principal-to-tenant/sender/receiver/instruction binding, integrity, freshness and event identity | Existing 86 offline regressions preserved |
| IAM/SCP/resource policies | Prevent clients or unrelated roles invoking function/version/alias directly, changing code/config or passing its role | Only API Gateway grants are modeled here; full effective policy is unresolved |

`requestContext.authorizer.jwt` is data, not cryptographic proof inside Lambda.
A later Gateway-claims adapter could consume it only after the invocation path is
independently secured and tested. Matching API ID/stage is a consistency check;
an actor allowed direct InvokeFunction could forge those fields. Restricting the
resource-policy Allow to API Gateway does NOT eliminate identity-policy allows
in the same account or privileged administrators. An approved account-level
invocation restriction/SCP/boundary review and bypass tests are mandatory. This
candidate does not claim only API Gateway can effectively invoke in a real account.

## Single declarative infrastructure format

`infra/template.json` is plain CloudFormation; `tools/make_template.py` regenerates
it offline. Models only NEW resources: HTTP API, JWT authorizer, exact POST and
receipt GET routes, explicit sandbox stage with AutoDeploy=false and explicit
Deployment, new Python 3.13 x86_64 Lambda, published version/alias, new PK:S/SK:S
on-demand table, dedicated execution role, retained log group, Errors/Throttles
alarms, and separate alias-scoped invoke grants for POST and GET.

No legacy resources, external role imports, Function URL, NONE/default/ANY routes,
secret parameters, provider creation or automatic deployment are included. Table
has deletion protection, PITR, encryption and Retain on deletion/replacement.
The only permissions are PutItem/GetItem on the new table and log stream creation/
writes on the new function log group. Log-stream wildcard and GET sender/event
path wildcards are necessary for dynamic stream/path values; neither widens to
other tables, functions, APIs or stages. No runtime CreateLogGroup grant.

Issuer/audience and versioned artifact S3 location/code hash are mandatory input
parameters with no defaults. Artifact bucket is an externally approved build
prerequisite, not a legacy data bucket. No artifact is uploaded. No S3 permissions
are given to the runtime. Physical function/log names derive from StackName;
all other resources use generated names. Alarm destinations/owners are unresolved;
Lambda Errors does not count application 4xx/5xx responses, so application status
metrics/alarms must be added before activation. No raw request/access logging.

A future release must give CandidateVersion and CandidateDeployment new logical
IDs and update their references to force reviewed version/snapshot publication;
changing only Description is not a reliable release mechanism. The artifact SHA
parameter is Lambda's **base64** SHA-256, while provenance records hexadecimal.
Rollback uses a previously validated compatible alias version; retain event data.

## Offline checks and deterministic build

From repository root, Python 3.13, standard library only:

```sh
python3 -B aws/isolated-v6/tools/run_checks.py --core reference/isolated-v6
python3 -B aws/isolated-v6/tools/build.py --core reference/isolated-v6 --source-commit FULL_40_HEX_COMMIT --output work/v6-build
```

The runner denies socket creation and runs both core and adapter/template tests.
127 tests pass: 86 unchanged core tests plus 41 adapter/infrastructure/build tests.
Tests use a local fake client and do not prove service semantics. Static negative
tests reject unauthenticated routes, broad grants, wrong scopes, direct function
grants, extra env vars, legacy references and deployment drift. The structural
allowlist is deliberately narrow; it is not a general secret scanner or IAM engine.

Build uses sorted explicit runtime `.py` entries, fixed 1980 timestamps, fixed
permissions and ZIP_STORED to avoid compressor-version drift. No symlinks,
credentials, tests, SDKs, caches or infrastructure enter the runtime ZIP. Manifest
records source commit, Python/runtime/architecture, included file hashes, all
source/test/tool/template input hashes, dependency inventory, artifact SHA-256
and actual test results. Source commit is supplied by the caller; it is NOT a
signed provenance claim. Before upload, compare every input hash against that
Git tree and sign/retain the resulting attestation in an approved build system.
No generated ZIP or self-referential provenance is committed into the source tree.

Third-party dependency versions: none. The standard library version is the build
Python version. boto3/botocore are not bundled, imported or resolved; dependency
pinning and real client composition are unresolved activation gates. Identical
inputs under the recorded build Python yield identical ZIP and manifest; changing
source attribution changes the manifest, not the code ZIP. Do not use the bundled
AWS SDK implicitly without pinning and testing it.

## Required gates before any deployment or activation

1. Approve AWS sandbox account/region, naming/ownership, budget/retention/recovery
   policy; refresh dated PR #5 evidence only in a later authorized audit.
2. Choose real issuer/client profiles and binding governance. Implement/review an
   authentication adapter and composition root; verify JWTs, scopes, expiry,
   revocation, malformed identities and direct-invocation bypass.
3. Select/pin/vendor a real SDK from an approved offline dependency cache; add SDK
   serializer/stubber checks, then separately authorized sandbox service tests for
   conditional races, consistent reads, uncertainty, durability and IAM denials.
4. Run cfn-lint schema validation and cfn-guard/compliance in an approved offline
   toolchain. Those tools are absent here; no installation/download or AWS
   validate-template/change-set API was attempted. Current checks are structural.
5. Verify execution-policy baseline with approved tooling. iam-policy-autopilot
   and uvx are absent. No installation or account discovery was attempted under
   the offline/no-credential constraint. Future offline-approved command (replace
   the absolute checkout path; omit account/region until actually approved):
   `uvx iam-policy-autopilot@latest generate-policies /absolute/checkout/aws/isolated-v6/aws_v6/dynamodb.py --service-hints dynamodb --pretty`.
   Pin the tool before reproducible use. Injected clients may need a reviewed SDK
   composition source for analyzer detection. Never use upload flags. The template
   expresses the user's explicit PutItem/GetItem permissions and isolated logging
   requirements; it is not claimed to be analyzer-generated or effective IAM proof.
6. Review identity/resource policies, SCPs, boundaries and deployment role/PassRole
   separately; prove no legacy access or direct-invocation bypass. Validate template
   service schemas, explicit release IDs, artifact source binding and code digest.
7. Add application-status observability, approved alarm destinations, synthetic load,
   cost estimates, restore/rollback drills and opt-in caller/reader migration.
8. Obtain separate explicit deployment approval. No step here grants that approval.

🐈📦 UNRESOLVED: real JWT provider/issuer behavior; real API Gateway enforcement;
real IAM/SCP/boundary evaluation; real DynamoDB concurrency/durability; approved
AWS account/region; load/cost; caller migration; production deployment. Also:
SDK pinning/composition, schema-tool validation, effective auth adapter, retention,
alarm ownership, source/build signing and source-to-runtime lineage.
