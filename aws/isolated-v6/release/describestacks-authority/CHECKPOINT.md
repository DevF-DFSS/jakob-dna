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
