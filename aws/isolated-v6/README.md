# Isolated V6 offline activation readiness — 2026-09-25

Status: DOCUMENTED / OFFLINE TESTED, not deployed or approved for deployment.
PR #12 same-account isolation candidate is stacked directly on reviewed PR #11
`42cf882bae2fe9ab7020c8c62c7cea189525bc64`. The recovered local work was preserved.
Read [the isolation design](isolation/DESIGN.md) for bootstrap/runtime fencing,
action-level enforcement limits, and unresolved CloudFormation schema conflict.
Provider-neutral core, runtime code and empty bindings remain unchanged.

## Activation components

- `aws_v6/activation.py`: validates named non-secret settings and packaged binding
  registry before constructing a low-level boto3 DynamoDB client; wires clock,
  DynamoEventStore, core Ingress and LambdaHost. Client is reused by the initialized
  host. Startup failure returns static 503 without configuration/exception text.
- `config.py`: immutable settings, exact sandbox/API/region/qualified-alias checks,
  HTTPS issuer, explicit audience/client list, isolated table prefix, registry
  version and SHA-256. Missing/malformed config or empty registry fails closed.
- `claims.py`: consumes only HTTP API v2 `requestContext.authorizer.jwt` claims
  and scopes under the trust assumption below; returns a typed Principal or None.
  Headers/body identity, bypass flags and legacy fallbacks are never consulted.
- `bindings.json`: deliberately empty UNCONFIGURED registry. Replace in a reviewed
  source change with approved identities and policy before building for activation;
  set matching version/hash parameters. There is no request/env path override.
- PR #8's `dynamodb.py` remains unchanged: conditional PutItem, strong GetItem,
  immutable record marshalling, typed conflict handling and StoreUnavailable.

`compose()` permits client/path/clock injection for offline tests only. The
production handler invokes it without caller-supplied dependencies. Importing
modules never constructs SDK clients. Default boto3 credential discovery would
occur only in a later deployed composition after valid startup; it was never run
in this work. Tests inject explicit synthetic credentials with SDK config files
redirected to /dev/null and block the credential resolver and HTTP transport.

SDK retries use one total attempt, two-second connect and three-second read
limits. An uncertain write surfaces as 503; clients retry the same event ID/body.
This avoids hidden multi-attempt write semantics. Client configured endpoint URLs
and proxies are disabled by the composition, with explicit approved region.

## Explicit authentication boundary

API Gateway cryptographic authentication → trusted host claims adapter → server
binding/authorization → integrity → freshness → idempotency.

Lambda DOES NOT verify JWT signatures, retrieve keys, contact the issuer or decode
a bearer token. The adapter trusts Gateway-origin authorizer data ONLY under the
external assumption that Gateway verified the JWT and IAM/resource policies
prevent direct-invocation bypass. That assumption remains 🐈📦 UNRESOLVED.

Gateway must verify signature/key, exact issuer/audience, validity and route
scopes. The host rechecks claim profile and context consistency. A direct invoker
with InvokeFunction permission can forge ALL event fields, including authorizer
claims. Checking the qualified alias ARN in Lambda context does not prevent an
actor allowed to invoke that alias. A regression test intentionally demonstrates
that a fully forged structurally valid event passes these local checks. Never
represent this test as authenticated identity or effective invocation isolation.

The candidate full resource policy grants only the two new API/stage routes access
to the alias and models explicit non-Gateway/legacy denies. Unlike an Allow alone,
a supported explicit Deny overrides identity grants; actual enforcement is unproven.
Real IAM/SCP/boundary evaluation and negative invocation tests are mandatory gates.

## Required claim profile (proposal, not observed provider behavior)

`authorizer` must contain exactly `jwt`; `jwt` exactly `claims` and `scopes`.
Claims are a bounded dictionary of strings. Required claims:

- iss: exact configured HTTPS issuer.
- aud: exact single string audience. Arrays and client_id-as-aud fallback rejected.
- client_id: member of configured approved list. No azp or other fallback.
- sub: nonempty, trimmed, control/whitespace-free immutable subject. Exact
  `(iss,sub,client_id)` must match server policy; unknown/revoked subjects deny.
- token_use: exactly access. ID-token-shaped claims rejected.
- scope: single-space-separated unique values matching the authorizer scopes
  list exactly. Only jel-v6/read and jel-v6/write allowed; core requires route scope.
- exp and iat: required decimal epoch-second strings; exp strictly future,
  iat not future and earlier than exp. No token-time skew allowance.
