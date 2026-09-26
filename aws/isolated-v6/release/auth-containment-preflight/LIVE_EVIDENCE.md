# Narrow live inventory and IAM simulation — 2026-09-26

Evidence class **AWS_LIVE_READ_ONLY** unless labelled IAM_SIMULATION. All requests used the configured AWS connector and were metadata/control-plane reads. Caller identity returned account `083127296577` root; this identity was used for reads only. Candidate account/region approval remains absent. Sampling regions us-east-1/us-east-2 follows PR10's candidate-region evidence; it is not global AWS inventory.

## Live observations

At 16:14:39 UTC, `GetCallerIdentity`, `ListUsers`, `ListRoles`, and `GetApis`/`ListUserPools`/`ListFunctions` in each region succeeded (9 calls). One user exists: `arn:aws:iam::083127296577:user/us-os-gateway`. Three ordinary roles exist: `DFSS-ColdStart-role-io8kh35x` and `us-os-brain-role-c7v6jeb1` under `/service-role/`, and `JakobLambdaExecutionRole` under `/`. Four further roles are AWS service-linked roles for API Gateway, Resource Explorer, Support and Trusted Advisor. No V6 role, function, HTTP API or Cognito user pool was observed in either sampled region. Functions: `DFSS-ColdStart` (us-east-1), `us-os-brain` (us-east-2). HTTP APIs: `DFSS-API` (`kirmld16gb`) and `us-os-brain` (`qjiuor3yak`) in us-east-1; `us-os-brain-API` (`p9qtqpd8mc`) in us-east-2.

At 16:15:39 UTC, targeted IAM user/role policy-name/trust reads and API authorizer/route/stage reads succeeded (20 calls). `us-os-gateway` path `/` has attached `AmazonAPIGatewayAdministrator`, `AmazonDynamoDBFullAccess`, `AWSLambda_FullAccess`, no inline policy. `GetUser` later returned no permissions boundary. DFSS role has `AmazonDynamoDBFullAccess` and Lambda basic policy; us-os-brain role has DynamoDB FullAccess and FullAccess_v2 plus Lambda basic policies; Jakob role has three inline CloudWatch/DynamoDB/S3 policies. No ordinary role returned a permissions boundary. All three ordinary role trusts allow `lambda.amazonaws.com` only. The three observed HTTP APIs have **zero authorizers**; each has one legacy `ANY` route with `AuthorizationType=NONE`. Their stages are existing `$default`, `default` or `v2`, not V6 `sandbox`. These are legacy facts, not an invitation to modify them.

At 16:17:39 UTC, `GetUser` and `GetPolicy` succeeded; `DescribeOrganization` failed with `AWSOrganizationsNotInUseException` (3 calls; 2 successful, 1 failed). This supports "account is not a member of an AWS Organization" at that instant, hence no Organization SCP path was observable for this account. It does not rule out all session/other effective controls. `AWSLambda_FullAccess` default version was v7. At 16:18:17 UTC, `GetPolicyVersion` v7 succeeded (1 call): it allows `lambda:*` on `*`, plus `iam:PassRole` on `*` **conditioned on** `iam:PassedToService=lambda.amazonaws.com`; it also contains unrelated service metadata permissions. The user has no permissions boundary in `GetUser`. A new narrow V6 execution role cannot remove this existing user's identity grants. No policy was modified.

## IAM_SIMULATION: hypothetical future resources only

At 16:16:32 UTC, eight `SimulatePrincipalPolicy` calls succeeded: four principals × two action/resource groups. Lambda actions tested: InvokeFunction, InvokeFunctionUrl, CreateFunctionUrlConfig, DeleteFunction, UpdateFunctionCode, UpdateFunctionConfiguration, PutResourcePolicy, DeleteResourcePolicy, AddPermission, RemovePermission. Resource inputs were hypothetical us-east-1 function `arn:aws:lambda:us-east-1:083127296577:function:jel-v6-sandbox-preflight-v6`, its `:1` version and `:sandbox` alias. A separate PassRole simulation used a hypothetical new `/jel-v6/` deployment role ARN; its placeholder is not a deployed role and is not asserted as the candidate's exact eventual name. No context entries were supplied. **Important simulator limit:** multi-resource responses returned generic `${ResourceId}` evaluation names, so those calls are only a generic-resource indication, not per-qualifier proof.

- `us-os-gateway`: all ten Lambda actions **allowed** in the generic-resource results; PassRole to the hypothetical CloudFormation deployment role **implicitDeny** without a `iam:PassedToService` context value. This does not contradict v7's conditional lambda-service PassRole grant.
- DFSS and us-os-brain execution roles: DeleteFunction **allowed**; other nine Lambda actions **implicitDeny**; hypothetical PassRole **implicitDeny**.
- JakobLambdaExecutionRole: all ten Lambda actions and hypothetical PassRole **implicitDeny**.

At 16:17:00 UTC, one additional single-resource `SimulatePrincipalPolicy` call for `us-os-gateway`, `lambda:InvokeFunction`, and the exact hypothetical `:sandbox` ARN returned **allowed**, with `AWSLambda_FullAccess` as the matched identity policy and no missing context values. This is stronger evidence for an identity-side allow on that hypothetical alias, but still omits the *future* Lambda resource policy, candidate boundary, actual ARN, SCP/session context, and live invocation. It is **not** OBSERVED_LIVE_AUTHORIZATION. No invoke was performed. Account root is outside ordinary same-account containment and was not simulated.

## AWS API call ledger

| Batch UTC | Attempted | Succeeded | Failed | Exact operations |
|---|---:|---:|---:|---|
| 16:14:39 | 9 | 9 | 0 | STS GetCallerIdentity; IAM ListUsers, ListRoles; APIGatewayV2 GetApis ×2; CognitoIDP ListUserPools ×2; Lambda ListFunctions ×2 |
| 16:15:39 | 20 | 20 | 0 | IAM ListAttachedUserPolicies, ListUserPolicies; GetRole/ListAttachedRolePolicies/ListRolePolicies ×3 roles; APIGatewayV2 GetAuthorizers/GetRoutes/GetStages ×3 APIs |
| 16:16:32 | 8 | 8 | 0 | IAM SimulatePrincipalPolicy ×8 (four principals; Lambda action set and hypothetical PassRole each) |
| 16:17:00 | 1 | 1 | 0 | IAM SimulatePrincipalPolicy ×1 (single hypothetical alias InvokeFunction) |
| 16:17:39 | 3 | 2 | 1 | IAM GetUser, GetPolicy; Organizations DescribeOrganization failed: AWSOrganizationsNotInUseException |
| 16:18:17 | 1 | 1 | 0 | IAM GetPolicyVersion v7 |
| **Total** | **42** | **41** | **1** | No mutating or data-plane operation |

One connector script was rejected *before dispatch* because `__name__` access is disallowed. It caused **zero AWS API calls** and is separate from the 42 attempted calls above. No credential values, secret values, token contents, Lambda invocations or DynamoDB items were read. `deployment_authorized=false`.
