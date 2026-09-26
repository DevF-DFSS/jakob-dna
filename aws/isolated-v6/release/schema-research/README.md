# PR15 — schema and IAM catalog convergence, 2026-09-26

Parent: PR14 `7589d51fd528486533293bd9ba357a220ff28954`. This is a research/evidence change. Runtime, templates, policies, pins, validation rules, and authorization gates are unchanged. `deployment_authorized=false`.

## Findings and disposition

`classifications.json` enumerates all **15 original PR14 diagnostic occurrences**, including exact JSON paths, messages, region, and supporting evidence. They were reproduced locally against unchanged templates. No diagnostic is suppressed or waived.

| Original finding | Occurrences | Classification | Evidence and disposition |
|---|---:|---|---|
| E3006, unknown `AWS::Lambda::ResourcePolicy`, runtime FunctionResourcePolicy Type, us-east-1 | 1 | TOOLING_LAG | Pinned 1.40.2 lacks the regional schema. Three live registries contain the type; separate 1.57.0 comparison recognizes it. Retain candidate type. |
| W3037, `lambda:PutResourcePolicy` / `lambda:DeleteResourcePolicy`, bootstrap DeploymentBoundary Allow, boundary NotAction, DeploymentRole Allow | 6 per region, 12 total | TOOLING_LAG | AWS API/Developer Guide, public IAM catalog and registry handler permissions all name these actions. Pinned action catalog omits them; 1.57.0 contains them and removes these warnings. Keep actions. |
| W6001, runtime Outputs/SandboxApi/Value/Fn::Sub/1/Api/Fn::ImportValue | 1 per region, 2 total | STYLE_WARNING | Rule explicitly warns about re-exposing an imported output. The candidate uses the imported bootstrap API ID to construct its endpoint output. AWS documents ImportValue with Sub; neither validator reports an intrinsic-function error here. Both versions retain this warning. Leave the intentional output and the failing lint result visible. |

No original diagnostic is established as REAL_DEFECT. No live regional difference was observed in the three sampled regions; this does not establish global propagation. The HTML contradiction below is AWS_DOC_CONTRADICTION, separate from the emitted diagnostics. Classification is not an exemption from release gates.

## Property spelling: registry-supported ResourceArn

The [CloudFormation reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-lambda-resourcepolicy.html) still names `FunctionResourceArn` in syntax/properties, but its examples and Ref description use `ResourceArn`: **AWS_DOC_CONTRADICTION**.

Fresh `DescribeType(Type=RESOURCE, TypeName=AWS::Lambda::ResourcePolicy)` observations at `2026-09-26T13:45:29.451620+00:00` in **us-east-1, us-east-2, eu-west-1** all report:

- PUBLIC, LIVE, FULLY_MUTABLE, default version;
- properties and required fields exactly `ResourceArn`, `PolicyDocument`;
- `additionalProperties=false`, primary/create-only identifier `/properties/ResourceArn`;
- `FunctionResourceArn` only as a schema **definition**, referenced by the ResourceArn property.

Retain **ResourceArn**. This conclusion is based on the live CloudFormation input schema, corroborated by examples and newer validator schemas, not on selecting whichever spelling passes lint. The HTML conflict remains uncorrected. Registry TimeCreated values are retained as metadata, not interpreted as capability launch dates. The response did not supply a numbered DefaultVersionId, LastUpdated or SourceUrl; none is invented.

`registry.json` preserves the returned metadata, property definitions, required fields and handlers. It is a reduced observation, not a byte-for-byte full response. Its call ledger distinguishes **3 successful registry reads**, **3 failed connector operation dispatch attempts** (`describe_type` spelling rejected; not regional absence), and **2 pre-dispatch connector events**. No Lambda policy APIs were called.

## IAM/API names and validator sources