- nbf: optional only when absent. If present, it must be a decimal epoch-second
  string, not future and earlier than exp. Null, booleans, numbers, fractional,
  negative, whitespace or oversized values fail closed.

API ID and sandbox stage must match, payload version must be 2.0, and invoked
alias ARN must match the configured qualified sandbox ARN. A provider that omits
token_use/client_id, supplies an audience array, or uses a different scope
shape needs an explicitly reviewed profile revision; no permissive inference.

## Server-owned registry

Packaged JSON has exactly version and nonempty bindings. Each binding contains
issuer, subject, client_id, tenant, senders, receivers, instructions. Duplicate
JSON members/tuples, unknown keys, wrong version/hash, empty/duplicate permission
sets, invalid identity/config and oversized registry fail before client creation.
The packaged file is capped at 64 KiB; no remote policy fetching or self-enrollment.
The unchanged Registry enforces tenant/sender/receiver/instruction policy.

Registry updates require a new reviewed package/version and matching configuration;
warm instances retain their initialized snapshot. Core revocation tests cover
subsequent checks within a process, not distributed revocation or cancellation
of already-authorized requests. Emergency ingress disable/revocation rollout
requires an approved operational plan.

## Pinned dependencies and offline tooling

Runtime wheels and SHA-256 values are in dependencies.lock.json and requirements.lock:
boto3 1.40.35, botocore 1.40.35, jmespath 1.1.0, s3transfer 0.14.0,
python-dateutil 2.9.0.post0, six 1.17.0, urllib3 2.8.0. These are tested pins, not
claims of latest versions or a vulnerability assessment. All are pure Python
wheels included in the runtime artifact with distribution metadata/licenses.
No reliance on Lambda's unpinned SDK or local macOS native libraries.

Validation uses cfn-lint 1.40.2; exact installed development-tool versions are
recorded in validation-toolchain.lock. Development tools are NOT in the Lambda
ZIP. cfn-guard/Autopilot were not installed/run; the existing narrow static IAM/
resource allowlist and negative tests are the equivalent local checks here.
Static validation is NOT effective AWS authorization proof.

The dependency cache was acquired during historical PR #9 work. PR #11 reused
that cache without downloads. No AWS service, console, STS, metadata or deployment
endpoints were contacted in this remediation; no credential discovery or paid
agents were used. PR #10's authorized read-only observations remain dated evidence.

From repository root, with a Python 3.13 virtualenv and approved local wheel cache:

```sh
python -m pip --isolated install --no-index --find-links aws/isolated-v6/wheelhouse --require-hashes -r aws/isolated-v6/requirements.lock
python -B aws/isolated-v6/tools/run_checks.py --core reference/isolated-v6
python -B aws/isolated-v6/tools/lint_offline.py -t aws/isolated-v6/infra/template.json -r us-east-1
python -B aws/isolated-v6/tools/build.py --core reference/isolated-v6 --source-commit FULL_40_HEX_COMMIT --output work/v6-build --diagnostic-only
```

Install the recorded cfn-lint development environment separately from an approved
cache before lint/build. The wheelhouse is not committed; acquire exact official
wheels matching the lock before going offline. Builder accepts `--wheelhouse`;
its default is the candidate directory's wheelhouse. Unit packaging tests expect
the default cache. No install or download happens inside build/test tooling.

## Validation and artifact evidence

231 offline tests pass: 86 unchanged core, 41 candidate, 50 activation/real-SDK,
29 PR #11 remediation, one new failed-lint release-gate test and 24 isolation tests (with negative subcases).
PR #9 historical result was 177 tests; it is not the result for this candidate. Runner blocks socket creation, botocore HTTP send and credential
resolver. Real Stubber validates operation shapes/typed errors; separate botocore
serializer tests verify JSON AttributeValues. No actual service behavior is proven.

cfn-lint 1.40.2 does NOT pass this candidate: missing us-east-1 resource schema
and outdated action catalog. Both templates and auxiliary eu-west-1 diagnostics
are recorded in infra/offline-validation.json. No findings are suppressed.
Region selection is a test fixture, NOT approval of an account/region. Existing security
checks reject legacy references, additional env vars, broad permissions, NONE/ANY
routes, public Function URLs and unqualified invocation grants.

Build verifies wheel hashes, includes runtime modules + bindings + locked wheel
contents, normalizes ZIP order/timestamps/permissions, excludes wheel CLI scripts,
and records source commit, every included file hash, dependency wheel hashes,
Python/runtime/architecture, actual test results and offline lint result.
Use --diagnostic-only solely to retain review artifacts with failed lint marked
false; ordinary builds fail. Release validation rejects that provenance.
Two independent builds must yield byte-identical ZIP and provenance. Manifest
source commit remains caller-supplied: verify its source-input hashes against the
Git tree before uploading. Local verification is unsigned, not a supply-chain
attestation. A new binding registry changes the artifact and requires new tests,
source attribution, hash, version and explicit approval.

