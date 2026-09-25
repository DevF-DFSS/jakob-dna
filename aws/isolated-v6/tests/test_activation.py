import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import boto3
import botocore.session
from botocore.stub import Stubber
from botocore.exceptions import ReadTimeoutError
from aws_v6.activation import compose, sdk_client
from aws_v6 import activation
from aws_v6.claims import GatewayClaims
from aws_v6.config import settings, load_registry
from aws_v6.dynamodb import DynamoEventStore, marshal
from isolated_v6.store import StoreUnavailable
from test_ingress import fixture, http, NOW
from test_aws_candidate import row

ALIAS='arn:aws:lambda:us-east-1:000000000000:function:synthetic-v6:sandbox'
CTX=SimpleNamespace(invoked_function_arn=ALIAS)


def policy():
    return {'version':'v1','bindings':[{'issuer':'https://synthetic.invalid','subject':'subject','client_id':'client',
        'tenant':'tenant-a','senders':['sender'],'receivers':['receiver'],'instructions':['ACCEPT']}]}


def environment(raw):
    return dict(V6_TABLE_NAME='jel-v6-synthetic',EXPECTED_REGION='us-east-1',AWS_REGION='us-east-1',
        EXPECTED_API_ID='syntheticapi',EXPECTED_STAGE='sandbox',EXPECTED_ISSUER='https://synthetic.invalid',
        EXPECTED_AUDIENCE='v6-audience',EXPECTED_CLIENT_IDS='["client"]',EXPECTED_ALIAS_ARN=ALIAS,
        BINDINGS_VERSION='v1',BINDINGS_SHA256=hashlib.sha256(raw).hexdigest())


