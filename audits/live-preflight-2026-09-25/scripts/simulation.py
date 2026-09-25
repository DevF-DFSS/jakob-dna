roles=await call_boto3(service_name='iam',operation_name='ListRoles',region_name='us-east-1',params={})
results=[]
for r in roles.get('Roles',[]):
    if r['RoleName'] in ['DFSS-ColdStart-role-io8kh35x','us-os-brain-role-c7v6jeb1']:
        for actions,resource in [(['dynamodb:GetItem','dynamodb:PutItem'],'arn:aws:dynamodb:us-east-1:083127296577:table/jel-v6-jel-v6-sandbox-20260925-events'),(['lambda:InvokeFunction','lambda:DeleteFunction'],'arn:aws:lambda:us-east-1:083127296577:function:jel-v6-sandbox-20260925-v6:sandbox')]:
            try:
                value=await call_boto3(service_name='iam',operation_name='SimulatePrincipalPolicy',region_name='us-east-1',params={'PolicySourceArn':r['Arn'],'ActionNames':actions,'ResourceArns':[resource]})
            except Exception:value={'unresolved':'SimulatePrincipalPolicy'}
            results.append({'role':r['RoleName'],'actions':actions,'resource':resource,'simulation':value})
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':results}
result
