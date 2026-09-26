# PR14 independent execution evidence

The workflow is a non-deploying observer. Local Work execution, GitHub runner
execution, AWS live observations, and DevF authorization are separate evidence
classes. A workflow label or green check authenticates none of the other classes.
PR13's contract is unchanged; GITHUB_CI_EXECUTION cannot satisfy its AWS live or
human-authority gates. Even a locally forged GITHUB_ACTIONS environment variable
can change the display label: provenance must be checked against the actual GitHub
run, repository, workflow revision, event and checked-out commit independently.

Triggers: pull requests changing candidate/core/workflow paths, plus manual
workflow_dispatch. Manual dispatch requires the workflow to exist on the default
branch under GitHub's rules; this stacked draft does not change that branch.
PR runs explicitly check out the PR head SHA, not the synthetic merge ref.
Checkout does not persist credentials. Actions are commit-pinned; Python is
3.13.7. Standard ubuntu-24.04 runner, 20-minute timeout, contents:read only,
no secrets, no id-token permission, no AWS login or service commands. Public-only
job guard avoids enabling paid private-repository execution accidentally.

GitHub documents standard hosted public-repository runner execution as free:
https://docs.github.com/en/billing/concepts/product-billing/github-actions
The repository was independently observed PUBLIC. No caches, artifact uploads,
paid runners/services or AWS resources are configured. Logs and job summary retain
human-readable tests and machine-readable evidence within ordinary run retention.
No durable signed attestation or externally authenticated evidence collector exists.

The workflow invokes existing authorization unittest discovery first (stdlib),
then the existing run_checks.py, validate_offline.py and build.py entry points via
a small orchestration wrapper. The wrapper continues to collect diagnostic builds
after failed lint, but exits nonzero if ANY entry point fails or either artifact/
provenance differs. Known lint failures are neither suppressed nor turned green.
The workflow records commit, Python, exit codes, suite counts, SHA-256 values,
source-input verification count and deployment_authorized=false. Authorization
file counts appear in their separate verbose log. Test/SDK/lint network guards
remain those of the existing tools; dependency acquisition necessarily uses PyPI.

Runtime wheel pins/hashes remain requirements.lock + dependencies.lock.json.
Only official PyPI binary wheels, exact versions, no dependency auto-resolution.
Runtime wheels are installed offline from their verified cache. Validation pins
remain identical to validation-toolchain.lock; release/ci/linux-toolchain.lock
adds SHA-256 for every downloaded Linux wheel and CI requires those hashes. No arbitrary newer version is a
fallback. Acquisition failure means full-suite/lint/build evidence UNKNOWN and a
failed workflow, while the earlier stdlib authorization results remain visible.
Linux-native validation wheels differ from macOS development wheels; versions and
hashes are logged. This does not prove byte-identical validation installations
across operating systems, or equivalence of live AWS registry schemas.

The two builds compare ZIP and full provenance inside the same runner. Source-input
hashes are checked against git show of the actual HEAD. Runtime ZIP portability
across local/GitHub execution is a separately observable comparison; provenance
includes Python/platform execution context and is not presumed identical across
machines. Existing PR12/13 runtime/template/binding bytes remain unchanged.

Remaining UNKNOWN: hosted dependency installation success until a run occurs;
runner/schema drift; live CloudFormation/IAM/JWT/recovery behavior; effective
operator authority; authenticated evidence ingestion and explicit DevF approval.
No workflow result sets deployment_authorized=true. Do not wire generic CI success
into authorization gates. No deployment, PR merge, production migration or semantic
state runtime is introduced.
