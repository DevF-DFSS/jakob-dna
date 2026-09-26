# V6 authentication and direct invocation enforcement matrix — 2026-09-26

Evidence classes, limits and conclusions are expanded in [CONTRACT.md](CONTRACT.md), [LIVE_EVIDENCE.md](LIVE_EVIDENCE.md), [DECISION.md](DECISION.md) and [sources.json](sources.json). This table is an index; `matrix.json` is the machine-readable source.

| Control | Intended layer | Current result | Next proof |
|---|---|---|---|
| JWT signature and RSA JWKS | API Gateway | SUPPORTED_WITH_CONFIGURATION; no provider configured | Approve RSA-signing OIDC provider, JWKS/key-rotation profile, negative signature sandbox tests |
| issuer iss | Gateway + Lambda | SUPPORTED_WITH_CONFIGURATION; value unapproved | Live provider iss and Gateway reject/accept evidence |
| audience aud | Gateway + Lambda | REQUIRES_PROVIDER_DECISION; Gateway may fallback to client_id, Lambda will not | Actual access token aud and Gateway projection; single string |
| client_id | Lambda | REQUIRES_LOCAL_VALIDATION; client IDs unconfigured | Provider token, approved client list, projected value |
| subject sub | Lambda + registry | REQUIRES_LOCAL_VALIDATION; binding empty | Provider subject stability and approved registry entry |
| access token use | Lambda | REQUIRES_LOCAL_VALIDATION; Gateway has no token-use setting | Provider token_use claim and ID-token negative test |
| route scopes | Gateway + ingress | SUPPORTED_WITH_CONFIGURATION; no provider grants configured | Live wrong-scope negative test on each route |
| scope projection | Lambda | CLAIM_SHAPE_MISMATCH risk for scp-only or differently projected provider | Actual integration event for approved provider, exact list/string test |
| expiration exp | Gateway + Lambda | SUPPORTED_WITH_CONFIGURATION; projected type untested | Expired-token rejection and projected type from live sandbox |
| issued-at iat | Gateway + Lambda | SUPPORTED_WITH_CONFIGURATION; projected type untested | Future-issued negative and boundary test |
| not-before nbf | Gateway + Lambda | SUPPORTED_WITH_CONFIGURATION; optional claim | Absent and present-invalid provider/sandbox tests |
| JWT event claim shape | Gateway projection + Lambda | DOCUMENTED_SHAPE; provider-specific values unverified | Capture sanitized representative event in authorized sandbox |
| API ID | Gateway + Lambda | STATIC_DESIGN_CONSISTENT; no V6 API exists | Actual API ID and direct-invocation negative test |
| stage | Gateway + Lambda | STATIC_DESIGN_CONSISTENT; no V6 stage exists | Live stage/route deployment metadata and wrong-stage test |
| route/method/path | Gateway + core parser | STATIC_DESIGN_CONSISTENT; no live V6 routes | Live route configuration and rejected default/ANY route checks |
| qualified alias | Gateway integration + Lambda context | STATIC_DESIGN_CONSISTENT; context can be forged by direct invoker | Live integration target and alias-only invocation test |
| Gateway source account | Lambda resource policy | EFFECTIVE_POLICY_UNRESOLVED | Live resource policy and Gateway service-context evaluation |
| Gateway source ARN | Lambda resource policy | EFFECTIVE_POLICY_UNRESOLVED | Live service SourceArn on both routes and wrong-source negative test |
| unqualified direct InvokeFunction | Lambda resource policy + IAM | IDENTITY_ALLOW_EXISTS; future explicit deny untested | Effective policy evaluation and authorized negative test |
| published-version direct InvokeFunction | Lambda resource policy + IAM | EFFECTIVE_POLICY_UNRESOLVED; simulator generic-resource limit | Version-specific effective deny and negative test |
| alias direct InvokeFunction | Lambda resource policy + IAM | IDENTITY_ALLOW_EXISTS; no live deny | Alias-specific effective deny and negative test |
| Function URL | CloudFormation absence + Lambda policy | NO_URL_OBSERVED; existing user may CreateFunctionUrlConfig | Live GetFunctionUrlConfig absence and management-path fence |
| code/config mutation | IAM identity/boundary + resource policy only where supported | KNOWN_MANAGEMENT_GAP | Identity-side fence or separate account; live effective evaluation |
| resource-policy mutation | IAM identity/boundary | KNOWN_BYPASS_PATH if future policy can be replaced | Explicit identity-side deny/account isolation before activation; negative management tests |
| PassRole | IAM identity conditions + role trust | SIMULATION_WITHOUT_CONTEXT implicit deny to CloudFormation role; lambda service path allowed by policy | Evaluate exact future role, iam:PassedToService context, trust and escalation paths |
| deployment-role use | IAM trust + CloudFormation service role | UNCONFIGURED; no role exists | Approved non-root operator, PassRole/effective trust and stack-role association |
| known legacy principal access | Lambda resource policy + legacy identity policies | LEGACY_AUTHORITY_RISK; list not complete guarantee | Current all-principal audit, creation window and effective deny proof |
| recovery path | Approved non-root role and human gate | UNCONFIGURED/BLOCKED | Approve/create later under separate authorization; effective-role recovery drill |
| tenant/sender/receiver binding | Lambda registry | FAIL_CLOSED; no approved identity binding | Versioned approved registry and isolation tests against live identity |
| root/administrator override | Account governance | UNCONTAINED_BY_SANDBOX_POLICY | Separate account or explicit risk acceptance and human authority |
| deployment approval | PR13 gate + DevF | BLOCKED; deployment_authorized=false | Fresh authenticated evidence + explicit DevF authorization |

No row is an overall PASS. Gateway documentation, local static tests, IAM simulation, current account inventory and future human authorization remain separate evidence classes. Candidate behavior changed: NO. `deployment_authorized=false`.
