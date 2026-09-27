# PR19 authority / phase design decision

Status: offline implementation in progress; no AWS calls or installation. Parent PR18 and its 32 paths remain historical evidence. Sources and retrieval hashes are in sources.json. This decision does not close A1/A2/A3 live gates.

## A1 selected mechanisms

1. **Source-bound data authority.** Add ArnEquals `lambda:SourceFunctionArn` to the GetItem/PutItem identity Allow and an explicit ArnNotEquals Deny in the maximum boundary. The intended unqualified function name is already deterministic (`${RuntimeStackName}-v6`), so construct its ARN from partition/account/region/name; never use a Function GetAtt that would create a role/function dependency cycle. No such condition is put in a table/resource policy. Logs remain a separate statement. AWS documents injection for SDK calls inside the execution environment and specific log/X-Ray/EFS service calls; not all service-generated calls carry the key. Candidate uses in-function low-level DDB Get/Put and no replication/VPC/layer/capacity-provider path. Public operation catalogs also list conditional ancillary actions; no unused replication/layer privileges are added merely from the catalog.
2. **Association-bound PassRole.** Exact execution role Resource + StringEquals PassedToService=lambda.amazonaws.com + ArnEquals AssociatedResourceArn=intended unqualified function. Maximum boundary explicitly denies wrong/missing service or association. IAM documentation says services supporting PassedToService also support AssociatedResourceArn; Lambda operation catalog supplies Lambda PassedToService. Actual CloudFormation request context remains a B-class service-path test. Missing context fails closed, never falls back to an unconstrained grant.
3. **Independent legacy fence.** A proposed identity-side Deny attachment targets only new function/qualifiers, role/boundary/stack namespace, exact generated HTTP API and new table/bucket. Deny passing V6 roles from ordinary legacy identities at all, rather than granting a conditional pass to them. New-stack policies cannot remove existing identity Allows. HTTP APIs do not support the REST API resource-policy feature; management protection must be installed on relevant existing identities/boundaries or other applicable account controls by a separate authorized actor. An API with unknown generated ID is inert until exact-ID fencing is read back; creating routes/integrations/stages is a later authority.

AWS basis: [source function](https://docs.aws.amazon.com/lambda/latest/dg/permissions-source-function-arn.html), [IAM condition keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_iam-condition-keys.html), [missing-key operators](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition_operators.html), [HTTP API feature comparison](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html). SourceFunctionArn is a credentials-context control, not a network-origin attestation: stolen credentials issued to the intended function may retain that context. Changed intended code can use its intended data authority. Management containment remains necessary.

## Attack model before implementation

| Attack | Proposed result | Limit / required installation |
|---|---|---|
| Alternate Lambda receives V6 role | Source-bound DDB Deny; permitted deployer PassRole association also fails | LOCAL_STATIC_ANALYSIS proposal; B live propagation/evaluation test |
| Wrong service / missing or qualified association | Fail closed in deployer boundary | Actual CF context unobserved |
| Direct role credentials without source key | Fail closed for DDB | Does not prove denial of stolen intended-function credentials carrying its source context |
| Wrong role | No V6 runtime identity grant; boundary/resource graph must be evaluated | Source key alone is not a principal allowlist |
| Execution policy changed | Maximum boundary still limits data; ordinary deployer cannot edit boundary | Boundary writer/administrator is trusted installation authority, not contained by itself |
| Intended function config/code replaced | Still open if legacy mutation rights persist | Requires future identity fence before creation; source key is not a code hash |
| Gateway routes/authorizer/integration changed | New runtime deployer has no API authority; proposed legacy fence denies it | Future fence attachment/read-back mandatory; trusted ingress deployer can still change its own domain |
| Creation / rollback window | Independent pre-installed fence persists outside candidate lifecycle; no stage in runtime stack | No automatic policy installation or verified rollback here |
| CF role reuse via another stack | Operators scoped to exact stack and RoleArn; role alone cannot authenticate template contents | AWS warns authorized stack users can reuse service role; all stack mutators and PassRole paths must be contained |

## A2 topology selection

A separately approved **existing non-root authority establisher** is the unavoidable first writer. Its trust/federation is not invented. It installs exact new boundaries/roles and the separate legacy fence under a reviewed, expiring operation. A policy author able to replace maximum policies is a trusted installation actor; a boundary cannot inspect another policy document's semantics. This trust is explicit and outside normal recovery, not recursively solved by another self-created role.

Normal roles: narrowly scoped CloudFormation stack operators (bootstrap/runtime/ingress), distinct CF service-role domains, S3-only publisher, runtime execution role, and a read/rollback-only recovery operator. Temporary installation/emergency authority is not a standing recovery grant. Proposed grants have an absolute expiry Deny as well as trust expiry and one-hour maximum sessions; trust removal alone does not revoke existing sessions. Date expiry can also stop rollback, so the recovery procedure must allocate a separate freshly approved repair window rather than silently extending itself.

The installation specification must identify exact trust, maximum policy, PassRole/stack association, expiry/removal, and retained-resource behavior. No existing root/user/role is modified. No automatic federation/client selection. [CF service roles](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-iam-servicerole.html) and [role-session revocation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_revoke-sessions.html) define limits; real trust/session evaluation remains B.

## A3 structure selected for implementation

Derive a new phased composition from existing reviewed generators, retaining the old combined templates as explicitly historical comparison fixtures. Extend existing build/static validation to select and hash the phased composition, not silently use the old combined deployment path.

- Inert bootstrap: empty HTTP API + private/versioned retained artifact bucket/policy; no stage, route, Lambda or execution role. Only independently approved temporary bootstrap authority can create these.
- Authority installation: exact generated API ID enables the separate fence and new maximum boundaries/role domains. It does not create a function, table or stage. Trusted installation requires an external first-write decision.
- Contained runtime: function/table/role/full Lambda policy, no API management resources. Runtime CF role cannot create a stage. Packaged phase capability defaults CLOSED before SDK construction. Unconfigured provider is not replaced by invented live values.
- Configured synthetic ingress: separate ingress composition and independently scoped ingress actor; exact test principal tuples and a bounded packaged time window checked by the host before forwarding to unchanged ingress. A label cannot prove payload semantics; the guarantee is a bounded allowlist of independently approved test identities, not detection of all sensitive data.
- Reviewed sandbox: a new immutable capability/artifact and separate phase decision after B evidence. No environment flag or approval string unlocks it. A future authenticated reviewer/executor is outside this candidate, so offline plans always return deployment_authorized=false.

Release transitions must bind source/parent, all templates, packaged capability/bindings/artifact, S3 version, actual stack/role/API/provider context, exact mutation/resource class, evidence freshness, stop/quarantine and approval coordinate. Ordinary operator permissions must not span bootstrap/runtime/ingress domains. A deliberately trusted installer/activator can change the domain it controls; exact consent is not cryptographically supplied by an IAM RoleArn condition or by this offline planner.

## Preserved unknowns

All PR18 B groups remain open: real JWT/projection, effective IAM/service context, negative invocation/data fences, artifact delivery, handler/rollback/delete/PR16 DescribeStacks, transition behavior, quotas/logging/cost. No validator upgrade or speculative DescribeStacks grant. No live installation/authorization implied by a passing local decision table.
