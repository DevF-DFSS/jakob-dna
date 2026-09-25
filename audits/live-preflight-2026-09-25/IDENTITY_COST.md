# Identity feasibility and tiny-sandbox cost — 2026-09-25

## Identity capability ≠ configured behavior ≠ verified live enforcement

✅ VERIFIED current inventory: no Cognito user pools in 17 enabled regions; no authorizers on the three HTTP APIs; no IAM OIDC providers. IAM OIDC provider registration is not required merely to use an external issuer with an HTTP API JWT authorizer, so its absence does not prove no external identity option exists. No issuer endpoint/token/client secret was queried.

| Option | Provider capability | Configured here | PR #9 exact-profile result |
|---|---|---|---|
| Existing legacy APIs | No authorizer observed | NONE | 🚫 BLOCKED; legacy handshake is not V6 authentication and must not be reused. |
| New Cognito user pool, human authorization-code + PKCE | Documented user access tokens, resource-bound audience and custom scopes | None | ⚠️ MIGRATION/DECISION REQUIRED. Reasonable low-cost human sandbox direction, but mandatory nbf is not documented in standard tokens and cannot be added by pre-token trigger. No claim compatibility assertion without samples. |
| New Cognito client credentials/M2M | Access tokens/custom scopes; client identity, paid token issuance | None | ⚠️ MIGRATION/DECISION REQUIRED. Resource-bound aud flow excludes client credentials; required user-style subject needs explicit machine profile proof. No automatic substitution of client_id for aud/sub. |
| External OIDC authorization server | Could deliberately emit all required claims using a configured access-token profile | No known approved issuer/client | 🐈📦 UNRESOLVED availability, cost, public JWKS/RSA compatibility, claim types and operational trust. Do not invent a provider. |

| Claim / structure | PR #9 requirement | Feasibility / decision |
|---|---|---|
| iss | Exact configured HTTPS issuer string | Cognito issuer possible; chosen pool and exact issuer still absent. |
| aud | Required single exact audience string | Cognito access-token aud only with requested resource binding in supported user flows. Gateway can fall back to client_id if aud absent; PR #9 deliberately cannot. Do not equate Gateway acceptance with host acceptance. |
| client_id | Required allowlisted string | Cognito access tokens supply it; external providers may use azp instead. No implicit translation. |
| sub | Required bounded nonempty subject, registry-bound with issuer/client | Human Cognito subject available. M2M semantics/profile unproved. Never bind only a caller-provided sender. |
| token_use | Must be access | Cognito provides it; generic OIDC need not. ID tokens remain rejected. |
| scope | Allowed jel-v6/read and jel-v6/write only, exact agreement with Gateway jwt.scopes | Cognito resource server identifier jel-v6 and scope read/write can produce these strings. Extra openid/profile/email/admin scopes would be rejected. Agree exact requested scopes in a provider review. |
| exp, iat | Required epoch strings, temporal validation | Cognito emits NumericDate values; actual Gateway string normalization must be proven. |
| nbf | Required epoch string | Standard Cognito example omits it, and pre-token trigger cannot add/modify nbf. Current mandatory requirement is unnecessarily incompatible with ordinary Cognito usage. Review whether optional nbf with strict validation when present meets the security model; do not patch it in an evidence PR. |
| Other claims and audience arrays | Adapter requires string-valued claim map, single aud; scopes list validated separately | Group/array/number rendering in actual Gateway events remains 🐈📦. Test real provider/Gateway fixture after explicit authorization, then review narrowly scoped normalization. |
| API ID / stage / invocation alias | Exact expected API, sandbox stage, qualified alias | Structural consistency only. A direct caller can forge authorizer data if IAM lets it invoke. |

Sources inspected 2026-09-25: [Cognito access tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html), [resource binding and supported flows](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-define-resource-servers.html), [trigger claim restrictions](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html), [token endpoint / machine flow](https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html). These are capability documents, not account observations.

