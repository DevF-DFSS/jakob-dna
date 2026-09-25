# Same-account containment candidate — 2026-09-25

Status: DOCUMENTED / OFFLINE TESTED; NOT DEPLOYED. Parent is reviewed PR #11
`42cf882bae2fe9ab7020c8c62c7cea189525bc64`. This is PR #12 work, not a revision of
historical PR #9/#10/#11 evidence. No new AWS inventory was taken. The interrupted
local file snapshot survived; no local Git repository, staged changes or commits
existed. It was continued in place, without reset, cleanup or reconstruction.

## Threat model and evidence

Contain ordinary known legacy principals and new runtime/publisher roles while
retaining an explicitly approved recovery/deployment path. Same-account policy
controls do not constrain account root or an administrator able to replace the
policies, change role membership/trust, pass deployment roles, or operate an
existing stack under its service role. The new deployment role intentionally
manages the candidate and is trusted for it; it is not trusted for bootstrap or
legacy resources. Compromise of that role can change the candidate's protections.
This is not account-level isolation. There is currently no second account.

`legacy-identities.json` distinguishes PR #10 observed role paths from the
user-supplied us-os-gateway name whose current full ARN/path is unverified. Both
root/nested user paths are covered. The other names are
DFSS-ColdStart-role-io8kh35x, us-os-brain-role-c7v6jeb1 and
JakobLambdaExecutionRole. Conditions use the IAM role ARN for role sessions.
This list is not a current or exhaustive principal inventory. No policies on
these existing principals are changed. Denies use aws:PrincipalArn; no
NotPrincipal/Deny pattern is used. [AWS global condition-key guidance](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html).

## Bootstrap, then runtime (design only)

1. Independent human review must approve an existing recovery role under
   `/jel-v6-approved/`, same account, distinct from all denied principals, and
   its effective identity/SCP/boundary rights. No default or invented ARN exists.
2. A future separately authorized bootstrap operation must run as that recovery
   role **without an alternate CloudFormation service role**. Bootstrap creates
   a generated-name private/versioned S3 bucket, bucket policy, empty HTTP API,
   publisher role/boundary, runtime boundary, and deployment role/boundary.
   Bucket and protective bucket policy are retained on replacement/deletion.
   There is no artifact, runtime Lambda, route or stage in bootstrap.
3. After reviewing bootstrap outputs, the approved recovery actor may assume the
   new publisher role for a later explicitly authorized upload. Publisher can
   PutObject/GetObjectVersion and inspect location/versions only in this bucket;
   it cannot delete objects, edit policy, or write legacy storage. Pin an immutable
   object version and reviewed SHA. No uploader is included or executed here.
4. Runtime imports this bootstrap's bucket, API ID and runtime boundary. Its stack
   name MUST equal bootstrap RuntimeStackName. Use only the exported dedicated
   deployment role. It creates the new table, execution role, function/version/
   alias, JWT authorizer, exact two routes, sandbox stage and sanitized monitoring.
   Stage depends on full Lambda policy. This removes the artifact/API circularity.
5. Rollback must preserve bootstrap, artifact versions and retained table. Do not
   delete protective policies while protected resources remain in use. Changing
   bootstrap names or boundaries needs separate review; it is not a runtime update.

A policy attachment is not atomic with every resource creation: the S3 bucket
exists before its bucket policy and the function before its resource policy.
No ingress stage exists until its policy, but broad existing identity permissions
could act during creation. Pre-activation control-plane isolation and creation
windows remain blocking review items. Do not upload sensitive artifacts or enable
bindings merely because a stack can be created.

## Enforcement matrix

| Surface | Candidate enforcement | Limits / required proof |
| --- | --- | --- |
| Lambda invocation | One AWS::Lambda::ResourcePolicy on unqualified function, covering function and all versions/aliases. Explicit non-Gateway invoke deny; wrong source account/API/stage/path deny; only POST /v6/events and GET /v6/senders/{sender}/events/{event_id} allow qualified sandbox alias. No Permission or Function URL resources. | Receipt wildcards represent route parameters, not input validation; exact route definitions and host parser remain required. Service context, alias coverage and actual JWT enforcement need live proof. |
| Legacy Lambda access | Explicit action list from AWS's supported resource-policy APIs, including InvokeFunction/Url, DeleteFunction, UpdateFunctionCode and alias operations. Every listed action and principal tested synthetically. | UpdateFunctionConfiguration, Put/Get/DeleteResourcePolicy, Add/RemovePermission are not listed as resource-policy protected in the reviewed guide. No protection for those is claimed. Existing legacy identities' effective rights to these paths MUST be assessed/constrained separately before deployment; new role boundaries do not retrofit legacy identities. |
| New DynamoDB | Table ResourcePolicy explicitly denies known legacy principals dynamodb:* on the exact new table and index ARNs. Execution identity policy and boundary retain GetItem/PutItem on the table only. | Applies to actions supported on these resources, not account-level DynamoDB APIs. Unknown principals/administrators and policy replacement remain separate review. No index, scan/query/update/delete data path is introduced. |
| Artifact S3 | New generated-name bucket, all four public-access blocks, BucketOwnerEnforced, AES256, versioning. Bucket policy denies known legacy identities, denies non-whitelisted principal ARNs, and requires TLS for non-service actors. | Whitelist is deployment role, publisher role and approved recovery role. Identity permissions still required. Root has documented bucket-policy recovery powers; no root containment claim. Actual Lambda/CloudFormation artifact retrieval needs proof. |
| Runtime role | Bootstrap-owned boundary allows only exact table Get/Put and exact log-stream Create/Put. Explicit denies outside these actions/resources resist same-account session grants. | No ability to edit boundary/trust or assume/pass roles. New logs/table only; startup bindings still empty. |
| Deployment role | Identity policy plus boundary scope lifecycle operations to the exact new function, table, role, API children, log group, alarms and artifact versions. Explicit outside-resource/action denies. CreateRole requires exact immutable bootstrap boundary; PassRole requires new runtime role + Lambda service. | Can edit candidate inline role policy but cannot change its boundary or bootstrap resources. Get*/List* Lambda metadata and *Alias lifecycle patterns are limited to this new function; iam:GetRole* limited to its new role. DescribeLogGroups is the sole wildcard-resource Allow because that metadata API has no resource-level scope. |

