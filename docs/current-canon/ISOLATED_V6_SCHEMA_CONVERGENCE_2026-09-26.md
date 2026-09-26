# Isolated V6 schema convergence — 2026-09-26

PR15 starts at PR14 `7589d51fd528486533293bd9ba357a220ff28954` and preserves PR12–14 unchanged. See [evidence and complete diagnostic classification](../../aws/isolated-v6/release/schema-research/README.md).

Fresh live read-only CloudFormation type observations agree in us-east-1, us-east-2 and eu-west-1: `AWS::Lambda::ResourcePolicy` uses required `ResourceArn` and `PolicyDocument`. Retain the candidate spelling. The public HTML's `FunctionResourceArn` syntax/property text contradicts its examples and the registries; it remains an AWS documentation contradiction.

All 15 original lint occurrences are classified with evidence: one E3006 and twelve W3037 are TOOLING_LAG, two W6001 are STYLE_WARNING. Separately evaluated cfn-lint 1.57.0 resolves E3006/W3037 and retains W6001. Pinned 1.40.2, templates, policies, validation semantics and runtime remain unchanged. No finding is suppressed. The sampled live registries show no regional discrepancy; global propagation is unproven.

The registry's delete handler declares `cloudformation:DescribeStacks`, absent from the candidate deployment role/boundary. Exact lifecycle scope/credential-context remains 🐈📦 and requires review before activation; no speculative privilege expansion was made.

Local tests/builds, GitHub CI, public documentation, AWS registry reads and DevF authority remain distinct evidence classes. New test/build execution is recorded in the PR15 handoff, not inferred from earlier PRs. Same-account isolation and recovery effectiveness remain unproven. `deployment_authorized=false`. No deployment or mutation is authorized by this delta.
