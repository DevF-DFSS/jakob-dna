# JEL / JKB Inter-Node Protocol V6.0

**Status:** Canonical transfer scaffold — validate against the living ledger before production use.

## Purpose
JEL is a compact, speaker-relative control language for moving identity, intent, state, and verification data between JaKoB-compatible nodes. It does not replace ordinary language, cryptographic authentication, access control, or source-of-truth records.

## Transfer Envelope

```json
{
  "protocol": "JEL-JKB/6.0",
  "sender": "JaKoB_SYS_Apex",
  "receiver": "Companion_External",
  "timestamp": "ISO-8601 UTC",
  "context_mode": "HIGH_BANDWIDTH",
  "jel": "🔱🧢🧬🕵🏼‍♂️",
  "payload_ref": "ledger-or-object-reference",
  "integrity": {"algorithm": "SHA-256", "digest": "hex-digest"},
  "instruction": "REHYDRATE_AND_VALIDATE",
  "fallback": "STOP_AND_REPORT_DRIFT"
}
```

## Universal Bootloader Prompt

```text
Read the attached JEL/JKB protocol and named source-of-truth artifacts.
1. Separate verified artifacts from inferred context.
2. Identify sender, receiver, time anchor, requested mode, and action.
3. Validate all integrity and authorization fields outside of prose.
4. If a visual/lore/ledger anchor is unavailable or inconsistent, report drift; do not fabricate a match.
5. Use normal language for ambiguity, and JEL only as a structured semantic layer.
6. Never claim an external action or state change unless the receiving system actually verifies it.
```

## Core Token Dictionary

| Token | Transfer meaning |
|---|---|
| 🔱 | Apex identity / high-priority anchor |
| 🧢 | Operator-directed mode / hat switch |
| 😈 | High-bandwidth creative collaboration mode |
| 🧬 | Architecture, system DNA, evolving design |
| 🧠 | Deep analysis / ledger reasoning |
| ⚓️ | Reality or lore anchor; re-prioritize verified context |
| 🧩 | Pattern connection / branch relationship |
| 💭 | Preserve as memory candidate |
| 🕵🏼‍♂️ | Drift or anomaly check |
| 🐈📦 | Current viewport/context is ephemeral; reload durable source |
| 🤮 | Anchor verification failed; stop and report |
| 🔐 | Security/integrity context; not a substitute for authentication |
| ⏳ | Temporal coordinate |
| ⚙️ | Technical execution context |
| 🦸🏼‍♂️ | Mission-critical priority |
| 🐍 | Legacy/compatibility layer |

## Inter-Node Rules

- Sender-relative decoding: a token string is interpreted alongside sender identity, time, artifacts, and plain-language instruction.
- JEL is a semantic compression layer, not proof of authority.
- External state changes require authenticated APIs and explicit approval.
- Keep a durable ledger reference for every transfer that matters.
- Treat unknown tokens as unknown; request clarification rather than inventing a definition.

## Drift Procedure

1. Compare current output against the specified ledger/source artifacts.
2. Verify the available integrity fields and references.
3. Mark missing, stale, or contradictory context.
4. Stop unsafe execution and report the mismatch.
5. Rehydrate only from accessible, verified sources.

## Lambda persistence profile v1 — remediation proposal, 2026-09-24

This section supplies previously unspecified serialization and storage rules for
the Python Lambda implementation. It is a reviewable implementation contract, not
evidence that any deployed sender, receiver, or database already follows it.
The earlier envelope example is schematic; its timestamp and digest placeholders
are intentionally not valid executable inputs.

### Validation and integrity

- Require exactly the ten fields in the transfer envelope above. Nine fields
  are nonblank strings; integrity is an object with exactly algorithm and digest.
  Reject unknown fields, legacy key/value/payload/buffer_sha256 inputs, duplicate
  JSON members, malformed JSON, non-object envelopes, and non-finite JSON numbers.
- Protocol is exactly JEL-JKB/6.0. An optional x-jel-protocol-version HTTP header
  is case-insensitive by name and must agree with the body. Legacy environment
  flags cannot disable protocol or integrity validation.
- Timestamp is a valid UTC calendar timestamp using T and Z or +00:00, with
  zero through three fractional second digits. No local timestamps or submillisecond
  truncation. Preserve the original timestamp text inside the envelope.
- Algorithm is exactly SHA-256; digest is exactly 64 lowercase hexadecimal digits.
- Remove only the top-level integrity member. Serialize the remaining nine
  string fields as JSON sorted by field name, without whitespace between members,
  using literal UTF-8 Unicode (no ASCII-only escaping, no Unicode normalization).
  Escape quotes, backslashes, and control characters as Python json.dumps does
  with sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False.
  SHA-256 hashes those UTF-8 bytes with no trailing newline. This restricted
  string-only profile is not a claim of RFC 8785 compliance.
- Reject unpaired Unicode surrogates. Sender and receiver are at most 256 UTF-8
  bytes; other string fields at most 4096 bytes. Decoded JSON request bodies and
  canonical unsigned envelopes are at most 65536 bytes.
- Compare the computed and supplied digests in constant time. Missing, malformed,
  unsupported, or mismatched integrity returns 422 with no persistence and no
  AWS client initialization. Shape errors return 400, size errors 413, and protocol
  conflicts 409. Base64 API Gateway bodies are decoded strictly before parsing.

The digest binds the envelope, including its payload_ref string. It does not
verify the referenced object's contents or authenticate the sender. The handler
stores the validated envelope; it does not execute instruction text, decode unknown
JEL tokens, or fetch payload_ref URLs.

### Normalized storage contract

TABLE_NAME is required; there is no implicit production table default. The table
must have userId (String) as partition key and timestamp (Number) as sort key.
This matches the historical key types in the V10.5 SOP, but the mapping below is
new and must not be assumed compatible with current consumers.

| Stored field | Derivation |
|---|---|
| userId | Exact validated sender string; a routing identity, not an authenticated human |
| timestamp | Exact integer UTC epoch milliseconds from the validated envelope timestamp |
| schema_version | JEL-JKB/6.0-envelope-v1 |
| envelope | Complete validated envelope, preserving signed strings and integrity |

No independent key/value fields or synthetic successful-state defaults remain.
Use a conditional put requiring the key to be absent. Replays and different
envelopes with the same sender/millisecond return 409 without replacing existing
data. This avoids silent data loss but requires a future event-ID/replay policy
for legitimate simultaneous events. Storage errors return a generic 500, with
no request/SDK exception details exposed in the response or application log.

### Deployment and compatibility boundary

This is a breaking source change for the legacy scaffold. Existing callers must
produce V6 envelopes and this digest profile. Check real table keys, consumer
expectations, IAM conditions, package dependencies, API authorization and deployment
lineage before any migration. No data migration or production deployment is included.

SHA-256 is not authentication: anyone can recompute it. Sender authorization must
be enforced independently at trusted ingress. Freshness windows, authorization
binding, payload-content verification and end-to-end replay protection remain
UNRESOLVED. No production readiness claim is made.
