# PR19 validation lineage

## Executed at eb7359c44412475ee4c08e1b3e06cb08047ed361

Command: Python 3.13.7 `-B aws/isolated-v6/tools/ci_evidence.py /private/tmp/pr19-validation-prepublish` using the preserved activation-venv. Existing entry points run under denied sockets/SDK HTTP/credential discovery. No AWS credentials or live calls.

- 326/326 tests; zero failures/errors/skips. 255 inherited + 25 policy/topology + 11 host + 21 plan + 14 template.
- Historical and new phase structural/security checks passed.
- Two diagnostic ZIPs and provenance files byte-identical within local runner.
- 106/106 source-input hashes verified against that exact Git tree.
- cfn-lint 1.40.2 unchanged, no suppression. Historical fixtures: us-east-1 exit6 (6 W3037, E3006, W6001); eu-west-1 exit4 (6 W3037, W6001). New phase composition: us-east-1 exit6 (6 W3037, E3006); eu-west-1 exit4 (6 W3037). W6001 disappears from new composition because new AliasArn output is exported/used; no linter rule disabled. Full evidence command exits1 because lint remains failing; both diagnostic builds exit0. Not release-ready.
- Artifact `2a3179938387f995432a1202f5f85bec2eefe06462bb75d7eaf5651334832de6` vs PR18 `964269c33919dbbb3e46f4f12b2685dde834a001bdeffab9261fcc86d6beced3`: new phase_host.py and packaged capability.json explain runtime change.
- Historical template `1aa415937400720cd7804c7ad04d3358a489f2e0b2e04f5dc5e9b2014cbc43fa`, bootstrap `c7b10b8fd7854ccc791b6cfa5663ee76ea83607d974fb4177bc4dfefd8599449`, bindings `1e1612ea14057a336f9ef5d66df10b8f569940e1e673c9c92fdf260609d78c6b` unchanged from PR18.
- New phase template hashes: bootstrap `10dbf471abf2ebe4be87d8dcbac588c3cfbf500c2f8821e962b730c6cde99024`; authority `7d7a708795e8451d5d638f0339c0618f37c6ff0ac4bbadcee9632ee6adc99644`; runtime `551cb09f68be134fd175cac1dd0e3357e032443a262efc535a7217e7c6d02d98`; ingress `62e9e40f340fd3aced6d1cd13ca62082b0331089627deb691f5c06581c0b1892`.
- Capability `c9cfa17f7578b4197cf7c677135e1caca596d22931d47263fa40a2e19cd865c6` is CLOSED.
- Historical local provenance at this checkpoint: `dadeb5322e5512b91f70807583c04f6e18c512941842bab4fc36a9c2d2895105`. It is not final-head provenance.

## Final coordinate reconciliation rule

This record is intentionally a committed prior-coordinate observation, avoiding a self-referential source hash. After the containing checkpoint is committed, rerun the full evidence entry point against its final HEAD. Record exact resulting source-input count/provenance hash and actual final-head CI run in the PR body. This file is never evidence that a later commit was run. GitHub workflow object's head_sha outranks any prose. Local and GitHub evidence remain distinct; neither authenticates AWS effectiveness or DevF authorization.

Known test setup failure: first inherited package test could not find the local wheelhouse. Seven existing PR18 wheels were copied only after SHA-256 verification against unchanged lock; no network acquisition/upgrades. Subsequent suite/builds passed. A preliminary policy-model test exposed action/resource cross-product overbreadth in maximum construction; code corrected and original negative retained.

No deployment, resource/credential mutation, live invocation, data access, paid agents or PR merge occurred. deployment_authorized=false.
