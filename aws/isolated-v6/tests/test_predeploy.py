"""Synthetic projected claims, never minted tokens or live-provider evidence."""
import copy
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aws_v6 import activation
from aws_v6.claims import GatewayClaims
from aws_v6.config import settings, load_registry
from aws_v6.host import LambdaHost
from aws_v6.telemetry import emit_outcome
from isolated_v6.service import Ingress
from isolated_v6.store import MemoryStore
from test_activation import environment, policy, event, CTX
from test_ingress import NOW, fixture, sign
from make_template import template
from security import check
from release_manifest import validate, read_json

ROOT=Path(__file__).resolve().parents[1]
PROJECTED=json.loads((ROOT/'tests/fixtures/cognito_projected.json').read_text())


class CognitoProjectedTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'bindings.json'
        p=policy();b=p['bindings'][0];c=PROJECTED['claims']
        b.update(issuer=c['iss'],subject=c['sub'],client_id=c['client_id'])
        self.path.write_text(json.dumps(p));self.env=environment(self.path.read_bytes())
        self.env.update(EXPECTED_ISSUER=c['iss'],EXPECTED_AUDIENCE=c['aud'],EXPECTED_CLIENT_IDS=json.dumps([c['client_id']]))
        config=settings(self.env);self.auth=GatewayClaims(config,lambda:NOW)
        self.store=MemoryStore()
        self.host=LambdaHost(Ingress(load_registry(config,self.path),self.store,lambda:NOW,api_id='syntheticapi',stage='sandbox'),self.auth)
    def event(self):
        e=event();e['requestContext']['authorizer']['jwt']=copy.deepcopy(PROJECTED);return e
    def test_absent_nbf_accepts_and_persists(self):
        self.assertEqual(201,self.host(self.event(),CTX)['statusCode'])
    def test_present_nbf_at_now_accepts(self):
        e=self.event();e['requestContext']['authorizer']['jwt']['claims']['nbf']=str(NOW//1000)
        self.assertEqual(201,self.host(e,CTX)['statusCode'])
    def test_present_nbf_past_accepts(self):
        e=self.event();e['requestContext']['authorizer']['jwt']['claims']['nbf']=str(NOW//1000-1)
        self.assertIsNotNone(self.auth.authenticate(e,CTX))
    def test_present_invalid_nbf_denies(self):
        for v in [None,True,0,[],{},'', 'NaN','1.2','-1',' 1','1 ','0'*13,str(NOW//1000+1),str(NOW//1000+60)]:
            e=self.event();e['requestContext']['authorizer']['jwt']['claims']['nbf']=v
            with self.subTest(v=v): self.assertEqual(401,self.host(e,CTX)['statusCode'])
    def test_required_claims_remain_required(self):
        for k in ['iss','aud','client_id','sub','token_use','scope','exp','iat']:
            e=self.event();del e['requestContext']['authorizer']['jwt']['claims'][k]
            with self.subTest(claim=k): self.assertIsNone(self.auth.authenticate(e,CTX))
    def test_wrong_claims_deny(self):
        for k,v in [('iss','https://other.invalid'),('aud','other'),('client_id','other'),('sub',''),('token_use','id'),
                    ('exp',str(NOW//1000)),('exp','no'),('iat',str(NOW//1000+1)),('iat',None),('iat',True),('iat','1e3')]:
            e=self.event();e['requestContext']['authorizer']['jwt']['claims'][k]=v
            with self.subTest(claim=k,value=v): self.assertEqual(401,self.host(e,CTX)['statusCode'])
    def test_excess_scopes_even_when_gateway_agrees(self):
        for scope in ['openid','profile','jel-v6/admin']:
            e=self.event();j=e['requestContext']['authorizer']['jwt'];j['scopes'].append(scope);j['claims']['scope']+=' '+scope
            self.assertEqual(401,self.host(e,CTX)['statusCode'])
    def test_read_only_scope_cannot_write(self):
        e=self.event();j=e['requestContext']['authorizer']['jwt'];j['scopes']=['jel-v6/read'];j['claims']['scope']='jel-v6/read'
        self.assertEqual(403,self.host(e,CTX)['statusCode'])
    def test_sender_receiver_instruction_binding(self):
        for field in ['sender','receiver','instruction']:
            e=self.event();f=fixture();f['envelope'][field]='other';sign(f['envelope']);e['body']=json.dumps(f)
            with self.subTest(field=field): self.assertEqual(403,self.host(e,CTX)['statusCode'])
    def test_unknown_subject_denied(self):
        e=self.event();e['requestContext']['authorizer']['jwt']['claims']['sub']='other'
        self.assertEqual(403,self.host(e,CTX)['statusCode'])
    def test_header_spoof_does_not_supply_absent_claims(self):
        e=self.event();del e['requestContext']['authorizer'];e['headers']['authorization']='synthetic-unverified';e['headers']['sub']=PROJECTED['claims']['sub']
        self.assertEqual(401,self.host(e,CTX)['statusCode'])


class SafetyTests(unittest.TestCase):
    def test_no_reservation_in_candidate_or_generator(self):
        self.assertTrue(check(template()))
        self.assertEqual(template(),json.loads((ROOT/'infra/template.json').read_text()))
        for value in [0,1,2,True,{'Ref':'Limit'}]:
            t=template();t['Resources']['Function']['Properties']['ReservedConcurrentExecutions']=value
            with self.assertRaises(AssertionError): check(t)
    def test_throttle_regressions_denied(self):
        for change in [{'ThrottlingBurstLimit':10,'ThrottlingRateLimit':5},{}, {'ThrottlingBurstLimit':2,'ThrottlingRateLimit':100}]:
            t=template();t['Resources']['Stage']['Properties']['DefaultRouteSettings']=change
            with self.assertRaises(AssertionError): check(t)
        t=template();t['Resources']['Stage']['Properties']['RouteSettings']={'POST /v6/events':{'ThrottlingRateLimit':100}}
        with self.assertRaises(AssertionError): check(t)
    def test_legacy_resource_ids_denied(self):
        for name in ['DFSS-ColdStart','us-os-brain','kirmld16gb','qjiuor3yak','p9qtqpd8mc','JakobLambdaExecutionRole','DFSS_SessionState','jakob-memory-store','jakob-identity-profiles','us-os-memory']:
            t=template();t['Description']=name
            with self.subTest(name=name),self.assertRaises(AssertionError): check(t)
    def test_outcomes_are_finite_and_have_no_request_fields(self):
        for status,outcome in [(201,'accepted'),(401,'rejected'),(403,'rejected'),(429,'rejected'),(503,'unavailable'),('payload','unavailable')]:
            with redirect_stdout(io.StringIO()) as out: emit_outcome(status)
            self.assertEqual({'kind':'v6_outcome','outcome':outcome},json.loads(out.getvalue()))
    def test_handler_emits_one_sanitized_record(self):
        for status in [201,401,503]:
            response={'statusCode':status,'body':'synthetic-sensitive'}
            with patch.object(activation,'_host',return_value=response),redirect_stdout(io.StringIO()) as out:
                self.assertEqual(response,activation.handler({'secret':'synthetic-sensitive'},None))
            self.assertEqual(1,len(out.getvalue().splitlines()));self.assertNotIn('sensitive',out.getvalue())
    def test_startup_failure_signal(self):
        with patch.object(activation,'_host',None),patch.object(activation,'compose',side_effect=ValueError('synthetic-sensitive')),redirect_stdout(io.StringIO()) as out:
            self.assertEqual(503,activation.handler({},None)['statusCode'])
        self.assertEqual('unavailable',json.loads(out.getvalue())['outcome']);self.assertNotIn('sensitive',out.getvalue())
    def test_logging_failure_does_not_change_receipt(self):
        with patch('builtins.print',side_effect=OSError('synthetic')): emit_outcome(201)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);p=Path(self.temp.name)
        self.paths={n:p/n for n in ['template','artifact','bindings']}
        self.paths['template'].write_text(json.dumps(template()));self.paths['artifact'].write_bytes(b'synthetic artifact')
        self.paths['bindings'].write_text(json.dumps(policy()))
        self.m=json.loads((ROOT/'release/manifest.unapproved.json').read_text())
        self.m.update(approval={'status':'APPROVED','review_reference':'synthetic-review-only'},account_id='111111111111',region='us-east-1',
            issuer='https://synthetic.invalid',audience='v6-audience',client_id='client',allowed_scopes=['jel-v6/read','jel-v6/write'],
            binding_version='v1',source_commit='a'*40,artifact={'bucket':'synthetic-v6-artifact','key':'candidate.zip','version':'synthetic-version'})
        for k,n in [('template_sha256','template'),('artifact_sha256','artifact'),('binding_sha256','bindings')]:
            self.m[k]=hashlib.sha256(self.paths[n].read_bytes()).hexdigest()
        self.provenance={'source_inputs':[{'path':'aws/isolated-v6/infra/template.json','sha256':self.m['template_sha256']},{'path':'aws/isolated-v6/aws_v6/bindings.json','sha256':self.m['binding_sha256']}],'source_commit':'a'*40,'artifact_sha256':self.m['artifact_sha256'],
            'tests':{'passed':True,'tests_run':1,'failures':0,'errors':0,'skipped':0},'cloudformation':{'passed':True}}
    def validate(self,m=None):
        return validate(self.m if m is None else m,expected_source='a'*40,provenance=self.provenance,**self.paths)
    def test_consistency_never_authorizes_deployment(self):
        self.assertEqual(False,self.validate()['deployment_authorized'])
    def test_unapproved_placeholder_rejected(self):
        with self.assertRaises(ValueError):self.validate(read_json(ROOT/'release/manifest.unapproved.json'))
    def test_missing_and_unknown_fields(self):
        for k in self.m:
            m=copy.deepcopy(self.m);del m[k]
            with self.subTest(field=k),self.assertRaises(ValueError):self.validate(m)
        m=copy.deepcopy(self.m);m['bypass']=True
        with self.assertRaises(ValueError):self.validate(m)
    def test_wrong_approval_hash_source_binding_identity(self):
        for k,v in [('approval',{'status':'UNAPPROVED','review_reference':'test'}),('artifact_sha256','0'*64),('template_sha256','0'*64),
                    ('binding_sha256','0'*64),('source_commit','b'*40),('binding_version','v2'),('client_id','other'),('issuer','https://other.invalid'),
                    ('allowed_scopes',['openid']),('account_id','000000000000')]:
            m=copy.deepcopy(self.m);m[k]=v
            with self.subTest(field=k),self.assertRaises(ValueError):self.validate(m)
    def test_tampered_bytes_fail(self):
        for n,p in self.paths.items():
            original=p.read_bytes();p.write_bytes(original+b' ')
            with self.subTest(file=n),self.assertRaises(ValueError):self.validate()
            p.write_bytes(original)
    def test_failed_provenance_denied(self):
        self.provenance['tests']['passed']=False
        with self.assertRaises(ValueError):self.validate()
    def test_duplicate_members_denied(self):
        p=Path(self.temp.name)/'bad.json';p.write_text('{"approval":true,"approval":false}')
        with self.assertRaises(ValueError):read_json(p)
    def test_legacy_artifact_bucket_denied(self):
        self.m['artifact']['bucket']='jakob-asset-store'
        with self.assertRaises(ValueError):self.validate()
