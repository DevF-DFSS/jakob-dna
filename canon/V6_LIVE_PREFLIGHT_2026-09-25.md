# Canon delta — 2026-09-25: live preflight and convergence

Source: PR #9 head f7acf43f1f4a87fbbcda068a94a5037427750b24; PR #5 historical head a4c2c2666345e663e9f0678878b3c0e1abcc6a9a. Method: read-only AWS connector metadata/simulation, GitHub commit/file inspection, official AWS public documentation and offline evidence checks. Observation window September 25 11:40–11:48 UTC. Limits and source links reside in the audit README and IDENTITY_COST.md; raw projections/call ledger in evidence.json.

✅ VERIFIED: 22 common runtime/schema/API/policy comparisons unchanged from PR #5. Legacy resources remain evidence-bearing infrastructure. New observation of quota 10 in each relevant region conflicts with candidate reservation 2 under documented unreserved capacity rules. New concrete-ARN simulations allow both legacy roles to Get/Put the proposed V6 table; they do not execute item operations. Organizations reports non-membership; current seven roles lack boundaries. No Cognito pools in enabled regions, no configured HTTP JWT authorizer.

🚫 BLOCKED: PR #9 activation as-is. Concurrency, same-account isolation, real direct-invoke protection, approved provider/profile/bindings, deployment principal/PassRole and new artifact storage are unresolved gates. Mandatory nbf is incompatible with ordinary documented Cognito access tokens and cannot simply be added with the pre-token trigger. No implementation validation was weakened.

⚠️ MIGRATION/DECISION REQUIRED: prefer new sandbox account for isolation, preserving legacy resources; approve exact account/region, identity flow, operational signals and budget. Tiny human test usage may be negligible/within some free allowances; M2M token issuance and retention can bill. No $0 promise.

✅ VERIFIED lineage: #3/#4/#5/#6 are siblings of #2; #6→#7→#8→#9 is the implementation chain. #3/#5 evidence is not automatically included by #9. Preserve #4 as an unmerged historical implementation alternative. Future convergence imports evidence deliberately and freezes one source commit and matching rebuilt artifact, without implying live proof.

🐈📦 UNRESOLVED: real JWT/IdP enforcement; complete IAM/SCP/boundary/direct-invoke behavior in the finally selected account; real DynamoDB concurrency/durability; approved account/region, quota remedy, artifact storage, monitoring, cost/credits/quotas under load; final release commit; sandbox deployment and production migration.

No AWS mutations, Lambda/API invocations, application-data reads/writes, secret-value reads, credential changes, PR merges/closures or paid external agents. Runtime code and historical PRs unchanged. This delta adds evidence; it does not supersede the dated PR #5 snapshot or authorize deployment.

Pattern ≠ fact; reference ≠ execution; architecture ≠ deployment; convergence ≠ proof.
