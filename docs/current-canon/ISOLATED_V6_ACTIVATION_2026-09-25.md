# Canon delta — 2026-09-25 — offline activation readiness

Status: DOCUMENTED / OFFLINE VERIFIED. Source: stacked activation branch from
PR #8 d1f24c260d0b5dd00dafae39fc4e585cf496780c; AGENTS.md, Issue #1 and PRs #3–#8
read. PR #8 was reverified unchanged and no prior PR #9/activation branch existed.
No live AWS state was queried; PR #5 remains historical dated live evidence.

Added a separately reviewable sandbox composition root: validated configuration,
versioned/hashed packaged registry, Gateway claims adapter, pinned low-level
boto3 client, EventStore, clock and provider-neutral Ingress. No bypass/fallback.
PR #7 core and PR #8 DynamoDB adapter preserved. Candidate template selects the
new handler and supplies required identity/registry/alias settings. The packaged
registry stays empty UNCONFIGURED so startup fails closed until reviewed policy
is included in a separately approved build.

Lambda does NOT verify JWT cryptography. Gateway-origin claims are trusted only
under unresolved real Gateway enforcement and invocation isolation. A test shows
fully forged Gateway-shaped data passes structural checks; alias/API/stage checks
are not authentication. Exact claim profile requires single audience, client_id,
sub, access token_use, consistent scopes and exp/iat/nbf strings.

Verification 2026-09-25: 177 offline tests pass (86 core, 41 candidate, 50 new).
Real botocore serialization/Stubber paths exercise typed conditional conflicts,
strong reads and uncertainty recovery. Sockets, SDK HTTP transport and credential
resolver are blocked. cfn-lint 1.40.2 passes locally using installed schemas;
static IAM/CloudFormation checks pass. Neither proves service behavior or effective
AWS authorization. cfn-guard/Autopilot not run.

Runtime pins: boto3/botocore 1.40.35; jmespath 1.1.0; s3transfer 0.14.0;
python-dateutil 2.9.0.post0; six 1.17.0; urllib3 2.8.0. Wheel SHA-256 locks,
packaging metadata and development-tool versions recorded. Build includes locked
runtime wheels and records all input hashes, tests, lint and artifact SHA.
Source attribution still requires independent Git-tree verification/attestation.

🐈📦 UNRESOLVED: real API Gateway JWT enforcement, actual provider behavior,
effective IAM/SCP/boundary behavior, direct-invocation bypass protection,
DynamoDB concurrency/durability, approved account/region, service quotas/cost,
live sandbox deployment and production migration.

Only free public development package acquisition and GitHub repository work used
network. No AWS APIs, console/metadata/account discovery, deployment operations,
stored credential inspection/use/rotation or paid agents/services were used.
