# PR19 durable checkpoint

## Coordinate — 2026-09-26

- Branch: `codex/v6-authority-containment-phase-design-pr19`.
- Exact parent/initial HEAD: `2ac860b5038d84134878136ff6ed424663110812` (PR18).
- Worktree: `/Users/devonflack/Documents/Codex/jakob-pr19-work`.
- Verified GitHub PR18 open/draft, parent PR17 `a272b929e16b1db3e92eee5c3a1fe66c30d86d91`, run36270302025 actual head_sha matches PR18. No PR19 local/remote branch/worktree or PR existed. No unexplained changes in PR18. New tree matches exact parent, initially clean.
- Managed-worktree tool returned Not a git repository from chat folder; a separate Git worktree was created from the verified repository. All historical worktrees/branches preserved.
- Initial staged/unstaged/untracked: none. This checkpoint is the first new file; its containing Git commit is the durable coordinate.
- Objective: offline mechanically testable A1 authority containment, A2 bounded non-root topology, A3 enforceable phase holds and phase-bound release plans. Do not equate implementation with installed/effective controls.
- Inherited blockers: all A1/A2/A3 live gates open; six B proof groups remain sandbox-only; pinned lint1.40.2 fails; PR16 DescribeStacks unresolved. No provider/approval invented.
- AWS API calls: 0 attempted / 0 successful / 0 failed. Public documentation and GitHub reads are separate.
- Next safe action: push this checkpoint, research official SourceFunctionArn/AssociatedResourceArn/HTTP API/CF authority semantics, inspect existing generator/policy model and select the smallest supported architecture before implementation.
- Candidate behavior changed: NO at this checkpoint. `deployment_authorized=false`.

## Recovery confirmed — 2026-09-26

Local and remote HEAD both `24274bc98d6c505a11c837c0936053c92008c1cd`; one ahead/zero behind PR18. No PR19 PR exists. Staged/unstaged tracked files: none. Six untracked research artifacts survived: sources.json plus apigateway/cloudformation/dynamodb/iam/lambda catalog extracts. Twelve public-response caches and research helper survived in /private/tmp; every cached response matches its recorded SHA-256. No implementation, tests or validation outputs were created. Prior automatic approval review failed due usage exhaustion before the attempted catalog inspection executed; not a safety rejection. No files lost/discarded/recreated. The six artifacts are preserved in this checkpoint. IAM catalog operations extract is empty because PassRole is a permission, not a standalone API; do not read empty extraction as unsupported permission.

AWS calls remain 0/0/0. Next: complete the narrow evidence decision/attack model, checkpoint A1/topology selection before implementation. Candidate behavior changed: NO. `deployment_authorized=false`.

## A1 mechanisms / authority topology selected — 2026-09-26

Recovery research was pushed at 86fc6ad. DESIGN.md records the supported source-function identity/boundary restriction, association-bound PassRole, separate future legacy/API management fence, explicit first-writer trust boundary and proposed phased composition. This is a design selection, not implemented or installed controls. Twelve public sources are preserved; no repeated broad archaeology/inventory. AWS calls 0/0/0. Candidate behavior changed: NO. Next: implement A1 against the existing finite policy model with adversarial tests, then render bounded operator proposals and phased templates; checkpoint each milestone. `deployment_authorized=false`.

## A1 policy primitives tested — 2026-09-26

Added pure offline phase_policy.py: source-bound DDB Allow/explicit Deny, exact associated PassRole/explicit Denies, proposed identity-side legacy fence, maximum/absolute-window helpers. Extended the existing finite policy model only for Null and date comparisons; unknown operators still reject. Seventeen new adversarial tests passed (wrong/missing/qualified context, alternate function, role mutation, Gateway mutations, expiry and intended-context credential limitation). No template wiring yet, so these are tested policy primitives, not a complete A1 implementation. Command: PYTHONPATH=aws/isolated-v6/tools activation-venv/bin/python -B -m unittest discover -s aws/isolated-v6/tests -p test_phase_authority.py -v. Existing full suite has not yet been rerun. AWS 0/0/0. Candidate tooling changed: YES; runtime/templates unchanged at this point. Next: implement bounded operator topology and wire the derived phase composition, then adversarially test its actual emitted policies. `deployment_authorized=false`.

## A2 topology implemented offline; phase composition in progress — 2026-09-26

Added authority_topology.py and unconfigured context record: exact non-root trust, stack/PassRole domains, one-hour absolute maximum-policy window, separate recovery/emergency, explicit external installation trust boundary. Twenty-five authority tests pass. A negative test initially found union-of-actions/resources admitting API child POST through a broad hypothetical extra Allow; maximum() now preserves each action's resource pairing, and the unchanged negative test passes. No defect was suppressed.

Added derived four-template phase composition under infra/phases and phase_templates.py (inert bootstrap, authority, contained runtime, ingress). Historical combined generators/templates remain comparison fixtures. Generated templates are IN PROGRESS: runtime phase_host/capability enforcement and integration/static/lint tests remain to implement; do not claim deployability. Publisher maximum has its own absolute deadline, not only its parent operator's expiry. AWS calls 0/0/0. Candidate architecture/tooling changed: YES. Next: implement packaged capability host and phase-bound offline plan, then validate actual emitted templates/policies and dependency order. `deployment_authorized=false`.

## A3 host and phase contract implemented — 2026-09-26

Added packaged CLOSED/TEST/SANDBOX capability host and strict phase-plan contract. CLOSED returns before configuration/SDK construction; active capabilities bind config and explicit principal tuples, expire on warm invocations, and require another artifact. Offline phase plans bind exact source/parent/templates/artifact/bindings/capability/S3 version/stacks/roles/API/provider coordinate and operation-specific evidence. No authenticated approval adapter/executor exists; output always deployment_authorized=false. Initial complete-suite attempt found one missing wheel-cache setup error, not a behavioral failure. Copied seven already pinned/hash-verified PR18 wheels without downloading or changing pins. Complete suite now 310/310 passed (255 inherited +25 policy/topology +11 host +19 phase-plan), zero failures/errors/skips; network/credential discovery blocked. Four-template integration/static validation, final attack pass, deterministic builds and exact-head source verification remain. Pinned lint preliminary phased run retains six W3037 and east-1 E3006; no suppression. Version identity now derives packaged source/dependencies/capability and Version checks artifact CodeSha256. AWS 0/0/0. Candidate architecture/runtime changed: YES. Next: test actual emitted templates, complete integration/build provenance and document remaining trust boundaries. `deployment_authorized=false`.