The artifact retains the empty registry on purpose, so it fails startup closed.
Read [PREFLIGHT.md](PREFLIGHT.md) before any proposed activation. Passing offline
checks does not authorize deployment or establish production readiness.

## Portable pre-deployment remediation

PR #10 observed concurrency quota 10/unreserved 10 in both candidate regions.
Positive reservation 2 cannot leave AWS's required 100 unreserved. This template
now omits ReservedConcurrentExecutions entirely; static tests reject its return,
including zero (which would disable execution). This uses shared unreserved
capacity and is not a production capacity or legacy-availability design.

Stage default route throttles are now rate 1 request/second, burst 2, with no route
overrides. These apply to each route's default settings, not a guaranteed aggregate
budget/capacity reservation. AWS throttling is best effort, not a hard cost ceiling.
[HTTP API throttling](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-throttling.html).

The activation handler emits only fixed kind=v6_outcome and one of accepted,
not_found (404), rejected (other 4xx), unavailable. No event IDs, claims, headers, principal/binding identifiers,
payloads, SDK exceptions or environment values are logged. Two log metric filters
and alarms capture rejection and unavailable/503 outcomes, including caught startup
failures that Lambda Errors would miss. Existing Lambda Errors/Throttles remain;
a Gateway 4xx stage alarm covers upstream failures including possible 429s without
claiming to distinguish throttling from authentication failures. No access logging
or detailed route metrics are enabled. HTTP metric names/dimensions are documented
by [AWS](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-metrics.html).
Delivery/filter matching, alarm behavior, upstream attribution and notification
routing need live verification and owner-approved destinations. Signals add two
custom metrics and three alarms: PR #10's two-alarm cost estimate must be revised;
free allowances are unproved and this can add ongoing monitoring charges.

The synthetic Cognito-style fixture uses resource-bound aud, access token_use,
client_id/sub, and decimal projected time strings without nbf. It is not a minted
JWT, configured user pool or captured Gateway event. Optional nbf resolves only
that contract mismatch. Audience resource-binding flow, scope selection, string
projection, actual provider behavior and direct-invoke isolation remain unresolved.
No issuer/client/scopes/exp/iat/sender-binding relaxation is introduced.

## Release manifest v1 (offline gate, not deployment authorization)

`release/manifest.unapproved.json` deliberately contains null placeholders and an
UNAPPROVED declaration. `tools/release_manifest.py` defines the strict versioned
schema and rejects missing/extra/duplicate members, wrong formats, unset approval,
missing/duplicate/extra scopes, legacy artifact buckets, mismatched source/hash/provenance and
invalid or empty runtime bindings. It verifies local template/artifact/binding
bytes, template security checks and recorded test/lint success. It does not contact
AWS, prove that a bucket exists, authenticate the reviewer or prove source lineage.
Even a consistent record returns deployment_authorized=false. Do not treat an
edited approval string or caller-supplied commit as authority. Independent review
must verify source-input hashes against the approved Git tree and authorize any
future deployment separately. No uploader or deployer is included.

Run from repo root (expected-source must come from the independently reviewed SHA):

```sh
PYTHONPATH=reference/isolated-v6:aws/isolated-v6 python -B aws/isolated-v6/tools/release_manifest.py --manifest aws/isolated-v6/release/manifest.unapproved.json --expected-source FULL_40_HEX_COMMIT --template aws/isolated-v6/infra/template.json --bindings aws/isolated-v6/aws_v6/bindings.json --artifact work/v6-build/isolated-v6-candidate.zip --provenance work/v6-build/provenance.json
```

The shipped example must exit 1. Never fill it with inferred live identities;
review actual approved values and rebuilt bindings/artifact first. Use a release
record outside its own source tree to avoid a self-referential source-commit hash.
All current runtime bindings remain UNCONFIGURED. No semantic state model added.

PR #11 review correction: release schema jel-v6-release/1 requires exactly the
read/write scope set implemented by both candidate routes, in either order. This
is a runtime declaration, not per-client scope policy; such a capability needs a
separately versioned design. HTTP 404 maps to sanitized not_found and does not
match rejection/unavailable log metric filters. Existing Gateway 4xx monitoring
still counts HTTP 404 as part of its aggregate; no not_found alarm was added.
