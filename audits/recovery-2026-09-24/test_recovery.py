"""Offline characterization tests; known gaps are asserted, not fixed or endorsed."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent
CODE = ROOT / 'source/03_DFSS_Operations/Codebases'
if not CODE.exists():
    CODE = ROOT.parents[1] / '03_DFSS_Operations/Codebases'

def load(name):
    spec = importlib.util.spec_from_file_location(name, CODE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.writes = []
        fake = types.ModuleType('boto3')
        fake.resource = lambda service: types.SimpleNamespace(Table=lambda name: types.SimpleNamespace(put_item=lambda **kw: self.writes.append((name, kw))))
        with patch.dict(sys.modules, {'boto3': fake}), patch.dict(os.environ, {'JEL_PROTOCOL_VERSION':'2.6B','DRIFT_CHECK_ENABLED':'true','TABLE_NAME':'offline-test-table'}):
            self.handler = load('lambda_function')
        self.handler.LOGGER.disabled = True
        self.codec = load('py_emoji_codec')

    def invoke(self, body, version='2.6B'):
        return self.handler.lambda_handler({'body': body, 'headers': {'x-jel-protocol-version':version}}, None)

    def test_valid_digest(self):
        digest = hashlib.sha256(b'{}').hexdigest()
        self.assertTrue(self.handler.verify_from_buffer('{}', digest))

    def test_invalid_and_missing_digest(self):
        for digest in (None, '', '0'*64):
            self.assertFalse(self.handler.verify_from_buffer('{}', digest))

    def test_drift_blocks_write(self):
        self.assertEqual(self.invoke({}, 'wrong')['statusCode'],409)
        self.assertEqual(self.writes, [])

    def test_known_gap_missing_integrity_still_writes(self):
        self.assertEqual(self.invoke({})['statusCode'],200)
        self.assertFalse(self.writes[0][1]['Item']['integrity_ok'])

    def test_known_gap_bad_integrity_still_writes(self):
        self.assertEqual(self.invoke({'buffer_sha256':'0'*64})['statusCode'],200)
        self.assertFalse(self.writes[0][1]['Item']['integrity_ok'])

    def test_known_gap_digest_does_not_cover_stored_value(self):
        digest = hashlib.sha256(b'{}').hexdigest()
        for value in ('first', 'changed'):
            self.invoke({'payload':{},'buffer_sha256':digest,'value':value})
        self.assertEqual([x[1]['Item']['value'] for x in self.writes],['first','changed'])
        self.assertTrue(all(x[1]['Item']['integrity_ok'] for x in self.writes))

    def test_known_gap_v6_envelope_not_parsed(self):
        envelope={'protocol':'JEL-JKB/6.0','sender':'test','receiver':'Companion_External','timestamp':'2026-09-24T00:00:00Z','payload_ref':'offline','integrity':{'algorithm':'SHA-256','digest':'0'*64},'instruction':'REHYDRATE_AND_VALIDATE'}
        self.assertEqual(self.invoke(envelope)['statusCode'],200)
        self.assertEqual(self.writes[0][1]['Item']['key'],'SYSTEM_STATE_V6')
        self.assertFalse(self.writes[0][1]['Item']['integrity_ok'])

    def test_v6_protocol_header_is_drift(self):
        self.assertEqual(self.invoke({},'JEL-JKB/6.0')['statusCode'],409)
        self.assertEqual(self.writes,[])

    def test_malformed_json_fails_without_write(self):
        self.assertEqual(self.invoke('{')['statusCode'],500)
        self.assertEqual(self.writes,[])

    def test_nonobject_json_fails_without_write(self):
        for body in ('[]','null','1'):
            self.assertEqual(self.invoke(body)['statusCode'],500)
        self.assertEqual(self.writes,[])

    def test_unicode_serialization(self):
        payload={'text':'🐈📦'}
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(self.invoke(json.dumps({'payload':payload,'buffer_sha256':digest}))['statusCode'],200)
        self.assertTrue(self.writes[0][1]['Item']['integrity_ok'])

    def test_header_case_is_not_normalized(self):
        response=self.handler.lambda_handler({'body':{},'headers':{'X-JEL-Protocol-Version':'2.6B'}},None)
        self.assertEqual(response['statusCode'],409)
        self.assertEqual(self.writes,[])

    def test_codec_balanced(self):
        translated=self.codec.translate_source_text('if True 🍇\nx = 1\n🍉')
        compile(translated,'<offline>','exec')
        self.assertIn('    x = 1',translated)

    def test_codec_unclosed(self):
        with self.assertRaises(SyntaxError):
            self.codec.translate_source_text('if True 🍇\nx = 1')

    def test_known_gap_extra_close_is_accepted(self):
        self.assertEqual(self.codec.translate_source_text('🍉\nx = 1'),'\nx = 1\n')

if __name__ == '__main__':
    unittest.main()
