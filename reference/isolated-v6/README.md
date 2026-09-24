# Isolated V6 ingress — offline reference implementation

Status: DOCUMENTED / OFFLINE VERIFIED, 2026-09-24. Implements Phase 1 of
[PR #6](https://github.com/DevF-DFSS/jakob-dna/pull/6), stacked on its head
`8ec33eda8a75e1994257456c3efa1985a31039e7`. This is not a deployable Lambda or an
authentication provider. No AWS SDK, network client, credentials, infrastructure
or third-party dependencies are needed. Python 3.10+; checked locally on 3.13.

From the repository root:

```sh
cd reference/isolated-v6
python3 -B -m unittest discover -s tests -v
```

86 offline tests pass, including thread races within the in-memory adapter. This
is not proof of DynamoDB atomicity, durability, load capacity or production safety.

## Modules and boundaries

- `isolated_v6/http.py`: HTTP API v2-shaped event parsing. Requires explicit API
  ID/stage, exact POST/GET route/method/path, JSON content type, no query parameters
  or compressed bodies. Ignores unused Gateway metadata and pathParameters;
  derives receipt keys from rawPath with canonical percent-encoding. API/stage
  values are consistency checks, not proof that Gateway authenticated the event.
- `envelope.py`: selectively reuses PR #4's canonicalization and validation
  (`cbe8eeff045802a305a98b78d743328f17403dcf`), adding a root type guard. No other
  PR #4 implementation or persistence code is merged. Exact ten fields, nine
  nonblank strings, UTF-8 limits (sender/receiver 256 bytes; other fields 4096),
  UTC timestamp with at most millisecond precision, SHA-256 lowerhex integrity.
- `contract.py`: exact four-field wrapper, canonical lowercase UUIDv4, separate
  submission time, inclusive age 300 seconds / future skew 30 seconds, and full
  canonical wrapper digest. These fixed policy values implement PR #6's proposal;
  changing them requires policy review. Historical envelope timestamp is preserved.
- `auth.py`: immutable trusted principal tuple `(issuer, subject, client_id)` with
  verified scopes, server-owned binding registry, default-deny tenant/sender/
  receiver/instruction policy, explicit revocation for subsequent requests.
- `store.py`: immutable event and receipt records, conditional insert/strong-read
  interface, and single-process locked in-memory adapter. No delete/update API.
- `service.py`: authorization, validation and persistence orchestration, receipt
  recovery, static sanitized response/log codes. No payload dereference, model
  call, instruction execution, legacy forwarding, or secondary effects.
- `errors.py`: internal static rejection codes.

## Authentication is a trusted host boundary

`Ingress.handle(event, trusted_principal=principal)` accepts Principal only from
trusted host code after independent authentication. The default is unauthenticated
and denies access. It never extracts identity from Authorization headers, body
fields, `requestContext.authorizer`, or a claims dictionary. Synthetic Principal
objects occur in offline tests only. No JWT parsing or verification is implemented.

A Python class is not a cryptographic capability: anyone with trusted process-code
execution could construct it. A future adapter must authenticate requests and
control invocation before constructing Principal; it must never deserialize a
client-controlled object into this argument. API context matching alone cannot
prevent forged direct invocation. Real issuer/audience/signature/time/token-type
verification and transport TLS enforcement remain external unresolved gates.

Read/write scopes are independent of binding. Every POST (including retries) and
GET checks the current registry; GET checks tenant/sender and returns only a receipt.
Registry entries are server-owned frozen values. Revocation denies subsequent
checks; requests already authorized may finish. Distributed revocation and
in-flight cancellation are not claimed.

**authentication ≠ authorization ≠ integrity ≠ freshness ≠ idempotency**

SHA-256 does not prove identity or referenced-payload contents. Any authenticated,
authorized sender can recompute it. A new event ID represents a new event even if
business content repeats; semantic deduplication is outside this contract.

## Wire, size and canonicalization rules

Body must be a string and isBase64Encoded an explicit boolean. Limit decoded body
to 65,536 UTF-8 bytes; check encoded length before base64 allocation and require
canonical padded base64. JSON nesting is capped at 16; reject duplicate members
at every depth, non-finite constants, invalid Unicode/JSON and extra wrapper or
envelope fields. Header count is capped at 64 and aggregate text length at 16,384;
header names are case-insensitive with duplicates rejected. Optional
X-JEL-Protocol-Version must match JEL-JKB/6.0. GET has no body or freshness check.

Canonical envelope bytes are sorted compact JSON, literal UTF-8, no Unicode
normalization, excluding only integrity. Full request digest includes integrity
and all four wrapper fields. JSON ordering, spacing and escape spelling do not
change identity; changing signed string text, issued_at or integrity does.
Timestamps accept Z or +00:00 but preserve exact text, so changing spelling under
the same event ID is a conflict, even if the instant is equal.

## Persistence and receipt semantics

PK is canonical JSON `[tenant_id,sender]`; SK is `EVENT#<event_id>`. Tenant is derived
from binding, never the request. Frozen records store canonical immutable wrapper
bytes, full request digest, profile, hashed principal reference, binding version,
and an immutable receipt. Wrapper bytes retain envelope and issued_at losslessly.
This is a provider-neutral representation, not DynamoDB marshalling; a later
adapter must map the wrapper to the PR #6 proposed envelope/issued_at attributes.

Conditional insert returns 201 exactly once per key. On existing key, strong read
and matching digest return 200 with the original receipt; mismatch returns 409.
Missing conflict-read results or StoreUnavailable (including uncertain commit)
return 503. Retrying must reuse the complete original wrapper. Stale POST fails
before store access; authenticated GET can recover its receipt. Unexpected internal
exceptions return a static 500 with no exception text or traceback logging.

The store is an internal trusted adapter: insert_if_absent must never overwrite,
get must be strongly consistent, and failure must raise StoreUnavailable. The
memory implementation loses all data on process exit; it is for offline tests.
No TTL/deletion exists: future retention must preserve idempotency guarantees.
Logs contain only fixed status/reason codes, never requests, JWTs, refs or identities.

## Validation and open gates

Tests cover malformed/bounded transport, duplicate JSON/header fields, Unicode
and canonical bytes, tampering of every signed field, bad/missing integrity,
spoofed/unknown/revoked principals, scope/binding/tenant denial, freshness limits,
threaded same/different-ID races, conflicts, lost-response recovery, stale receipt
lookup, forged auth contexts, size limits and immutability. No cloud calls are
made. Tests do not imply any lineage between source and legacy deployed packages.

- 🐈📦 UNRESOLVED: real JWT verification/provider claims and TLS/authentication adapter.
- 🐈📦 UNRESOLVED: real DynamoDB concurrency, durability, AWS SDK integration/marshalling.
- 🐈📦 UNRESOLVED: IAM and API Gateway configuration, direct-invocation isolation.
- 🐈📦 UNRESOLVED: deployment, artifact provenance, load testing and cost.
- 🐈📦 UNRESOLVED: approved accounts/region, owners, bindings, retention/recovery policy.
- 🐈📦 UNRESOLVED: legacy lineage, caller/reader migration, payload-reference verification.

PRs #3–#6 and legacy source remain unchanged. PR #5 remains dated live evidence;
no live AWS state was queried or inferred during this implementation.
