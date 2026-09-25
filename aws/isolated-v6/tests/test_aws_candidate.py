import copy
import dataclasses
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import isolated_v6
from isolated_v6.auth import Binding, Registry
from isolated_v6.contract import canonical, digest
from isolated_v6.service import Ingress
from isolated_v6.store import Event, Receipt, StoreUnavailable
from aws_v6.dynamodb import DynamoEventStore, marshal, unmarshal
from aws_v6.host import LambdaHost, handler
from test_ingress import fixture, http, P, NOW
from build import build
from security import check
from make_template import template

ROOT=Path(__file__).resolve().parents[1]
CORE=Path(isolated_v6.__file__).resolve().parents[1]


def row():
    w=fixture()
    return Event(canonical(['tenant-a','sender']).decode(),'EVENT#'+w['event_id'],w['profile'],digest(w),canonical(w),digest(list(P.key)),'v1',Receipt(w['event_id'],NOW))


class Conflict(Exception): pass


class FakeClient:
    exceptions=SimpleNamespace(ConditionalCheckFailedException=Conflict)
    def __init__(self):
        self.rows={}; self.calls=[]; self.lose=False; self.fail=False
    def put_item(self, **kwargs):
        self.calls.append(('put_item',copy.deepcopy(kwargs)))
        if self.fail: raise TimeoutError('synthetic-sensitive-detail')
        item=kwargs['Item']; key=(item['PK']['S'],item['SK']['S'])
        if key in self.rows: raise Conflict()
        self.rows[key]=copy.deepcopy(item)
        if self.lose: raise TimeoutError('uncertain_commit')
        return {'ResponseMetadata':{'HTTPStatusCode':200}}
    def get_item(self, **kwargs):
        self.calls.append(('get_item',copy.deepcopy(kwargs)))
        if self.fail: raise TimeoutError('synthetic-sensitive-detail')
        key=(kwargs['Key']['PK']['S'],kwargs['Key']['SK']['S'])
        response={'ResponseMetadata':{'HTTPStatusCode':200}}
        if key in self.rows: response['Item']=copy.deepcopy(self.rows[key])
        return response


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.client=FakeClient(); self.store=DynamoEventStore(self.client,'synthetic-v6-table')
    def test_roundtrip(self):
        self.assertEqual(row(),unmarshal(marshal(row())))
    def test_exact_attribute_types(self):
        item=marshal(row())
        self.assertEqual({'N':str(NOW)},item['receipt']['M']['accepted_at_ms'])
        self.assertEqual({'S':row().wrapper_bytes.decode()},item['wrapper_json'])
    def test_conditional_put(self):
        self.assertTrue(self.store.insert_if_absent(row()))
        call=self.client.calls[0][1]
        self.assertEqual('attribute_not_exists(#pk) AND attribute_not_exists(#sk)',call['ConditionExpression'])
        self.assertEqual({'#pk':'PK','#sk':'SK'},call['ExpressionAttributeNames'])
        self.assertEqual('synthetic-v6-table',call['TableName'])
    def test_conflict_no_overwrite(self):
        self.assertTrue(self.store.insert_if_absent(row()))
        self.assertFalse(self.store.insert_if_absent(dataclasses.replace(row(),binding_version='v2')))
        self.assertEqual('v1',self.store.get(row().pk,row().sk).binding_version)
    def test_strong_read(self):
        self.store.insert_if_absent(row())
        self.assertEqual(row(),self.store.get(row().pk,row().sk))
        self.assertIs(True,self.client.calls[-1][1]['ConsistentRead'])
    def test_missing_read(self): self.assertIsNone(self.store.get(row().pk,row().sk))
    def test_put_error(self):
        self.client.fail=True
        with self.assertRaises(StoreUnavailable) as result: self.store.insert_if_absent(row())
        self.assertEqual('',str(result.exception))
    def test_get_error(self):
        self.client.fail=True
        with self.assertRaises(StoreUnavailable): self.store.get(row().pk,row().sk)
    def test_unknown_success_response(self):
        self.client.put_item=lambda **kw: {}
        with self.assertRaises(StoreUnavailable): self.store.insert_if_absent(row())
    def test_bad_read_status(self):
        self.client.get_item=lambda **kw: {'ResponseMetadata':{'HTTPStatusCode':500}}
        with self.assertRaises(StoreUnavailable): self.store.get(row().pk,row().sk)
    def test_corrupt_item(self):
        self.store.insert_if_absent(row())
        self.client.rows[(row().pk,row().sk)]['request_digest']={'S':'0'*64}
        with self.assertRaises(StoreUnavailable): self.store.get(row().pk,row().sk)
    def test_wrong_record_read(self):
        self.store.insert_if_absent(row())
        self.client.get_item=lambda **kw: {'ResponseMetadata':{'HTTPStatusCode':200},'Item':marshal(row())}
        with self.assertRaises(StoreUnavailable): self.store.get('wrong',row().sk)
    def test_bad_receipt_number(self):
        for number in ('1.5','NaN','01','1e3'):
            item=marshal(row()); item['receipt']['M']['accepted_at_ms']={'N':number}
            with self.assertRaises(ValueError): unmarshal(item)
    def test_immutable_roundtrip(self):
        result=unmarshal(marshal(row()))
        with self.assertRaises(dataclasses.FrozenInstanceError): result.receipt.status='bad'
    def test_only_two_operations(self):
        self.store.insert_if_absent(row()); self.store.get(row().pk,row().sk)
        self.assertEqual(['put_item','get_item'],[name for name,_ in self.client.calls])
        for name in ['update_item','delete_item','scan','query']:
            self.assertFalse(hasattr(self.store,name))
    def app(self):
        binding=Binding('tenant-a',frozenset({'sender'}),frozenset({'receiver'}),frozenset({'ACCEPT'}),'v1')
        return Ingress(Registry({P.key:binding}),self.store,lambda:NOW,api_id='synthetic-api',stage='offline')
    def test_uncertain_commit_recovery(self):
        app=self.app(); self.client.lose=True
        self.assertEqual(503,app.handle(http(),trusted_principal=P)['statusCode'])
        self.client.lose=False
        response=app.handle(http(),trusted_principal=P)
        self.assertEqual(200,response['statusCode'])
        self.assertEqual(NOW,json.loads(response['body'])['accepted_at_ms'])
    def test_same_id_conflict_service(self):
        app=self.app()
        self.assertEqual(201,app.handle(http(),trusted_principal=P)['statusCode'])
        w=fixture(); w['issued_at']='2026-09-24T12:00:01Z'
        self.assertEqual(409,app.handle(http(w),trusted_principal=P)['statusCode'])
    def test_host_injected_identity(self):
        host=LambdaHost(self.app(),SimpleNamespace(authenticate=lambda event,context:P))
        self.assertEqual(201,host(http(),None)['statusCode'])
    def test_host_forged_claims_denied(self):
        event=http(); event['requestContext']['authorizer']={'jwt':{'claims':dataclasses.asdict(P)}}
        host=LambdaHost(self.app(),SimpleNamespace(authenticate=lambda event,context:None))
        self.assertEqual(401,host(event,None)['statusCode'])
        self.assertEqual([],self.client.calls)
    def test_host_untyped_claims_denied(self):
        host=LambdaHost(self.app(),SimpleNamespace(authenticate=lambda event,context:dataclasses.asdict(P)))
        self.assertEqual(401,host(http(),None)['statusCode'])
    def test_auth_exception_sanitized(self):
        auth=Mock(); auth.authenticate.side_effect=RuntimeError('synthetic-sensitive-detail')
        response=LambdaHost(self.app(),auth)(http(),None)
        self.assertEqual(503,response['statusCode']); self.assertNotIn('sensitive',str(response))
    def test_packaged_entrypoint_closed(self):
        self.assertEqual(503,handler(http(),None)['statusCode'])
        self.assertEqual([],self.client.calls)
    def test_table_required(self):
        for name in ('','*','arn:aws:dynamodb:legacy'):
            with self.assertRaises(ValueError): DynamoEventStore(self.client,name)


