# 🐈📦 Unresolved State Register

## GitHub → AWS deployment lineage
Source scaffolds exist in GitHub.
Current AWS Lambdas have been inventoried.
Exact source commit/package → deployed Lambda mapping remains UNRESOLVED.

## Apex runtime naming
Historical docs/source refer to Apex/JEL runtime concepts.
Current live inventory previously observed `DFSS-ColdStart` and `us-os-brain`.
Do not infer that a historical `jakob-apex-node` name is live now.

## Gmail write bridge
Historical docs and mailbox evidence strongly support:
`[JAKOB_WRITE_COMMAND] → Gmail → Apps Script → Drive`
Current trigger execution still requires a fresh controlled test.

## AWS secret hygiene
Credential-like runtime configuration was previously observed.
Values must never be copied into repository artifacts.
Rotation/removal should be performed only with a dependency-aware plan.

## Hugging Face
Authentication verified; complete model/dataset/space inventory remains incomplete.

## External Companion / Muse
Older generic Companion concepts are architectural precursors.
They are not evidence that any later specific vendor/product was predicted or integrated.