Current official APIs are [PutResourcePolicy](https://docs.aws.amazon.com/lambda/latest/api/API_PutResourcePolicy.html), [GetResourcePolicy](https://docs.aws.amazon.com/lambda/latest/api/API_GetResourcePolicy.html), and [DeleteResourcePolicy](https://docs.aws.amazon.com/lambda/latest/api/API_DeleteResourcePolicy.html). Their request path uses `/2026-07-09/resource-policy/ResourceArn`. The ARN parameter can be qualified or unqualified; the attachment request does not accept wildcards. API existence and input syntax do not prove candidate authorization or alias-policy inheritance.

The [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html) lists IAM permissions: Put requires `lambda:PutResourcePolicy`, `lambda:AddPermission`, `lambda:RemovePermission`; Get requires `lambda:GetResourcePolicy`, `lambda:GetPolicy`; Delete requires `lambda:DeleteResourcePolicy`, `lambda:RemovePermission`. The [public AWS service authorization catalog](https://servicereference.us-east-1.amazonaws.com/v1/lambda/lambda.json) independently lists all three new actions with function resource support. `iam-catalog.json` records exact entries, catalog version and body SHA-256. It was a public documentation download, not an authenticated service API operation. Valid identity-policy action names do not imply those actions are valid inside a Lambda resource policy; existing unsupported-management-path blockers remain.

Pinned [W3037 implementation](https://github.com/aws-cloudformation/cfn-lint/blob/v1.40.2/src/cfnlint/rules/resources/iam/Permissions.py) validates against packaged `AdditionalSpecs/Policies.json`, not a live IAM query. Its [maintenance updater](https://github.com/aws-cloudformation/cfn-lint/blob/v1.40.2/src/cfnlint/maintenance.py) obtains actions from `https://servicereference.us-east-1.amazonaws.com`. Its [schema manager](https://github.com/aws-cloudformation/cfn-lint/blob/v1.40.2/src/cfnlint/schema/manager.py) obtains regional CloudformationSchema.zip files. No updater was run and no packaged data was patched.

Pinned 1.40.2 has a ResourceArn schema in eu-west-1, but none in us-east-1/us-east-2. That packaged regional difference does **not** match today's live registry observations. Local 1.57.0 uses regional indexes pointing to content-addressed schemas: all three point to the same ResourceArn schema. `validator-comparison.json` accounts for both packaging formats and records hashes. No inference of historical regional availability is made from either package.

## Comparative execution; pin retained

| Validator | us-east-1 | eu-west-1 |
|---|---|---|
| Candidate pinned 1.40.2 | exit 6: E3006 + six W3037 + W6001 | exit 4: six W3037 + W6001 |
| Separate 1.57.0 | exit 4: W6001 | exit 4: W6001 |

`pinned-lint.json` and `newer-lint.json` are actual local executions with sockets/credential discovery blocked by the existing entry point. Both static security checks passed. The pre-existing `schema_discrepancy` string in those reports is an inherited constant, not a new registry observation; this document supplies the updated disposition without rewriting historical tooling.

1.57.0 was downloaded from official PyPI into a separate temporary location, installed with no dependency replacement, and run using the existing pinned environment's dependencies. Its wheel/hash are recorded. This is a controlled comparative run, **not** a fully relocked replacement toolchain. No candidate dependency upgrade is needed to correct the templates. A future pin migration must review/lock its complete dependency set and rerun Linux CI; it must not suppress W6001 merely for a green badge.

## Additional lifecycle question, not hidden by lint classification

All three registry schemas declare `cloudformation:DescribeStacks` among delete-handler permissions. The candidate deployment role/boundary do not currently grant that action. **UNRESOLVED:** the exact handler target stack(s), credential context and lifecycle path requiring this permission were not established by these read-only type queries. Missing declared coverage is a concrete deployment/recovery review blocker, not proof of a failed real deletion. No broad CloudFormation permission is added speculatively. Before activation, reconcile the handler permission with the narrow deployment-role design and managed-policy size limit, add the smallest proven scope and regression tests if required, and independently verify the approved recovery path. This question is separate from the original catalog warnings.

## Evidence boundaries and remaining blockers

- Public documentation/catalog: URLs, UTC retrieval timestamps and response hashes in `sources.json` / `iam-catalog.json`.
- AWS live read-only: only the dated three-region type observations and explicitly recorded connector failures in `registry.json`; no account resources, policy contents, secrets or credentials queried.
- Local package inspection/execution: validator comparison and subsequent PR15 test/build results; not AWS effective authorization proof.
- GitHub CI: a separate execution against its exact checkout; report the actual PR15 run, never inherit PR14's pass counts as new results.
- DevF authorization: absent. No result in this directory grants it.

🐈📦 Global propagation, actual handler lifecycle permissions, function/alias enforcement, IAM/SCP/boundary effectiveness, direct-invocation containment, approved non-root recovery authority, identity-provider/live ingress behavior, and final account/region/human authorization remain unproven. The docs contradiction remains visible; the template property form is supported in the sampled registries. Pinned lint still fails. Existing release/authorization gates remain fail-closed. No AWS mutations, deployments, invocations, application data access, policy writes, secret/credential changes, paid agents, or PR merges occurred.
