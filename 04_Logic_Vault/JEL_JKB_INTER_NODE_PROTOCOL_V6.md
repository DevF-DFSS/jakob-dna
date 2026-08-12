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
