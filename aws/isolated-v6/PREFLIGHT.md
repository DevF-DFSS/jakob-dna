# Deployment preflight — not authorization to deploy

- [ ] Approve sandbox account/region, owner, quotas, budget and rollback authority.
- [ ] Review provider compatibility with the explicit claim profile; prove real
      Gateway signature/issuer/audience/time/scope enforcement and malformed tokens.
- [ ] Review ALL identity/resource policies, SCPs, boundaries and PassRole paths;
      prove clients cannot invoke unqualified function, versions or alias directly,
      modify code/configuration, or spoof a Gateway context. Alias grant alone is
      insufficient. Test using separately approved real-account negative tests.
- [ ] Review and package real non-secret principal bindings; confirm version/hash,
      tenant separation, revocation rollout and emergency ingress-disable process.
- [ ] Recheck dependency pins/hashes/licenses and approved supply-chain policy.
- [ ] Run offline tests/lint/build in pinned environment, verify every source-input
      hash against commit, compare two artifacts, sign/retain provenance.
- [ ] Replace logical version/deployment IDs for every release; update references.
      Use Lambda's base64 code SHA parameter, not hexadecimal provenance spelling.
- [ ] Approve artifact bucket/version and deployment-role permissions separately;
      never reuse legacy storage/roles. No uploader/deployer is provided here.
- [ ] Prove real DynamoDB conditional concurrency, strong reads, uncertainty,
      durability/restore and authorization in an explicitly approved sandbox.
- [ ] Add application-status metrics and approved alarm destinations; Lambda
      Errors alone does not capture 4xx/5xx responses. Exercise load/cost/rollback.
- [ ] Confirm no legacy diffs and approve caller migration separately.
- [ ] Obtain explicit deployment authorization. No offline result grants it.

🐈📦 UNRESOLVED: real API Gateway JWT enforcement; actual identity-provider
behavior; effective IAM/SCP/permission-boundary behavior; real direct-invocation
bypass protection; real DynamoDB concurrency/durability; approved AWS account/
region; service quotas/cost; live sandbox deployment; production migration.
