# Connector read-only script. Environment values are never returned.
async def read(service, operation, region='us-east-1', params=None):
    try:
        return await call_boto3(service_name=service,operation_name=operation,region_name=region,params=params or {})
    except Exception:
        return {'unresolved': operation}

async def region_details(region):
    funcs, tables, apis = await asyncio.gather(read('lambda','ListFunctions',region),read('dynamodb','ListTables',region),read('apigatewayv2','GetApis',region),return_exceptions=True)
    functions=[]
    for f in funcs.get('Functions',[]):
        name=f['FunctionName']
        config,aliases,versions,policy,urls=await asyncio.gather(
            read('lambda','GetFunctionConfiguration',region,{'FunctionName':name}),
            read('lambda','ListAliases',region,{'FunctionName':name}),
            read('lambda','ListVersionsByFunction',region,{'FunctionName':name}),
            read('lambda','GetPolicy',region,{'FunctionName':name}),
            read('lambda','ListFunctionUrlConfigs',region,{'FunctionName':name}),return_exceptions=True)
        keep=['FunctionName','FunctionArn','Runtime','Role','Handler','CodeSize','CodeSha256','LastModified','Timeout','MemorySize','PackageType','Architectures','State','LastUpdateStatus','RevisionId']
        clean={k:v for k,v in config.items() if k in keep}
        clean['environment_names']=sorted(config.get('Environment',{}).get('Variables',{}).keys())
        functions.append({'configuration':clean,'aliases':aliases,'versions':[{k:v for k,v in x.items() if k in keep+['Version']} for x in versions.get('Versions',[])],'policy':policy,'function_urls':urls})
    table_details=[]
    for name in tables.get('TableNames',[]):
        info=await read('dynamodb','DescribeTable',region,{'TableName':name})
        table=info.get('Table',{})
        keep=['TableName','TableArn','TableStatus','AttributeDefinitions','KeySchema','GlobalSecondaryIndexes','BillingModeSummary','DeletionProtectionEnabled','SSEDescription']
        table_details.append({k:v for k,v in table.items() if k in keep})
    api_details=[]
    for api in apis.get('Items',[]):
        aid=api['ApiId']
        parts=await asyncio.gather(*[read('apigatewayv2',op,region,{'ApiId':aid}) for op in ['GetRoutes','GetIntegrations','GetStages','GetAuthorizers']],return_exceptions=True)
        api_details.append({'api':{k:v for k,v in api.items() if k in ['ApiId','Name','ProtocolType','DisableExecuteApiEndpoint']},'routes':parts[0],'integrations':parts[1],'stages':parts[2],'authorizers':parts[3]})
    extras=await asyncio.gather(read('lambda','GetAccountSettings',region),read('logs','DescribeLogGroups',region),read('cloudformation','ListStacks',region),return_exceptions=True)
    return {'region':region,'functions':functions,'tables':table_details,'apis':api_details,'lambda_account_settings':extras[0],
            'log_groups':[{k:v for k,v in x.items() if k in ['logGroupName','retentionInDays','kmsKeyId','arn','logGroupClass']} for x in extras[1].get('logGroups',[])],
            'stacks':[{k:v for k,v in x.items() if k in ['StackName','StackStatus','StackId','CreationTime']} for x in extras[2].get('StackSummaries',[])],
            'errors':[x for x in extras if isinstance(x,dict) and 'unresolved' in x]}
regions=await asyncio.gather(*[region_details(r) for r in ['us-east-1','us-east-2']],return_exceptions=True)
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'regions':regions}
result
