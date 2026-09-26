# PR16 interruption checkpoint — 2026-09-26

State: **RECOVERY COMPLETE; RESEARCH NOT YET COMPLETE**.

- Branch: `codex/v6-describestacks-authority-pr16`
- Worktree: `/Users/devonflack/Documents/Codex/jakob-pr16-work`
- Exact parent and starting HEAD: PR15 `a9de8ce6a646520ad1548b86bd97af9669c5ab27`
- At recovery: staged files none; unstaged files none; untracked files none; local commits after parent none.
- Local branch/worktree survived the previous usage interruption. Managed-worktree tool had returned `Not a git repository` from the separate non-Git chat directory; subsequent manual `git worktree add` succeeded. No research/checkpoint artifact survived before this file.
- `git ls-remote` failed to resolve github.com in this turn. Remote PR16 branch existence is **UNVERIFIED**; do not interpret DNS failure as an absent branch.
- This checkpoint is the first local PR16 change. After commit, its HEAD is the checkpoint commit; verify with `git rev-parse HEAD` on resumption.

## Inherited evidence, with limits

- PR15 live read-only `DescribeType` observations in us-east-1, us-east-2 and eu-west-1 declare `cloudformation:DescribeStacks` under **delete-handler permissions only** for `AWS::Lambda::ResourcePolicy`. See `../schema-research/registry.json`. This is REGISTRY_DECLARED_REQUIREMENT, not an observed handler call.
- PR15's offline analysis found no `cloudformation:DescribeStacks` Allow in the candidate's new deployment role/boundary. This is LOCAL_STATIC_ANALYSIS, not live effective IAM evaluation.
- PR15 left the specific lifecycle principal, target stack ARN, required resource scope, handler behavior and failure mode unresolved. The candidate has not deployed.
- Current official [DescribeStacks API reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DescribeStacks.html) says a StackName can be supplied and provides a resource-scope example for denying unscoped calls. It does not establish which StackName this provider uses.
- Current official [CloudFormation service-role guide](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html) says CloudFormation uses an explicitly associated service role's credentials for stack operations; without one, temporary credentials from the caller are used. Whether this handler's DescribeStacks dependency executes under the candidate service role specifically remains to be verified.
- Current [resource schema definition](https://github.com/aws-cloudformation/cloudformation-resource-schema) describes handler `permissions` as API permissions used to generate IAM policy templates. This does not prove that each permission is called on every handler invocation.

## Questions still open

1. Is DescribeStacks actually called by the delete handler, or only declared as a possible permission?
2. Which stack name/ID and ARN would it target, and can IAM scope it to that exact new stack?
3. Which credentials execute this provider handler in the current bootstrap/runtime composition? Do rollback/deletion use the same service role?
4. Does the missing grant affect initial create, update, read, ordinary deletion, replacement, rollback, or failed-create cleanup?
5. Are documented IAM condition keys and resource scoping sufficient without widening authority to unrelated stacks?
6. Is the issue a proven blocker or an unresolved lifecycle risk?

## Current turn call ledger

- **AWS service API calls attempted/succeeded:** zero. PR15's three DescribeType reads are inherited evidence, not new PR16 calls.
- Public documentation searches/opened pages: DescribeStacks API reference, CloudFormation service-role guide, resource schema definition. No application data, credential values, or secrets read.
- GitHub remote read attempt: one `git ls-remote` DNS failure; no remote result.
- AWS mutations/deployments: zero.

## Next safe action

First verify this committed checkpoint and push this branch when GitHub connectivity is available. Then inspect authoritative provider documentation/source and CloudFormation/IAM reference for the delete-handler dependency, recording source retrieval times and evidence class. Use read-only AWS calls only if they resolve a specific remaining question; record every attempt. Do not add permission before principal, action context and resource scope are supported by evidence.

**Candidate behavior changed: NO. `deployment_authorized=false`.**

## Evidence collection transition — 2026-09-26

Checkpoint commit before research: `8bc9c50f4a03777a9be83a03644a665ea8848d96`, pushed to origin. Subsequent public-source/static research is recorded in `EVIDENCE.md` and `iam-reference.json`. No new authenticated AWS API calls were made. The registry's delete-only declaration and the candidate's explicit boundary deny are verified at their respective evidence levels. The provider's actual request, principal and target stack remain unverified. Decision: **no permission change**. Next: commit/push this evidence transition; run the existing offline suite/build/validator checks; open draft PR16 stacked on PR15 when coherent. Candidate behavior changed: NO; `deployment_authorized=false`.

## Local validation transition — 2026-09-26

Evidence commit `3b6c8d1f78b67c4418027810d6f3171f4810fbc6` was pushed. Against that exact commit, existing Python 3.13.7 offline tooling ran 255/255 tests (zero errors/failures/skips); static security checks passed; two diagnostic builds were byte-identical; 64 source-input blobs matched the Git tree. Runtime artifact SHA-256: `964269c33919dbbb3e46f4f12b2685dde834a001bdeffab9261fcc86d6beced3`; runtime template SHA-256: `1aa415937400720cd7804c7ad04d3358a489f2e0b2e04f5dc5e9b2014cbc43fa`; bootstrap SHA-256: `c7b10b8fd7854ccc791b6cfa5663ee76ea83607d974fb4177bc4dfefd8599449`. Existing pinned cfn-lint remains failing (us-east-1 exit 6, eu-west-1 exit 4), so combined `ci_evidence.py` returns nonzero by design. No new test was added because no executable behavior changed. Local evidence is not AWS effective authorization evidence.

Next safe action: commit/push this checkpoint, rerun the same Git input/build verification against the new final HEAD, then open draft PR16 stacked on PR15 and inspect independent GitHub CI. No candidate behavior changed. No new AWS API calls. `deployment_authorized=false`.

## Final source provenance transition — 2026-09-26

Public documentation retrieval times and SHA-256 body hashes are recorded in `sources.json`. These were HTTPS documentation downloads, not authenticated AWS API calls. Earlier CI run 36252559383 on `8be77e6` failed only on inherited pinned lint findings; its tests/build/source verification passed. The additional provenance file changes the Git source-input set, so rerun local and GitHub checks against the new commit before claiming final-head verification. Candidate behavior changed: NO; `deployment_authorized=false`.