class InfrastructureTests(unittest.TestCase):
    def test_generated_template_matches(self):
        self.assertEqual(template(),json.loads((ROOT/'infra/template.json').read_text()))
    def test_security_allowlist(self): self.assertTrue(check(template()))
    def test_reproducible_package(self):
        with tempfile.TemporaryDirectory() as temp:
            a=build(CORE,ROOT,Path(temp)/'a','1'*40,run_tests=False)
            b=build(CORE,ROOT,Path(temp)/'b','1'*40,run_tests=False)
            self.assertEqual(a,b)
            self.assertEqual((Path(temp)/'a/isolated-v6-candidate.zip').read_bytes(),(Path(temp)/'b/isolated-v6-candidate.zip').read_bytes())
            self.assertEqual('1.40.35',a['dependencies']['third_party']['boto3'])
            self.assertFalse(a['tests']['passed'])
            self.assertTrue(all(not f['path'].startswith('tests') for f in a['included_files']))
    def test_source_sha_required(self):
        with self.assertRaises(ValueError): build(CORE,ROOT,Path('/unused'),'HEAD',run_tests=False)


def negative(name, mutate):
    def test(self):
        t=template(); mutate(t['Resources'])
        with self.assertRaises(AssertionError): check(t)
    setattr(InfrastructureTests,'test_reject_'+name,test)

negative('none_auth',lambda r:r['PostRoute']['Properties'].update(AuthorizationType='NONE'))
negative('wildcard_dynamo',lambda r:r['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'][0].update(Resource='*'))
negative('extra_dynamo_action',lambda r:r['ExecutionRole']['Properties']['Policies'][0]['PolicyDocument']['Statement'][0]['Action'].append('dynamodb:DeleteItem'))
negative('public_url',lambda r:r.update(Url={'Type':'AWS::Lambda::Url','Properties':{}}))
negative('legacy_role',lambda r:r['Function']['Properties'].update(Role='us-os-brain'))
negative('unqualified_invoke',lambda r:r['PostPermission']['Properties'].update(FunctionName={'Ref':'Function'}))
negative('public_principal',lambda r:r['PostPermission']['Properties'].update(Principal='*'))
negative('broad_source',lambda r:r['PostPermission']['Properties'].update(SourceArn={'Fn::Sub':'*'}))
negative('autodeploy',lambda r:r['Stage']['Properties'].update(AutoDeploy=True))
negative('any_route',lambda r:r['PostRoute']['Properties'].update(RouteKey='ANY /v6/events'))
negative('legacy_secret',lambda r:r['Function']['Properties']['Environment']['Variables'].update(GEMINI_API_KEY='synthetic'))
negative('unexpected_environment',lambda r:r['Function']['Properties']['Environment']['Variables'].update(EXTRA='unreviewed'))
negative('missing_source_account',lambda r:r['PostPermission']['Properties'].pop('SourceAccount'))
negative('wrong_scope',lambda r:r['GetRoute']['Properties'].update(AuthorizationScopes=['jel-v6/write']))
