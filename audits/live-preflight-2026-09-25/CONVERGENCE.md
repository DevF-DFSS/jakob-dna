# Integration and release-convergence map — 2026-09-25

✅ VERIFIED from GitHub PR metadata, changed-file contents and commit parent lists, captured in `lineage.json`. All PRs #2–#9 were open/unmerged when inspected. Branch number is not ancestry. No merge/close/rebase/force push was performed.

```text
main 94401ae
└─ #2 recovery (four commits) 6cc3649
   ├─ #3 characterization 8b42fd0         [evidence sibling]
   ├─ #4 remediation cbe8eef             [superseded implementation candidate]
   ├─ #5 compatibility a4c2c26           [historical evidence sibling]
   └─ #6 design 8ec33ed
      └─ #7 provider-neutral 401893f
         └─ #8 AWS candidate d1f24c2
            └─ #9 activation f7acf43
               └─ #10 current preflight [docs/evidence only]
```

| PR | Head and actual base | Contents / canon disposition |
|---|---|---|
| [#2](https://github.com/DevF-DFSS/jakob-dna/pull/2) | 6cc3649a9801fa7a5f7e14f399e8725190180083 → main | Recovery foundation and prior canon; ancestor of all later work. Four commit parents recorded in JSON. Review as foundation, not deployed truth. |
| [#3](https://github.com/DevF-DFSS/jakob-dna/pull/3) | 8b42fd0ebc5850a82e2629006677ad41900c1748 → jakob-recovery-2026-09-23 | Characterization audit/tests + canon. Preserve baseline unchanged; bring evidence paths into future canon with historical labels. Its gaps are intentionally characterized, not current V6 expectations. |
| [#4](https://github.com/DevF-DFSS/jakob-dna/pull/4) | cbe8eeff045802a305a98b78d743328f17403dcf → recovery | Legacy Lambda/protocol remediation, tests/canon. Not ancestor of #7–#9. V6 selectively reuses reviewed integrity behavior; does not merge this Lambda wholesale. Preserve branch/head as historical candidate. Do NOT blindly merge conflicting persistence/runtime changes. |
| [#5](https://github.com/DevF-DFSS/jakob-dna/pull/5) | a4c2c2666345e663e9f0678878b3c0e1abcc6a9a → recovery | September 24 live compatibility snapshot, audit tooling/tests/canon. Sibling, not ancestor of #6. Import evidence paths unchanged with date; do not rewrite with current findings. |
| [#6](https://github.com/DevF-DFSS/jakob-dna/pull/6) | 8ec33eda8a75e1994257456c3efa1985a31039e7 → recovery | Isolated runtime/storage design, model/tests/canon. Ancestor #7–#9; design-only status preserved. |
| [#7](https://github.com/DevF-DFSS/jakob-dna/pull/7) | 401893f24e784795efa900ea32554ab1ca61e64c → codex/isolated-v6-design-2026-09-24 | Provider-neutral core and tests/canon. Supersedes #4 as intended new-runtime implementation direction, not a deployed replacement. |
| [#8](https://github.com/DevF-DFSS/jakob-dna/pull/8) | d1f24c260d0b5dd00dafae39fc4e585cf496780c → codex/isolated-v6-offline-2026-09-24 | AWS store/host/IaC/build/security/tests/canon. Inactive composition subsequently extended by #9. Keep historical artifact/provenance. |
| [#9](https://github.com/DevF-DFSS/jakob-dna/pull/9) | f7acf43f1f4a87fbbcda068a94a5037427750b24 → codex/isolated-v6-aws-candidate-2026-09-24 | Gateway claims/SDK/composition/config/build updates. Current offline candidate, blocked for activation. Does not cryptographically authenticate direct invocations. |
| #10 | parent f7acf43… → codex/isolated-v6-activation-2026-09-25 | Current preflight, delta, identity/cost/IAM findings and convergence map. No implementation fix, deployment or merge. |

## Future release sequence (proposal, not executed)

1. Record exact head SHAs, PR review decisions and test reports; preserve every historical branch. Review #2 foundation against current main. Do not rebase/squash the historical evidence branches merely to make the stack look linear.
2. Use a separate release-convergence branch at reviewed #9/#10 ancestry. Bring #3 and #5 evidence-only commits by reviewed merge commits (or exact path cherry-picks with origin SHAs explicitly recorded if ancestry cannot be retained). They are siblings and are NOT already included by merging #9. Keep audits and canon deltas dated; resolve any index/README conflicts manually rather than replacing historical facts. Their current file sets do not modify V6 runtime.
3. Preserve #4 unmerged as an alternative historical implementation. If useful documentation/tests are selected, review paths individually and record source SHA; do not introduce its legacy Lambda or normalized userId/timestamp persistence into the isolated core. Do not mistake its integrity fix for a proven live deployment.
4. Review #6→#7→#8→#9 chain in order, preferably preserving commit ancestry when eventually integrating. #9 extends #8 composition; it does not authorize removal of design/evidence/core. Earlier branches remain available after any future approved integration.
5. Address preflight blockers in separate implementation PRs on the convergence branch: account isolation decision, quota strategy, provider claim profile, approved registry, artifact/deployer/monitoring design. No silent relaxation of nbf/audience or wildcard IAM. Re-run offline tests, static IAM/CloudFormation checks, dependency hashes and two-build reproducibility against final inputs.
6. Freeze ONE source commit, approved parameter manifest, registry version/hash, template hash, dependency lock hashes, version/deployment identifiers and artifact SHA/object version. The immutable artifact must be traced to that commit. PR #9's previous SHA is not the hash for future modified inputs. Release review compares the final tree against the current legacy-resource exclusion list.
7. Only after a separate explicit authorization: provision new isolated sandbox and run defined positive/negative identity, direct-invoke, persistence/retry and operational tests. No legacy caller cutover. Rollback before deployment is simply retaining the existing candidate; after a future sandbox deployment, disable only new ingress/roll back only new alias to a reviewed compatible version, retaining new event data and evidence. Cleanup of retained/protected resources requires its own decision.
8. Production/caller migration is a later review with consumer schema/auth compatibility and rollback proof. Convergence does not prove IAM, cryptography, durability, account quotas or $0 cost.

🐈📦 UNRESOLVED: final main integration policy/reviews, release commit/artifact, selected IdP, real AWS enforcement, approved account/region, concurrency decision, operational budget, deployment authorization and production migration.