Lambda resource-policy action support and required PutResourcePolicy dependencies
are taken from the [Lambda resource policy guide](https://docs.aws.amazon.com/lambda/latest/dg/access-control-resource-based.html).
Deployment IAM includes AddPermission/RemovePermission because AWS requires them
for full-policy management, **not** to create legacy Permission resources. IAM
cannot infer our template-only convention from those dependency grants. The
trusted deployer can change the new policy; independent review controls its use.
The supported action list is explicit in `tools/isolation_policy.py`, not lambda:*.

[AWS IAM evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html)
places explicit Deny above Allow. Boundaries do not grant permissions. Our finite
model tests selected statements and synthetic context only, not full IAM/service
semantics, SCPs, session policies, context availability or effective authorization.
The [DynamoDB guidance](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/rbac-best-practices.html)
explains why a narrow new identity role alone would not block broad legacy grants.

## Recovery and deployment are not silently assumed

Recovery is excluded from the bucket deny only if its approved ARN is supplied;
that exception grants no rights. It needs independently reviewed bootstrap IAM,
CloudFormation, S3 policy and recovery rights. The new publisher/deployer cannot
edit their own bootstrap boundaries. New function non-Gateway invoke deny also
blocks recovery/deployer direct invocation intentionally; management remains
available through their separately granted rights. Tests prove absence of these
specific denies, not a live recovery drill.

CloudFormation service-role trust uses the documented service-only trust, without
inventing SourceArn/SourceAccount keys for ordinary stack role assumption.
The operator must separately scope PassRole and stack lifecycle permissions,
including existing-stack operations that can reuse a service role.
[AWS CloudFormation service-role guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/least-privilege-cloudformation/service-roles-for-cloudformation.html).
No existing operator policy or us-os-gateway is changed. If effective legacy
privileges can assume/use the recovery/deployment path, deployment remains blocked.

## CloudFormation discrepancy: CONFLICT / 🐈📦 UNRESOLVED

On 2026-09-25 the [CloudFormation reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-lambda-resourcepolicy.html)
lists FunctionResourceArn in syntax/properties, but ResourceArn in examples and
Ref identity. [Official CDK 2.268.0](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/CfnResourcePolicy.html)
uses resource_arn. Locally pinned cfn-lint 1.40.2 has ResourceArn + PolicyDocument
in its eu-west-1 schema, but no Lambda::ResourcePolicy in its us-east-1 schema.
The candidate uses ResourceArn to match examples/CDK/local schema **provisionally**;
this does not establish the deployable property form in an approved region.

Both templates are linted in both installed regional schemas without network.
Raw findings are retained in infra/offline-validation.json. The old IAM catalog
also does not recognize the new policy-management actions. No errors are suppressed
or patched away; auxiliary region selection is not region approval. W6001 records
the deliberate runtime output of the imported API URL. AWS's
[August 2026 launch](https://aws.amazon.com/about-aws/whats-new/2026/08/aws-lambda-full-iam-resource-based-policies/)
establishes capability, not consistency of this schema or deployability.

Ordinary build rejects lint failures. `--diagnostic-only` permits a reproducible
review artifact and records cloudformation.passed=false and deployment_authorized=false.
The release validator rejects such provenance. No deployment tool is included.
The v1 release record does not yet approve bootstrap identity/parameters/hashes;
a separately reviewed isolation release record linking BOTH templates, exact
stack names, recovery role, exports, object version and policy review is mandatory
before activation. Do not treat the old manifest as sufficient approval.

## Remaining gates

🐈📦 Authoritative schema/property resolution and approved region; effective IAM/
SCP/boundaries and unsupported management paths; legacy principal completeness;
protected bootstrap creation windows; approved recovery role and restricted
PassRole/stack access; account/region/cost decisions; actual provider and Gateway
JWT/context enforcement; new bucket artifact retrieval; real DynamoDB durability/
concurrency; monitoring/throttling delivery; bindings; release convergence and
bootstrap/runtime release attestation; separately authorized deployment/recovery
exercise; production migration. No semantic state layer is introduced.
