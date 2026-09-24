# Recovery audit delta — 2026-09-24

Status: DOCUMENTED source evidence / offline verification; AWS deployment remains 🐈📦 UNRESOLVED.

Source anchor: recovery branch commit `6cc3649a9801fa7a5f7e14f399e8725190180083`; executable blobs match main `94401aed89d7b3704dc4800207c32fc68c3bd333`.

Observed in this pass through GitHub source inspection and isolated tests:
- Missing/incorrect SHA-256 does not prevent scaffold persistence when the protocol header matches.
- The digest covers payload, while persistence uses separate key/value fields.
- V6 envelope fields do not match the scaffold's legacy request contract.
- The historical DynamoDB schema and Python write shape conflict; deployed schema remains unknown.
- Lowercase portal source can display successful synchronization without checking HTTP success or verifying persistence.
- Main and recovery branches contain distinct uppercase/lowercase index paths; preserve both when inspecting.
- A recorded successful GitHub Pages workflow is not AWS Lambda deployment evidence.

See [audit and dependency map](../../audits/recovery-2026-09-24/AUDIT.md), offline tests, and inventory comparison tool. Nineteen characterization tests pass, including known-gap assertions. This is not remediation or production acceptance.

No AWS resources, endpoints, secrets, live data, or historical canon sections were changed. This additive delta does not supersede September 23 observations with guessed live state.

Next: reconcile the protocol contract, prepare separate fail-closed fixes, and obtain a sanitized read-only source/package/function evidence chain. Preserve the existing unresolved Gmail, Hugging Face, Companion, and deployment states.
