# First writer — current live read-only finding (2026-09-27)

**No approved non-root first writer was observed in account `083127296577`.** The AWS connector resolved to `arn:aws:iam::083127296577:root`; this identity was used for metadata reads only and is excluded from the normal V6 workflow. IAM listed one user, `us-os-gateway`, with no boundary, inline policy or group membership. Its attached policies are AmazonAPIGatewayAdministrator v1, AmazonDynamoDBFullAccess v15 and AWSLambda_FullAccess v7. Their default policy versions allow broad legacy API/Lambda/DynamoDB control but contain no `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PutRolePolicy` or `cloudformation:CreateStack` Allow. Read-only identity-policy simulation of those actions on hypothetical `/jel-v6-approved/` and bootstrap-stack ARNs returned implicitDeny with missing-context warnings. This is supporting simulation, not effective authorization proof. The existing ordinary roles trust Lambda, not a human operator; service-linked roles are separate. None carries a V6 approved path or boundary. The account is not in AWS Organizations (DescribeOrganization reported AWSOrganizationsNotInUseException), so no Organizations SCP is presently available as a fence.

`us-os-gateway` is a **legacy principal to contain**, not a safe installer. Adding a temporary broad policy to it would expose V6 authority through a long-lived legacy identity and would require a separate IAM mutation. Do not use account root to paper over this gap.

The smallest separately authorized prerequisite is an account-security administration operation, outside PR20, that establishes a dedicated non-root, independently authenticated `/jel-v6-approved/` installation/operation path with exact trust, maximum boundary and expiry. The human principal/federation behind that trust is currently unknown; no role or user is invented as already usable. The bootstrap operator and bootstrap CF service role proposed below must be installed and read back before the first V6 stack create. Policy authoring itself is privileged and cannot be made safe by its own self-authored boundary. Another approved administrator or account governance decision must provide that initial authority. This is a real A2 decision, not a request to use root.

Proposed future ARNs, **not currently created**:

- bootstrap operator `arn:aws:iam::083127296577:role/jel-v6-approved/trident27-bootstrap-operator`;
- bootstrap CF service `arn:aws:iam::083127296577:role/jel-v6-approved/trident27-bootstrap-service`;
- normal recovery `arn:aws:iam::083127296577:role/jel-v6-approved/trident27-recovery-operator`;
- future runtime CF service `arn:aws:iam::083127296577:role/jel-v6/jel-v6-sandbox-trident27-runtime-deploy`;
- future ingress CF service `arn:aws:iam::083127296577:role/jel-v6/jel-v6-sandbox-trident27-ingress-deploy`;
- future publisher `arn:aws:iam::083127296577:role/jel-v6/jel-v6-sandbox-trident27-publisher`;
- future execution role `arn:aws:iam::083127296577:role/jel-v6/jel-v6-sandbox-trident27-v6-execution`.

Before any installation, independently confirm every principal, trust path, managed/inline policy, boundary, stack mutator, and temporary session; record the principal that performs the write. Time-box the authority and read back expiry/removal after use. If no non-root security administrator/federation can be approved, the first operation stays BLOCKED. Current role proposals are in PR19 `tools/authority_topology.py`; they are data, not installed grants.
