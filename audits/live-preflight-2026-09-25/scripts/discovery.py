async def safe(service, operation, region='us-east-1', params=None):
    try:
        return await call_boto3(service_name=service, operation_name=operation, region_name=region, params=params or {})
    except Exception:
        return {'error_type':'unavailable'}
identity, regions = await asyncio.gather(safe('sts','GetCallerIdentity'), safe('ec2','DescribeRegions',params={'AllRegions':False}), return_exceptions=True)
names = [r['RegionName'] for r in regions.get('Regions',[])]
async def inventory(region):
    values=await asyncio.gather(safe('lambda','ListFunctions',region),safe('dynamodb','ListTables',region),safe('apigatewayv2','GetApis',region),safe('cognito-idp','ListUserPools',region,{'MaxResults':60}),return_exceptions=True)
    f,t,a,p=values
    return {'region':region,'functions':[{k:v for k,v in x.items() if k in ['FunctionName','FunctionArn','Runtime','Handler','Role','CodeSha256','CodeSize','LastModified','Architectures','PackageType']} for x in f.get('Functions',[])], 'tables':t.get('TableNames',[]),'apis':[{k:v for k,v in x.items() if k in ['ApiId','Name','ProtocolType','DisableExecuteApiEndpoint']} for x in a.get('Items',[])], 'user_pools':[{k:v for k,v in x.items() if k in ['Id','Name','CreationDate','LastModifiedDate']} for x in p.get('UserPools',[])], 'errors':{k:v for k,v in zip(['lambda','dynamodb','api','cognito'],values) if isinstance(v,dict) and 'error_type' in v}}
regional=await asyncio.gather(*[inventory(r) for r in names],return_exceptions=True)
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':identity,'regions':names,'inventory':regional}
result
