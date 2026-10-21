# 🔱 JaKoB Codex Operating Contract

This repository is an evidence-bearing implementation source for the JaKoB continuity architecture.

## Mission
Help turn JaKoB from scattered historical artifacts into a reproducible, testable, portable system.

## Non-negotiable epistemic rules
- Pattern ≠ fact.
- Metaphor ≠ mechanism.
- Architecture ≠ deployment.
- Reference ≠ execution.
- Convergence ≠ proof.
- Newest file does not automatically erase older lineage.
- Preserve uncertainty and provenance.
- If live state is not verified, mark it UNMAPPED or HISTORICAL.

## Safety / production rules
- Never print, commit, log, or copy credentials, tokens, passwords, cookies, or secrets.
- Never place real secrets in examples.
- Do not modify production AWS resources unless the operator explicitly approves the specific change.
- Prefer read-only inventory, diffs, tests, and pull requests before deployment changes.
- If a secret is found in source or configuration, report location/type without reproducing the value.
- Do not treat emoji/JEL tokens as authentication or cryptographic authorization.

## Working style
- Make changes on branches and open PRs.
- Keep commits narrow and descriptive.
- Add tests for executable behavior.
- Separate current verified state from historical documentation.
- When reconciling two sources, record both timestamps and state what evidence resolves the difference.
- Do not delete historical source material merely because it is superseded.

## Current reconstruction model
JaKoB is treated as a portable continuity/orchestration architecture, not one model or one app.

Evidence layers:
- GitHub: versioned source / protocol / implementation history
- AWS: runtime/deployment evidence
- Google Drive: durable historical ledgers and source snapshots
- Gmail/Calendar: historical write-path + boot-anchor evidence
- Hugging Face: external model/experiment node
- ChatGPT/Codex: reasoning, engineering, code review, and implementation nodes

## Current priorities
1. Verify GitHub source → AWS deployment lineage.
2. Build reproducible infrastructure inventory tooling.
3. Add tests for JEL/inter-node protocol behavior.
4. Create a compact recovery seed and capability registry.
5. Preserve unresolved states in a dedicated register.
6. Keep all production-changing actions reviewable.

## Definition of done for a claim
A claim should identify:
- status: LIVE_VERIFIED / DOCUMENTED / HISTORICAL / PRECURSOR / SUPERSEDED / CONFLICT / UNRESOLVED / INFERENCE
- source
- observed timestamp
- verification method
- limitations

When in doubt, preserve the Cat Box: 🐈📦.
