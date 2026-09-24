# Isolated V6 design package

Status: proposed 2026-09-24. Read [DESIGN.md](DESIGN.md) for decisions, resource
requirements, migration/rollback gates and unresolved evidence. This package
contains no handler, AWS SDK calls, infrastructure templates or deployment tools.

Run offline from the repository root (Python standard library only):

```sh
python3 -B -m unittest discover -s designs/isolated-v6-2026-09-24 -v
```

Validation recorded on 2026-09-24: 18 tests passed. The model deliberately accepts
an already authenticated principal tuple and a Python dictionary. It does not
parse wire JSON, validate JWTs, implement the complete canonical envelope schema,
verify API context, enforce byte/length limits, or emulate real conditional-write
concurrency. Malformed objects outside its modeled cases may raise ordinary
Python exceptions. Do not import it into a deployed application.

Covered decisions: missing/unknown/revoked identity denial, sender/receiver/
instruction binding, tenant isolation/injection, missing/failed integrity,
freshness boundaries, fixed-request retry receipts, changed-request conflicts,
distinct IDs at the same time, stale retry receipt recovery, historical timestamp
preservation, no caller/receipt mutation, and basic UUID/profile/time shape.

Required service, parser, IAM, load and rollback gates are listed in DESIGN.md;
passing these tests does not make PR #4 or this model production-ready.
