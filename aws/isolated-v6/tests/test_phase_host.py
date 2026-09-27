import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from aws_v6.phase_host import capability, compose_phase, config_digest, CONFIG_KEYS


class PhaseHostTests(unittest.TestCase):
    def setUp(self):
        self.env = {k:'synthetic-'+k for k in CONFIG_KEYS}
        self.now = 100
        self.c = {'schema_version':'jel-v6-capability/1','mode':'TEST',
                  'config_sha256':config_digest(self.env),'starts_at':100,'expires_at':200,
                  'principals':[['issuer','subject','client']]}
        self.calls = []
        self.principal = SimpleNamespace(key=('issuer','subject','client'))
        self.host = SimpleNamespace(authentication=SimpleNamespace(authenticate=lambda e,c:self.principal),
                                    ingress=SimpleNamespace(handle=lambda e,**kw:{'statusCode':202}))
    def make(self):
        raw = json.dumps(self.c).encode()
        self.env['CAPABILITY_SHA256'] = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'capability.json';p.write_bytes(raw)
            def factory(*a,**kw):self.calls.append(1);return self.host
            return compose_phase(self.env,capability_path=p,factory=factory,clock_ms=lambda:self.now*1000)
    def test_closed_never_constructs_sdk(self):
        self.c.update(mode='CLOSED',config_sha256=None,starts_at=None,expires_at=None,principals=[])
        self.env={}
        host=self.make();self.assertEqual(host({},None)['statusCode'],503);self.assertEqual(self.calls,[])
    def test_intended_principal_with_current_capability(self):
        self.assertEqual(self.make()({},None)['statusCode'],202)
    def test_other_principal_and_forged_body_cannot_open(self):
        self.principal=SimpleNamespace(key=('issuer','other','client'))
        self.assertEqual(self.make()({'approved':'DevF','mode':'SANDBOX'},None)['statusCode'],403)
    def test_expiry_enforced_on_warm_host(self):
        h=self.make();self.now=200;self.assertEqual(h({},None)['statusCode'],503)
    def test_future_window_fails_before_sdk(self):
        self.now=99
        with self.assertRaises(ValueError):self.make()
        self.assertEqual(self.calls,[])
    def test_wrong_config_hash(self):
        self.env['EXPECTED_API_ID']='changed'
        with self.assertRaises(ValueError):self.make()
    def test_wrong_capability_hash(self):
        with self.assertRaises(ValueError):capability(json.dumps(self.c).encode(),'0'*64,self.env)
    def test_duplicate_json_and_extra_fields(self):
        raw=b'{"mode":"TEST","mode":"CLOSED"}'
        with self.assertRaises(ValueError):capability(raw,hashlib.sha256(raw).hexdigest(),self.env)
        self.c['approved_by']='DevF'
        with self.assertRaises(ValueError):self.make()
    def test_unbounded_or_duplicate_principals_reject(self):
        self.c['principals']*=2
        with self.assertRaises(ValueError):self.make()
        self.c['principals']=[]
        with self.assertRaises(ValueError):self.make()
    def test_test_window_is_short_and_integer(self):
        for end in [True,100,3701,200.0]:
            self.c['expires_at']=end
            with self.assertRaises(ValueError):self.make()
    def test_repository_capability_remains_closed(self):
        c=json.loads((Path(__file__).resolve().parents[1]/'aws_v6/capability.json').read_text())
        self.assertEqual(c['mode'],'CLOSED');self.assertEqual(c['principals'],[])
