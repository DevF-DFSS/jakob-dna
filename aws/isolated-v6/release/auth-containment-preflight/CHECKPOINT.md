# PR17 interruption checkpoint — coordinate established 2026-09-26

- Branch: `codex/v6-auth-containment-preflight-pr17`.
- Parent and starting HEAD: PR16 `dd0df665ea4bd7512e18597001def8bb798e83e5`.
- Worktree: `/Users/devonflack/Documents/Codex/jakob-pr17-work`.
- Recovery inventory: no pre-existing PR17 local worktree, branch, local commit, staged/unstaged/untracked change, remote branch or PR was found. The PR16 worktree was clean and exact HEAD matched the remote branch. Existing PR13–PR16 worktrees were preserved.
- State before this checkpoint: staged none, unstaged none, untracked none. This file is the first PR17 change. After committing, use `git rev-parse HEAD` to discover the checkpoint SHA; never infer a later HEAD from this text.
- Inherited blockers: PR16's `DescribeStacks` delete-handler authority remains unresolved; PR15's pinned cfn-lint 1.40.2 catalog findings remain; real JWT provider, API Gateway enforcement, IAM/SCP/boundary effectiveness, direct invocation prevention, recovery authority and human approval remain unproven.
- Exact objective: establish current evidence for the candidate HTTP API JWT/claim contract and direct Lambda invocation containment, keeping AWS documentation, live metadata, IAM simulation, static tests and human authorization separate.
- AWS service API calls in PR17 so far: **zero attempts, zero successes, zero failures**. Remote Git checks were not AWS API calls. No substantive PR17 security research has started.
- Next safe action: reconstruct exact candidate contract from the PR12–16 source; checkpoint it before narrow public documentation/live read-only research. No deployment, Lambda/API invocation or identity/policy mutation.
- Candidate behavior changed: **NO**. `deployment_authorized=false`.

## Security-contract reconstruction checkpoint — 2026-09-26

Checkpoint commit `d8f5e58ac6e245751341203ab9bbd03c62e9efbd` was pushed. Exact static contract is recorded in `CONTRACT.md`. No AWS API calls have been attempted. Confirmed from source: Gateway JWT routes/scopes and alias integration are modeled; Lambda compares projected issuer/audience/client/subject/token-use/scopes/time/API/stage/alias, then server-owned binding; packaged bindings and release approval are unconfigured. Local checks do not verify JWT cryptography and forged direct invocation remains possible unless AWS authority prevents it. Next: commit/push this reconstruction, then compare current official Gateway/Lambda semantics and perform only targeted read-only AWS metadata calls. Candidate behavior changed: NO; `deployment_authorized=false`.
