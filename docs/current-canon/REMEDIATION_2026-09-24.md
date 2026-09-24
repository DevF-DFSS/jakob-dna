# Envelope remediation — 2026-09-24

Status: source implementation and offline regression verification. Deployment:
🐈📦 UNRESOLVED.

Read AGENTS.md, issue #1, PR #3 and its audit, and the canonical V6 transfer
scaffold. This remediation branches independently from recovery commit
6cc3649a9801fa7a5f7e14f399e8725190180083. PR #3 and its characterization tests
remain unchanged as the pre-fix baseline; do not run their known-gap assertions
against this repaired source and interpret the expected failures as regressions.

Changes:
- Reject missing/invalid integrity before creating an AWS client or writing.
- Validate the canonical envelope and bind all nine non-integrity fields to the
  digest, replacing legacy payload/key/value inputs and protocol bypass flags.
- Normalize persistence to userId=sender and timestamp=integer UTC epoch milliseconds,
  preserving the complete validated envelope with an explicit schema version.
- Reject duplicate/conflicting records with a conditional put instead of overwrite.
- Strictly parse API Gateway JSON/base64; return bounded, non-sensitive errors.
- Require explicit TABLE_NAME; importing the module performs no SDK initialization.

The V6 document now contains an additive Lambda persistence profile describing
previously unspecified digest bytes and storage mappings. These choices are
reviewable source behavior, not an assertion about deployed contracts.

Validation: python3 -m unittest discover -s tests -v. SDK construction, table access,
conditional conflicts and failures are modeled offline; no AWS calls were made.
The tests use synthetic identities and references. boto3 is not installed in this
local interpreter, so real SDK marshalling/service integration remains unverified.

Unresolved before deployment:
- Actual Lambda package lineage, account/region and table key schema.
- Sender authentication and authorization: an unkeyed hash cannot establish identity.
- Payload-reference content verification; this implementation stores the reference only.
- Freshness/replay window and multi-event-per-millisecond policy.
- Existing callers, consumers, IAM conditions and any required migration.
- Portal false-success and client password-gate findings from PR #3 are outside this fix.

No AWS mutation, invocation, secret inspection, credential rotation, or data migration
was performed. This does not close issue #1 or promote historical observations into
live verification.