[Gateway JWT validation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html) covers signature/JWKS, issuer, audience (client_id fallback), time and route scopes. Lambda consumes projected claims under a trusted-invocation assumption; it does not cryptographically verify JWTs. Gateway does not implement the server-owned tenant/sender/receiver/instruction registry. Real cryptographic enforcement, issuer revocation/key rotation, scope propagation, time skew and bypass protection remain 🐈📦.

## Cost assumptions and provenance

Planning estimate only, USD/us-east-1, official pages checked September 25, 2026. No billing records, credit balances or signup eligibility inspected. Assume 10,000 HTTP requests/month, 256 MB Lambda averaging 100 ms including billed initialization, 5,000 writes of ≤4 KB and 5,000 strong reads of ≤4 KB, 0.1 GB average table/log storage, 0.1 GB log ingestion, two standard alarms, 0.1 GB total retained artifacts, one human tester. Real serialized items include envelope/receipt overhead; retry/conflict paths add requests. No NAT, custom domain, WAF, SMS, provisioned concurrency, paid AI or cross-region copies assumed. No guarantee of $0; public endpoint abuse, logs, retention and identity token volume can dominate.

| Service | Cost class | Approximate marginal cost before free allowances / constraints |
|---|---|---|
| HTTP API | negligible | $1/million first-tier requests → about $0.01. Free request allowance/credits depend on eligibility and shared account usage. [Pricing](https://aws.amazon.com/api-gateway/pricing/). |
| Lambda | likely free at test volume | 250 GB-s plus 10k requests ≈ $0.0062 before allowances at $0.0000166667/GB-s and $0.20/million. Published 1m requests/400k GB-s free allowance is shared; no available balance proved. Reservation is not provisioned concurrency. [Pricing](https://aws.amazon.com/lambda/pricing/). |
| DynamoDB on-demand | negligible | 20k write units × $0.625/million + 5k strong read units × $0.125/million ≈ $0.0131. Storage at $0.25/GB-month ≈ $0.025 before the published 25 GB Standard storage allowance. PITR is separately billable and retained table/history accumulates. Do not apply provisioned-capacity free units to on-demand traffic. [Pricing](https://aws.amazon.com/dynamodb/pricing/). |
| CloudWatch | potentially billable | Logs at $0.50/GB ingestion + $0.03/GB archive ≈ $0.053; two standard alarm metrics at $0.10/month ≈ $0.20 before allowances. Free allowances are shared. Custom/app metrics, queries and notifications can add cost. [Pricing](https://aws.amazon.com/cloudwatch/pricing/). |
| Cognito human user flow | likely free at test volume | Lite/Essentials direct/social-user allowance is 10k MAU; Plus has no such free tier. Email/SMS and extra features may bill separately. No configured pool or proven eligibility. [Pricing](https://aws.amazon.com/cognito/pricing/). |
| Cognito M2M | potentially billable | Current example $0.00225/successful token: 100 tokens ≈ $0.225; 5k ≈ $11.25. App-client monthly charge was removed November 2025; do not repeat old per-client pricing. Token reuse within validity affects cost. [Pricing](https://aws.amazon.com/cognito/pricing/), [change announcement](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-cognito-removes-machine-machine-app-client-price-dimension/). |
| External IdP | 🐈📦 | No chosen provider/plan; free availability and token profile unproved. |
| S3 artifacts | negligible / exact rate 🐈📦 | 0.1 GB and a handful of versioned object requests should be small; storage, requests, retained versions and encryption options bill separately. Dynamic regional price table was not extractable, so no fabricated exact regional rate. [Pricing](https://aws.amazon.com/s3/pricing/). |

Base modeled API/Lambda/DDB/CloudWatch subtotal ≈ **$0.31/month before allowances**, excluding PITR, S3, identity, transfer/taxes and any additional monitoring. A tiny human sandbox is plausibly sub-dollar at those assumptions, but the incomplete subtotal is not a quote or cap. M2M tokens can exceed all infrastructure cost. Free-plan credits introduced for new customers in July 2025 are not proof this account has any remaining entitlement. Approve a spend ceiling, retention/cleanup plan and monitoring before activation. No budget or alarm was created by this audit.