def event():
    e=http();e['requestContext'].update(apiId='syntheticapi',stage='sandbox')
    e['requestContext']['authorizer']={'jwt':{'claims':{
        'iss':'https://synthetic.invalid','aud':'v6-audience','client_id':'client','sub':'subject',
        'token_use':'access','scope':'jel-v6/read jel-v6/write','iat':str(NOW//1000-10),
        'nbf':str(NOW//1000-10),'exp':str(NOW//1000+60)},'scopes':['jel-v6/read','jel-v6/write']}}
    return e


def client():
    # Never use the default session or stored credentials/config; explicitly
    # synthetic signing inputs and empty config files. No requests can be sent.
    session=botocore.session.Session()
    session.set_config_variable('config_file','/dev/null')
    session.set_config_variable('credentials_file','/dev/null')
    session.set_credentials('synthetic-access','synthetic-secret','synthetic-session')
    return boto3.session.Session(botocore_session=session).client('dynamodb',region_name='us-east-1')


class ClaimsTests(unittest.TestCase):
    def setUp(self):
        self.raw=json.dumps(policy()).encode();self.env=environment(self.raw)
        self.auth=GatewayClaims(settings(self.env),lambda:NOW)
    def test_valid(self): self.assertEqual('subject',self.auth.authenticate(event(),CTX).subject)
    def test_spoof_body_header_ignored(self):
        e=event(); e['headers']['x-subject']='attacker';e['body']='{"sub":"attacker"}'
        self.assertEqual('subject',self.auth.authenticate(e,CTX).subject)
    def test_direct_invocation_not_cryptographically_proven(self):
        # A fully forged event AND qualifying context pass structural checks.
        # This test documents why real IAM invocation isolation is mandatory.
        self.assertIsNotNone(self.auth.authenticate(copy.deepcopy(event()),CTX))
        self.assertIsNone(self.auth.authenticate(event(),SimpleNamespace(invoked_function_arn=ALIAS.rsplit(':',1)[0])))
    def test_missing_alias_context(self): self.assertIsNone(self.auth.authenticate(event(),None))


def bad_claim(name,value):
    def test(self):
        e=event();e['requestContext']['authorizer']['jwt']['claims'][name]=value
        self.assertIsNone(self.auth.authenticate(e,CTX))
    setattr(ClaimsTests,'test_claim_'+name+'_'+str(len(ClaimsTests.__dict__)),test)

for name,value in [('iss','wrong'),('aud','wrong'),('aud',['v6-audience']),('client_id','wrong'),('sub',''),
    ('sub',' leading'),('sub','x\n'),('token_use','id'),('scope','jel-v6/write  jel-v6/read'),
    ('scope','jel-v6/admin'),('exp',str(NOW//1000)),('iat',str(NOW//1000+1)),('nbf',str(NOW//1000+1)),
    ('exp',True),('exp','NaN'),('scope',['jel-v6/read'])]: bad_claim(name,value)


def malformed(name, mutate):
    def test(self):
        e=event();mutate(e);self.assertIsNone(self.auth.authenticate(e,CTX))
    setattr(ClaimsTests,'test_'+name,test)

malformed('missing_authorizer',lambda e:e['requestContext'].pop('authorizer'))
malformed('null_authorizer',lambda e:e['requestContext'].update(authorizer=None))
malformed('lambda_authorizer',lambda e:e['requestContext'].update(authorizer={'lambda':{}}))
malformed('wrong_api',lambda e:e['requestContext'].update(apiId='wrong'))
malformed('wrong_stage',lambda e:e['requestContext'].update(stage='production'))
malformed('missing_subject',lambda e:e['requestContext']['authorizer']['jwt']['claims'].pop('sub'))
malformed('scope_mismatch',lambda e:e['requestContext']['authorizer']['jwt'].update(scopes=['jel-v6/read']))
malformed('scope_duplicates',lambda e:e['requestContext']['authorizer']['jwt'].update(scopes=['jel-v6/read','jel-v6/read']))
malformed('claims_list',lambda e:e['requestContext']['authorizer']['jwt'].update(claims=[]))
malformed('scope_string',lambda e:e['requestContext']['authorizer']['jwt'].update(scopes='jel-v6/read'))


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'bindings.json';self.path.write_text(json.dumps(policy()))
        self.env=environment(self.path.read_bytes())
    def test_valid_registry(self):
        self.assertIsNotNone(load_registry(settings(self.env),self.path))
    def test_invalid_environment_each_required_key(self):
        for key in self.env:
            bad=dict(self.env);bad.pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError): settings(bad)
    def test_bad_config_before_client(self):
        for key,value in [('EXPECTED_REGION','eu-west-1'),('EXPECTED_STAGE','production'),('V6_TABLE_NAME','legacy'),
            ('EXPECTED_ISSUER','http://wrong'),('EXPECTED_CLIENT_IDS','[]'),('BINDINGS_SHA256','wrong'),('EXPECTED_ALIAS_ARN','wrong')]:
            bad=dict(self.env);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):
                compose(bad,client_factory=lambda _:self.fail('client constructed'),registry_path=self.path)
    def test_binding_hash_version_missing(self):
        for mutate in [lambda p:p.update(version='v2'),lambda p:p.update(bindings=[]),lambda p:p['bindings'][0].update(client_id='other'),
                       lambda p:p['bindings'].append(p['bindings'][0]),lambda p:p['bindings'][0].update(senders=[])]:
            p=policy();mutate(p);self.path.write_text(json.dumps(p));env=environment(self.path.read_bytes())
            with self.assertRaises(ValueError): compose(env,registry_path=self.path,client_factory=lambda _:self.fail('client constructed'))
        with self.assertRaises(ValueError): compose(self.env,registry_path=self.path,client_factory=lambda _:self.fail('client constructed'))
    def test_missing_binding_file(self):
        self.path.unlink()
        with self.assertRaises(FileNotFoundError): compose(self.env,registry_path=self.path,client_factory=lambda _:self.fail('client constructed'))
    def test_unknown_revoked_subject(self):
        c=client();host=compose(self.env,registry_path=self.path,client_factory=lambda _:c,clock_ms=lambda:NOW)
        e=event();e['requestContext']['authorizer']['jwt']['claims']['sub']='unknown'
        self.assertEqual(403,host(e,CTX)['statusCode'])
        host.ingress.registry.revoke(('https://synthetic.invalid','subject','client'))
        self.assertEqual(403,host(event(),CTX)['statusCode'])
    def test_actual_composition(self):
        c=client();host=compose(self.env,registry_path=self.path,client_factory=lambda _:c,clock_ms=lambda:NOW)
        with Stubber(c) as stub:
            stub.add_response('put_item',{'ResponseMetadata':{'HTTPStatusCode':200}})
            self.assertEqual(201,host(event(),CTX)['statusCode'])
            stub.assert_no_pending_responses()
    def test_handler_startup_closed(self):
        with patch.object(activation,'_host',None),patch.object(activation,'compose',side_effect=ValueError('synthetic-sensitive')):
            result=activation.handler(event(),CTX)
            self.assertEqual(503,result['statusCode']);self.assertNotIn('sensitive',str(result))
    def test_unconfigured_packaged_registry_blocks_client(self):
        with self.assertRaises(ValueError): compose(self.env,client_factory=lambda _:self.fail('client constructed'))
    def test_sdk_factory_config(self):
        c=client()
        with patch('boto3.session.Session') as session:
            session.return_value.client.return_value=c
            self.assertIs(c,sdk_client(settings(self.env)))
            args=session.return_value.client.call_args
            self.assertEqual(('dynamodb',),args.args)
            self.assertEqual(1,args.kwargs['config'].retries['total_max_attempts'])
            self.assertTrue(args.kwargs['config'].ignore_configured_endpoint_urls)

    def test_uncertain_commit_receipt_recovery_real_stubs(self):
        c=client();host=compose(self.env,registry_path=self.path,client_factory=lambda _:c,clock_ms=lambda:NOW)
        with patch.object(c,'put_item',side_effect=ReadTimeoutError(endpoint_url='https://synthetic.invalid')):
            self.assertEqual(503,host(event(),CTX)['statusCode'])
        with Stubber(c) as stub:
            stub.add_client_error('put_item','ConditionalCheckFailedException')
            stub.add_response('get_item',{'Item':marshal(row()),'ResponseMetadata':{'HTTPStatusCode':200}})
            response=host(event(),CTX)
            self.assertEqual(200,response['statusCode'])
            self.assertEqual(NOW,json.loads(response['body'])['accepted_at_ms'])
            stub.assert_no_pending_responses()
    def test_duplicate_registry_json(self):
        raw=b'{"version":"v1","version":"v1","bindings":[]}'
        self.path.write_bytes(raw)
        with self.assertRaises(ValueError): load_registry(settings(environment(raw)),self.path)
    def test_no_request_bypass(self):
        c=client();host=compose(self.env,registry_path=self.path,client_factory=lambda _:c,clock_ms=lambda:NOW)
        e=event();e['requestContext'].pop('authorizer');e['trusted_principal']={'sub':'subject'}
        e['headers']['x-auth-bypass']='true'
        self.assertEqual(401,host(e,CTX)['statusCode'])


class RealSDKTests(unittest.TestCase):
    def setUp(self): self.client=client();self.store=DynamoEventStore(self.client,'jel-v6-synthetic')
    def test_request_serialization(self):
        # Botocore before-call receives serialized protocol body. Stubber itself
        # short-circuits earlier, so exercise the serializer independently too.
        model=self.client.meta.service_model.operation_model('PutItem')
        request=self.client._serializer.serialize_to_request({'TableName':'jel-v6-synthetic','Item':marshal(row()),
            'ConditionExpression':'attribute_not_exists(#pk) AND attribute_not_exists(#sk)',
            'ExpressionAttributeNames':{'#pk':'PK','#sk':'SK'}},model)
        body=json.loads(request['body'])
        self.assertEqual({'N':str(NOW)},body['Item']['receipt']['M']['accepted_at_ms'])
        self.assertEqual(row().wrapper_bytes.decode(),body['Item']['wrapper_json']['S'])
    def test_conditional_write_stub(self):
        expected={'TableName':'jel-v6-synthetic','Item':marshal(row()),
            'ConditionExpression':'attribute_not_exists(#pk) AND attribute_not_exists(#sk)',
            'ExpressionAttributeNames':{'#pk':'PK','#sk':'SK'}}
        with Stubber(self.client) as stub:
            stub.add_response('put_item',{'ResponseMetadata':{'HTTPStatusCode':200}},expected)
            stub.add_client_error('put_item','ConditionalCheckFailedException',expected_params=expected)
            self.assertTrue(self.store.insert_if_absent(row()));self.assertFalse(self.store.insert_if_absent(row()))
            stub.assert_no_pending_responses()
    def test_consistent_get_stub(self):
        expected={'TableName':'jel-v6-synthetic','Key':{'PK':{'S':row().pk},'SK':{'S':row().sk}},'ConsistentRead':True}
        with Stubber(self.client) as stub:
            stub.add_response('get_item',{'Item':marshal(row()),'ResponseMetadata':{'HTTPStatusCode':200}},expected)
            self.assertEqual(row(),self.store.get(row().pk,row().sk));stub.assert_no_pending_responses()
    def test_sdk_error_mapping(self):
        for code in ['ProvisionedThroughputExceededException','InternalServerError','AccessDeniedException']:
            with Stubber(self.client) as stub:
                stub.add_client_error('put_item',code)
                with self.assertRaises(StoreUnavailable): self.store.insert_if_absent(row())
    def test_uncertain_readtimeout(self):
        with patch.object(self.client,'put_item',side_effect=ReadTimeoutError(endpoint_url='https://synthetic.invalid')):
            with self.assertRaises(StoreUnavailable): self.store.insert_if_absent(row())
    def test_credential_discovery_is_blocked(self):
        from botocore.credentials import CredentialResolver
        with self.assertRaises(AssertionError): CredentialResolver([]).load_credentials()
    def test_network_is_blocked(self):
        import socket
        with self.assertRaises(AssertionError): socket.socket()
