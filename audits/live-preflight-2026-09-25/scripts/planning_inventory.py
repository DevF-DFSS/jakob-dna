async def read(service,operation,region='us-east-1',params=None):
    try:return await call_boto3(service_name=service,operation_name=operation,region_name=region,params=params or {})
    except Exception:return {'unresolved':operation}
buckets=await read('s3','ListBuckets')
storage=[]
for b in buckets.get('Buckets',[]):
    name=b['Name']
    location,versioning=await asyncio.gather(read('s3','GetBucketLocation',params={'Bucket':name}),read('s3','GetBucketVersioning',params={'Bucket':name}),return_exceptions=True)
    storage.append({'name':name,'location':location,'versioning':versioning})
async def quotas(region):
    values=await asyncio.gather(*[read('service-quotas','ListServiceQuotas',region,{'ServiceCode':s}) for s in ['lambda','dynamodb','apigateway','cognito-idp','cloudformation']],return_exceptions=True)
    selected=[]
    for service,data in zip(['lambda','dynamodb','apigateway','cognito-idp','cloudformation'],values):
        selected.append({'service':service,'unresolved':data.get('unresolved'),'quotas':[{k:v for k,v in q.items() if k in ['QuotaCode','QuotaName','Value','Unit','Adjustable','GlobalQuota']} for q in data.get('Quotas',[]) if any(term in q.get('QuotaName','').lower() for term in ['concurrent','storage','tables','read','write','api','authorizer','user pool','stack'])]})
    alarms=await read('cloudwatch','DescribeAlarms',region)
    return {'region':region,'services':selected,'alarms':[{k:v for k,v in a.items() if k in ['AlarmName','Namespace','MetricName','Dimensions','ActionsEnabled','AlarmActions']} for a in alarms.get('MetricAlarms',[])]}
regional=await asyncio.gather(*[quotas(r) for r in ['us-east-1','us-east-2']],return_exceptions=True)
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'buckets':storage,'regions':regional}
result
