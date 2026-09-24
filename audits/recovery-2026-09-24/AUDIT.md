# JaKoB recovery audit — 2026-09-24

## Outcome and coordinate

Continued issue [#1](https://github.com/DevF-DFSS/jakob-dna/issues/1) from the September 23 canon. This is an offline source audit, not a production verification or remediation. No AWS calls, endpoint invocations, production changes, or credential reads were performed. Historical source was not changed.

Repository anchors read through the GitHub connector:

- `main`: `94401aed89d7b3704dc4800207c32fc68c3bd333`, committed 2026-08-12T03:14:33Z.
- Recovery branch: `jakob-recovery-2026-09-23` at `6cc3649a9801fa7a5f7e14f399e8725190180083`. Its AGENTS.md and all three current-canon files were read. Executable source blob hashes match main. AGENTS.md is absent on main, but present on this branch; this is resolved branch context, not a missing-contract claim.
- `DevF-DFSS/JaKoB` main tree contains only README.md at observed commit `78a8684bc6df2cddf8d86d87b4abda358185dbc3`; engineering checklist #1 is in `jakob-dna`.

Drive sources read: START HERE, CURRENT STATE (updated 2026-09-24T01:47:02.211Z), LINEAGE MAP (updated 01:47:04.295Z), UNRESOLVED STATE REGISTER, CAPABILITY REGISTRY, and SECURITY + REALITY RULES from the September 23 canon. Their historical AWS/Gmail/Calendar/Hugging Face findings remain prior observations. They were not freshly verified here. Shared project conversation was read to identify the intended repositories and recovery sequence.

## Issue #1 checklist evidence

| Checklist | This pass | Remaining limitation |
|---|---|---|
| Executable inventory and dependency map | Documented below | Runtime wiring unverified |
| JEL/envelope/integrity tests | 15 source characterization tests, all pass | Passing gap tests reproduce defects; no security fix claimed |
| AWS resource names | expected_resources.json, 11 rows with evidence classes | Defaults, historical names, prior observations are separate |
| Read-only comparison | compare_inventory.py + 4 tests | No current inventory supplied; all 11 rows unresolved |
| Secret-handling risks | Location/type findings below, values withheld | Not an exhaustive historical secret scan |
| Commit → artifact → deployment requirements | Documented below | Exact Lambda lineage remains 🐈📦 |
| Historical versus live evidence | Explicitly separated throughout | Prior claims do not become current verification |
| Canon updates only on changed evidence | Additive audit delta proposed | No historical sections overwritten |

## Verified source findings

All findings below were observed 2026-09-24 by source inspection, with Python behavior confirmed by isolated tests against matching source blobs. Their applicability to production is 🐈📦 UNRESOLVED until deployment mapping exists.

1. **High — failed integrity does not block persistence.** `lambda_function.py:48-68` computes `integrity_ok` but only protocol drift prevents `put_item`. Matching protocol plus missing or incorrect digest returns 200 and attempts persistence in the fake store. `BUFFER_SHARED_SECRET` is mentioned only in the docstring; the source does not use it for authentication. `SECURITY_AUTH_MODE` is stored as metadata, not enforced. The unkeyed SHA-256 comparison is not proof of sender identity.
2. **High — the digest excludes the fields actually stored.** Lines 48-60 hash `payload`, but persist top-level `key` and `value`. Changing `value` while preserving payload/digest passes the integrity check. No replay protection is implemented in this scaffold.
3. **High — browser password gates disclose the comparison material to clients.** Locations include `index.html:145-151`, `Index.html:774-780`, `letter.html:102-106`, and `letter-perplexity.html:283`. Values are deliberately excluded. Static hidden content/client-side comparisons are not server authorization. The other letter pages also contain client-side unlock code; this pass does not claim all gates are active on deployed routes.
4. **High — portal status can claim success without verification.** Lowercase `index.html:174-200` parses JSON then says persistence is confirmed without checking HTTP status or response semantics. `jesseSync`, lines 211-228, treats any resolved fetch as successful. `jesseRefresh`, lines 204-208, sets ACTIVE after a timer without a network check. These are source findings; no live endpoint was called.
5. **Medium — V6 envelope and runtime input contracts diverge.** Protocol specifies `protocol`, sender/receiver/time, `payload_ref`, and nested `integrity`. Lambda expects an outer protocol header (default `2.6B`), `payload`, and `buffer_sha256`. A V6 document-shaped envelope with the legacy header writes default state rather than validating the envelope. A `JEL-JKB/6.0` header is rejected as drift. There is no standalone V6 parser to test as compliant.
6. **Medium — table schema conflict.** Python writes `key`/`value`; historical SOP lines 48-52 describes `jakob-memory-store` with `userId` and numeric `timestamp`, consistent with the SOP's Node.js example. Same table name does not prove compatible schema. Actual schema, overrides, and deployed code remain 🐈📦.
7. **Medium — malformed requests become generic 500s.** Invalid JSON/non-object JSON fail before a fake write; header names are matched case-sensitively. Input validation/base64 request handling are not implemented as a complete API contract.
8. **Low — excess closing emoji scopes are silently accepted.** `py_emoji_codec.py:30` clamps negative depth to zero. Unclosed opening scopes fail, but extra closing scopes do not. It is a line transformer, not a complete Python lexer or JEL envelope parser.
9. **Source hygiene — case and path portability.** GitHub contains distinct `Index.html` and `index.html`; a case-insensitive checkout may collide. The visual engine filename has a trailing U+2060. Its `jakob_anchor.jpeg` reference is absent from the inspected tree. Do not infer a replacement from similarly named images.

## Executable paths and dependencies

| Path | Entry / flow | Dependencies and effects |
|---|---|---|
| `03_DFSS_Operations/Codebases/lambda_function.py` | handler → asyncio process_event → drift/digest checks → table write | Python 3.11 scaffold; boto3; DynamoDB resource initialized on import; environment settings TABLE_NAME, LOG_LEVEL, DRIFT_CHECK_ENABLED, JEL_PROTOCOL_VERSION, SECURITY_AUTH_MODE |
| `03_DFSS_Operations/Codebases/py_emoji_codec.py` | codec registration → decode → line translation | Python codecs; no network; transforms scope markers into indentation |
| `index.html` | auth → initSession; jesseSync | Browser fetch → API `kirmld16gb`, us-east-1, POST `/session`; GTM external script; client gate; no verified backend mapping |
| `Index.html` | authenticate, switchTab, toggleAnchor, evaluateDrift, copyPrompt | DOM, clipboard and manual checkboxes; external fonts; this separate page does not establish live cloud state |
| Five `letter*.html` files | unlock/display logic | Browser DOM/client gates; narrative deployment claims are historical prose |
| `visual_seed_engine.html` + U+2060 | compileCloudIdentity → fetch anchor → image generation | Tailwind CDN, fonts, browser fetch/FileReader/localStorage; Google image-model endpoint; empty API-key declaration in reviewed source; if populated client-side, key would be exposed in URL/browser context |
| `v10.5/JaKoB_V10.5_Architecture_SOP.md` code blocks | Gmail → Apps Script → Drive → webhook; Node.js handler → PutCommand | Documented examples, not deployed artifacts; Google service authorization and AWS SDK packages unpinned in repository |

No dependency lockfile, test suite, IaC deployment template, or Lambda build workflow was present in the inspected source tree. The new tests use a fake boto3 module before importing Lambda; they cannot contact AWS. No new production boto3 implementation is introduced.

## Resource and security interpretation

`expected_resources.json` includes all named AWS table/bucket/function/API references identified in the inspected text, plus two separately labeled prior Lambda observations from canon. The Python default table has no pinned region and can be overridden. The historical SOP API ID differs from the executable portal API ID. This remains an explicit conflict rather than a guessed migration.

Credential findings are reported by path/type only. Source-derived passphrase values and historical personal prose are not copied into this audit package or fixtures. An empty image API key is not evidence of a leaked working key. Exceptions may log tracebacks in the Lambda; the test harness suppresses that logger, and no production logs were inspected. No claim is made that the full Git history or runtime configuration is secret-free.

## Deployment lineage: evidence required

GitHub reports successful Pages run [31559464672](https://github.com/DevF-DFSS/jakob-dna/actions/runs/31559464672) for `94401aed...`, completed 2026-08-12. That supports a recorded Pages deployment workflow outcome. It does not link Python source to an AWS Lambda or prove today's website/API state. Only the latest five workflow records were inspected.

To resolve exact Lambda lineage, collect a read-only evidence bundle containing:

1. Full source commit SHA, source tree, dependency lockfile, build command/runtime and build job identity/time.
2. Immutable package identity and digest (ZIP SHA-256 or image digest), including layers and generated code. Do not compare a single source-file hash with a packaged ZIP hash.
3. Account, region, function ARN/version/alias, runtime/handler, code digest, last-modified timestamp, and relevant sanitized configuration names. Omit environment values/secrets and signed download URLs.
4. Deployment job/event connecting that package digest to that function/version; API integration and alias mapping connecting the externally used route to it.
5. DynamoDB key schema and IAM policy evidence sufficient to verify dependencies, without data-plane reads or writes.

Matching names or timestamps alone is insufficient. The comparator reports only observations present in supplied inventory, not lineage proof. It deliberately never converts missing records into resource absence. Even a fully described match may be stale; review observation time and account scope.

## 🐈📦 Unresolved register and next coordinate

| Item | Preserved state | Evidence needed next |
|---|---|---|
| Source → deployed Lambda | Could be another name/version/account, undeployed, or historical | Package/deployment evidence chain above |
| Apex runtime name | No current claim of existence or absence | Scoped, dated read-only inventory |
| DynamoDB schema | Source/spec conflict | DescribeTable key schema and deployed function contract |
| API IDs | Executable portal and historical SOP differ | Current integrations/stages/aliases |
| Gmail/Apps Script/Drive bridge | Historical evidence only in this pass | Trigger/code/deployment inventory first; any write test separately scoped |
| Runtime credential risk | Prior canon observation, not re-read | Dependency-aware review without secret values; no rotation performed |
| V6 envelope semantics | Spec/scaffold mismatch | Decide canonical serialization, authenticated sender binding, freshness/replay policy and failure behavior before fixes |
| Hugging Face / Companion | Prior partial inventory / conceptual routing | Separate current verification; no inherited capabilities assumed |

Next engineering action: review this evidence-only change, then implement fail-closed validation and field-bound integrity/authentication under an explicit protocol contract in a separate change. Keep live resource mapping unresolved until the evidence bundle is available. Do not close issue #1 as production-recovered based on these tests.

## Reproduce locally

Requires Python 3.10+ for the existing source syntax; no additional packages are needed for the offline tests.

```sh
python3 -m unittest discover -s . -v
python3 compare_inventory.py inventory.empty.json
```

In the repository, run discovery under `audits/recovery-2026-09-24`. Standalone package source copies contain only the two Python modules and protocol document, with original Git blob identities in source-manifest.json. Test result: 19 tests passed. These are characterization tests, including known-gap assertions, not a claim that security requirements pass.

Inventory input shape: `{"resources":[{"service":"lambda","name":"example","account":"account-id","region":"us-east-1","observed_at":"UTC timestamp","evidence_ref":"sanitized evidence location"}]}`. Do not put credentials or full runtime environment dumps in the input. The included empty input intentionally yields only 🐈📦 UNRESOLVED rows.
