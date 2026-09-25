# Read-only policy metadata; no policy writes or credential operations.
async def read(service, operation, params=None):
    try:
        return await call_boto3(service_name=service,operation_name=operation,region_name='us-east-1',params=params or {})
    except Exception:
        return {'unresolved': operation}
roles,oidcs,org=await asyncio.gather(read('iam','ListRoles'),read('iam','ListOpenIDConnectProviders'),read('organizations','DescribeOrganization'),return_exceptions=True)
role_details=[]
policy_arns=set()
for role in roles.get('Roles',[]):
    name=role['RoleName']
    info,attached,inline=await asyncio.gather(read('iam','GetRole',{'RoleName':name}),read('iam','ListAttachedRolePolicies',{'RoleName':name}),read('iam','ListRolePolicies',{'RoleName':name}),return_exceptions=True)
    clean=info.get('Role',{})
    for p in attached.get('AttachedPolicies',[]): policy_arns.add(p['PolicyArn'])
    boundary=clean.get('PermissionsBoundary',{}).get('PermissionsBoundaryArn')
    if boundary: policy_arns.add(boundary)
    documents=[]
    for p in inline.get('PolicyNames',[]): documents.append(await read('iam','GetRolePolicy',{'RoleName':name,'PolicyName':p}))
    role_details.append({'role':{k:v for k,v in clean.items() if k in ['RoleName','Arn','Path','AssumeRolePolicyDocument','PermissionsBoundary','CreateDate','MaxSessionDuration']},'attached':attached,'inline':documents})
policies=[]
for arn in sorted(policy_arns):
    policy=await read('iam','GetPolicy',{'PolicyArn':arn})
    version=policy.get('Policy',{}).get('DefaultVersionId')
    document=await read('iam','GetPolicyVersion',{'PolicyArn':arn,'VersionId':version}) if version else {'unresolved':'version'}
    policies.append({'metadata':policy,'default_version':document})
providers=[]
for p in oidcs.get('OpenIDConnectProviderList',[]):providers.append({'arn':p['Arn'],'metadata':await read('iam','GetOpenIDConnectProvider',{'OpenIDConnectProviderArn':p['Arn']})})
# Account/root inheritance enumeration only where Organizations permits it.
identity=await read('sts','GetCallerIdentity')
account=identity.get('Account')
ancestry=[]
current=account
for depth in range(6):
    if not current:break
    attached=await read('organizations','ListPoliciesForTarget',{'TargetId':current,'Filter':'SERVICE_CONTROL_POLICY'})
    docs=[]
    for p in attached.get('Policies',[]):docs.append(await read('organizations','DescribePolicy',{'PolicyId':p['Id']}))
    parents=await read('organizations','ListParents',{'ChildId':current}) if not current.startswith('r-') else {'Parents':[]}
    ancestry.append({'target':current,'policies':attached,'documents':docs,'parents':parents})
    current=parents.get('Parents',[{}])[0].get('Id') if parents.get('Parents') else None
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'roles':role_details,'managed_policies':policies,'oidc':providers,'oidc_list':oidcs,'organization':org,'scp_ancestry':ancestry}
result
