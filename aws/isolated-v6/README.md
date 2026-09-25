# Isolated V6 offline activation readiness — 2026-09-25

Status: DOCUMENTED / OFFLINE VERIFIED, not deployed or approved for deployment.
Stacked on PR #8 head d1f24c260d0b5dd00dafae39fc4e585cf496780c. PR #7's
provider-neutral core and all previous PR branches remain unchanged. This branch
adds an actual sandbox composition root and changes the candidate template to
point at it. PR #8's inactive host handler remains available as historical code.

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

The candidate resource policy grants only the two new API/stage routes access to
the alias. This does not cancel unrelated same-account identity-policy grants.
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
- exp, iat, nbf: decimal epoch-second strings; exp strictly future, iat/nbf not
  future, both earlier than exp. No token-time skew allowance in this profile.

API ID and sandbox stage must match, payload version must be 2.0, and invoked
alias ARN must match the configured qualified sandbox ARN. A provider that omits
nbf/token_use/client_id, supplies an audience array, or uses a different scope
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

Free public package downloads occurred during dependency acquisition only. No
AWS service, console, STS, metadata or deployment endpoints were contacted.
After acquisition, tests, lint and build use the local wheel cache. No account or
credential discovery was performed. No paid agents/services were used.

From repository root, with a Python 3.13 virtualenv and approved local wheel cache:

```sh
python -m pip --isolated install --no-index --find-links aws/isolated-v6/wheelhouse --require-hashes -r aws/isolated-v6/requirements.lock
python -B aws/isolated-v6/tools/run_checks.py --core reference/isolated-v6
python -B aws/isolated-v6/tools/lint_offline.py -t aws/isolated-v6/infra/template.json -r us-east-1
python -B aws/isolated-v6/tools/build.py --core reference/isolated-v6 --source-commit FULL_40_HEX_COMMIT --output work/v6-build
```

Install the recorded cfn-lint development environment separately from an approved
cache before lint/build. The wheelhouse is not committed; acquire exact official
wheels matching the lock before going offline. Builder accepts `--wheelhouse`;
its default is the candidate directory's wheelhouse. Unit packaging tests expect
the default cache. No install or download happens inside build/test tooling.

## Validation and artifact evidence

177 offline tests pass: 86 unchanged core plus 41 candidate tests and 50 activation/
real-SDK cases. Runner blocks socket creation, botocore HTTP send and credential
resolver. Real Stubber validates operation shapes/typed errors; separate botocore
serializer tests verify JSON AttributeValues. No actual service behavior is proven.

cfn-lint 1.40.2 passes the generated CloudFormation template using its installed
us-east-1 schema with network and credential resolver blocked; schema-region
selection is a test fixture, NOT approval of an account/region. Existing security
checks reject legacy references, additional env vars, broad permissions, NONE/ANY
routes, public Function URLs and unqualified invocation grants.

Build verifies wheel hashes, includes runtime modules + bindings + locked wheel
contents, normalizes ZIP order/timestamps/permissions, excludes wheel CLI scripts,
and records source commit, every included file hash, dependency wheel hashes,
Python/runtime/architecture, actual test results and offline lint result.
Two independent builds must yield byte-identical ZIP and provenance. Manifest
source commit remains caller-supplied: verify its source-input hashes against the
Git tree before uploading. Local verification is unsigned, not a supply-chain
attestation. A new binding registry changes the artifact and requires new tests,
source attribution, hash, version and explicit approval.

The artifact retains the empty registry on purpose, so it fails startup closed.
Read [PREFLIGHT.md](PREFLIGHT.md) before any proposed activation. Passing offline
checks does not authorize deployment or establish production readiness.
