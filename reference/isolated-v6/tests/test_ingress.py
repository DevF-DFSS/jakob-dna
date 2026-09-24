import base64
import copy
import dataclasses
import hashlib
import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
from urllib.parse import quote

from isolated_v6.auth import Binding, Principal, Registry
from isolated_v6.contract import PROFILE, canonical
from isolated_v6.envelope import FIELDS, canonical_bytes
from isolated_v6.http import MAX_BYTES
from isolated_v6.service import Ingress
from isolated_v6.store import MemoryStore, StoreUnavailable

NOW = 1790251200000  # 2026-09-24T12:00:00Z
P = Principal('https://synthetic.invalid', 'subject', 'client', frozenset({'jel-v6/write', 'jel-v6/read'}))
Q = Principal(P.issuer, 'other', P.client_id, P.scopes)


def sign(e):
    e['integrity'] = {'algorithm': 'SHA-256', 'digest': hashlib.sha256(canonical_bytes(e)).hexdigest()}
    return e


def fixture():
    e = sign(dict(protocol='JEL-JKB/6.0', sender='sender', receiver='receiver', timestamp='2020-01-01T00:00:00.000Z',
                  context_mode='HIGH_BANDWIDTH', jel='🐈📦 café e\u0301', payload_ref='urn:synthetic:test',
                  instruction='ACCEPT', fallback='STOP'))
    return dict(profile=PROFILE, event_id='11111111-1111-4111-8111-111111111111', issued_at='2026-09-24T12:00:00.000Z', envelope=e)


def http(body=None):
    return dict(version='2.0', routeKey='POST /v6/events', rawPath='/v6/events', rawQueryString='',
                headers={'content-type': 'application/json'}, isBase64Encoded=False,
                requestContext={'apiId': 'synthetic-api', 'stage': 'offline', 'http': {'method': 'POST'}},
                body=json.dumps(fixture() if body is None else body, ensure_ascii=False))


class IngressTests(unittest.TestCase):
    def setUp(self):
        b = Binding('tenant-a', frozenset({'sender'}), frozenset({'receiver'}), frozenset({'ACCEPT'}), 'v1')
        self.registry = Registry({P.key: b, Q.key: dataclasses.replace(b, tenant='tenant-b')})
        self.store = MemoryStore()
        self.now = NOW
        self.app = Ingress(self.registry, self.store, lambda: self.now, api_id='synthetic-api', stage='offline')

    def send(self, event=None, principal=P):
        return self.app.handle(http() if event is None else event, trusted_principal=principal)

    def assert_status(self, status, event=None, principal=P):
        response = self.send(event, principal)
        self.assertEqual(status, response['statusCode'], response)
        return json.loads(response['body'])

    def reject_without_io(self, event, status=400, principal=P):
        class Spy:
            def insert_if_absent(self, row): raise AssertionError('storage touched')
            def get(self, *args): raise AssertionError('storage touched')
        self.app.store = Spy()
        self.assert_status(status, event, principal)

    def get_event(self, sender='sender', uid=None):
        e = http()
        e.update(routeKey='GET /v6/senders/{sender}/events/{event_id}',
                 rawPath='/v6/senders/' + quote(sender, safe='') + '/events/' + (uid or fixture()['event_id']), body='')
        e['requestContext']['http']['method'] = 'GET'
        return e

    def test_accept_and_retry_stable_receipt(self):
        receipt = self.assert_status(201)
        self.now += 10000
        self.assertEqual(receipt, self.assert_status(200))

    def test_conflicting_body(self):
        self.assert_status(201)
        w = fixture(); w['envelope']['jel'] = 'changed'; sign(w['envelope'])
        self.assert_status(409, http(w))
        self.assertEqual(NOW, self.assert_status(200, self.get_event())['accepted_at_ms'])

    def test_changed_issued_at_conflicts(self):
        self.assert_status(201)
        w = fixture(); w['issued_at'] = '2026-09-24T12:00:01Z'
        self.assert_status(409, http(w))

    def test_tenant_isolation(self):
        self.assert_status(201)
        self.assert_status(404, self.get_event(), Q)
        self.assert_status(201, principal=Q)

    def test_unknown_and_revoked(self):
        unknown = dataclasses.replace(P, subject='unknown')
        self.assert_status(403, principal=unknown)
        self.assert_status(201)
        self.registry.revoke(P.key)
        self.assert_status(403)
        self.assert_status(403, self.get_event())

    def test_untrusted_authorizer_context(self):
        e = http(); e['requestContext']['authorizer'] = {'jwt': {'claims': {'iss': P.issuer, 'sub': P.subject, 'client_id': P.client_id}}}
        self.reject_without_io(e, 401, None)
        self.reject_without_io(e, 401, dataclasses.asdict(P))

    def test_scope_denial(self):
        self.reject_without_io(http(), 403, dataclasses.replace(P, scopes=frozenset({'jel-v6/read'})))
        self.assert_status(403, self.get_event(), dataclasses.replace(P, scopes=frozenset({'jel-v6/write'})))

    def test_freshness_boundaries(self):
        for offset, status in [(-30000, 201), (300000, 200), (-30001, 422), (300001, 422)]:
            self.now = NOW + offset
            self.assert_status(status)

    def test_receipt_recovery_after_stale_post(self):
        saved = self.assert_status(201)
        self.now += 300001
        self.assert_status(422)
        self.assertEqual(saved, self.assert_status(200, self.get_event()))

    def test_missing_and_unauthorized_receipt(self):
        self.assert_status(404, self.get_event())
        self.assert_status(403, self.get_event('other'))

    def test_parallel_same_request(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses = list(pool.map(lambda _: self.send(), range(32)))
        self.assertEqual(1, sum(r['statusCode'] == 201 for r in responses))
        self.assertEqual(31, sum(r['statusCode'] == 200 for r in responses))
        self.assertEqual(1, len({r['body'] for r in responses}))

    def test_parallel_independent_events(self):
        def submit(_):
            w = fixture(); w['event_id'] = str(uuid4())
            return self.send(http(w))
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(submit, range(32)))
        self.assertTrue(all(r['statusCode'] == 201 for r in results))
        self.assertEqual(32, len({r['body'] for r in results}))

    def test_parallel_conflicting_requests(self):
        requests = []
        for i in range(16):
            w = fixture(); w['envelope']['jel'] = str(i); sign(w['envelope']); requests.append(http(w))
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(self.send, requests))
        self.assertEqual(1, sum(r['statusCode'] == 201 for r in results))
        self.assertEqual(15, sum(r['statusCode'] == 409 for r in results))

    def test_no_mutation(self):
        e = http(); original = copy.deepcopy(e)
        self.assert_status(201, e)
        self.assertEqual(original, e)
        row = self.store.get(canonical(['tenant-a', 'sender']).decode(), 'EVENT#' + fixture()['event_id'])
        with self.assertRaises(dataclasses.FrozenInstanceError): row.request_digest = 'changed'
        with self.assertRaises(dataclasses.FrozenInstanceError): row.receipt.status = 'changed'
        decoded = json.loads(row.wrapper_bytes); decoded['envelope']['jel'] = 'changed'
        self.assertEqual(fixture(), json.loads(row.wrapper_bytes))

    def test_unicode_canonical_equivalence(self):
        e = http(); w = fixture()
        self.assert_status(201, e)
        e['body'] = json.dumps(dict(reversed(list(w.items()))), ensure_ascii=True, indent=2)
        self.assert_status(200, e)
        w['envelope']['jel'] = w['envelope']['jel'].replace('e\u0301', 'é')
        self.reject_without_io(http(w), 422)

    def test_known_canonical_vector(self):
        e = {'jel': '🐈', 'sender': 'é', 'integrity': {'ignored': True}}
        self.assertEqual(b'{"jel":"\xf0\x9f\x90\x88","sender":"\xc3\xa9"}', canonical_bytes(e))

    def test_duplicate_members_at_each_depth(self):
        text = http()['body']
        for key in ['profile', 'sender', 'algorithm']:
            e = http(); e['body'] = text.replace('"' + key + '":', '"' + key + '":null,"' + key + '":', 1)
            self.reject_without_io(e)

    def test_base64(self):
        e = http(); e['body'] = base64.b64encode(e['body'].encode()).decode(); e['isBase64Encoded'] = True
        self.assert_status(201, e)

    def test_request_limit_raw_and_base64(self):
        base = http()['body']
        raw = base + ' ' * (MAX_BYTES - len(base.encode()))
        for encoded in (False, True):
            e = http(); e['isBase64Encoded'] = encoded
            e['body'] = base64.b64encode(raw.encode()).decode() if encoded else raw
            self.assertIn(self.send(e)['statusCode'], (200, 201))
            e['body'] = base64.b64encode((raw + ' ').encode()).decode() if encoded else raw + ' '
            self.assert_status(413, e)

    def test_lost_response_retry(self):
        underlying = self.store
        class Lost:
            def insert_if_absent(self, row):
                underlying.insert_if_absent(row)
                raise StoreUnavailable('synthetic-sensitive-detail')
            def get(self, *args): return underlying.get(*args)
        self.app.store = Lost()
        self.assert_status(503)
        self.app.store = underlying
        self.assert_status(200)

    def test_missing_conflict_read(self):
        class Missing:
            def insert_if_absent(self, row): return False
            def get(self, *args): return None
        self.app.store = Missing()
        self.assert_status(503)

    def test_sanitized_exception_and_logs(self):
        class Broken:
            def insert_if_absent(self, row): raise RuntimeError('synthetic-sensitive-detail')
        self.app.store = Broken()
        with self.assertLogs('isolated_v6.service', level='ERROR') as logs:
            response = self.send()
        self.assertEqual(500, response['statusCode'])
        self.assertNotIn('synthetic-sensitive-detail', str(response) + str(logs.output))
        self.assertNotIn('payload_ref', str(logs.output))

    def test_get_rejects_encoded_path_ambiguity(self):
        e = self.get_event(); e['rawPath'] = e['rawPath'].replace('sender/events', '%73ender/events')
        self.reject_without_io(e)

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError): Registry({P.key: {}})
        with self.assertRaises(ValueError): Binding('', frozenset({'s'}), frozenset({'r'}), frozenset({'i'}), 'v')
        with self.assertRaises(ValueError): dataclasses.replace(P, scopes=['jel-v6/write'])


def add_case(name, modify, status=400):
    def test(self):
        e = http(); modify(e)
        self.reject_without_io(e, status)
    setattr(IngressTests, 'test_reject_' + name, test)


for field in FIELDS:
    # Changing each signed field without rehashing must reject before storage.
    status = 409 if field == 'protocol' else 400 if field == 'timestamp' else 422
    add_case('tampered_' + field, lambda e, f=field: e.update(body=json.dumps(dict(fixture(), envelope=dict(fixture()['envelope'], **{f: 'tampered'})))), status)

for name, key, value, status in [
    ('version', 'version', '1.0', 400), ('body_object', 'body', {}, 400),
    ('encoding_flag', 'isBase64Encoded', 1, 400), ('query', 'rawQueryString', 'token=synthetic', 400),
    ('wrong_route', 'routeKey', '$default', 404), ('wrong_path', 'rawPath', '/session', 404),
    ('headers_type', 'headers', [], 400), ('invalid_json', 'body', '{', 400),
    ('array_root', 'body', '[]', 400), ('null_root', 'body', 'null', 400),
    ('nan', 'body', '{"x":NaN}', 400), ('deep', 'body', '[' * 17 + '0' + ']' * 17, 400),
    ('huge_raw', 'body', '🐈' * MAX_BYTES, 413), ('missing_body', 'body', None, 400),
    ('surrogate_raw', 'body', '\ud800', 400), ('bom', 'body', '\ufeff{}', 400),
]:
    add_case(name, lambda e, k=key, v=value: e.update({k: v}), status)

for name, changes, status in [
    ('missing_integrity', {'integrity': None}, 422), ('bad_algorithm', {'integrity': {'algorithm': 'sha256', 'digest': '0'*64}}, 422),
    ('numeric_field', {'jel': 3}, 400), ('blank_field', {'jel': ' '}, 400), ('surrogate_field', {'jel': '\ud800'}, 400),
    ('oversize_sender', {'sender': 'x'*257}, 413), ('oversize_jel', {'jel': 'x'*4097}, 413),
    ('unknown_envelope_field', {'tenant': 'other'}, 400), ('bad_timestamp_date', {'timestamp': '2026-02-30T00:00:00Z'}, 400),
]:
    add_case(name, lambda e, c=changes: e.update(body=json.dumps(dict(fixture(), envelope=dict(fixture()['envelope'], **c)))), status)

for name, value, status in [('profile', 'legacy', 409), ('event_id', 'bad', 400), ('issued_at', '2026-09-24T12:00:00.0001Z', 400), ('tenant', 'injected', 400)]:
    add_case('wrapper_' + name, lambda e, k=name, v=value: e.update(body=json.dumps(dict(fixture(), **{k: v}))), status)

for field in ['sender', 'receiver', 'instruction']:
    def change(e, f=field):
        w = fixture(); w['envelope'][f] = 'unauthorized'; sign(w['envelope']); e['body'] = json.dumps(w)
    add_case('binding_' + field, change, 403)

for name, text in [('invalid_base64', '!'), ('invalid_utf8', '/w=='), ('noncanonical_base64', 'Zh==')]:
    add_case(name, lambda e, v=text: e.update(body=v, isBase64Encoded=True))

add_case('duplicate_header', lambda e: e['headers'].update({'Content-Type': 'application/json'}))
add_case('protocol_header', lambda e: e['headers'].update({'X-JEL-Protocol-Version': 'old'}), 409)
add_case('content_type', lambda e: e['headers'].update({'content-type': 'text/plain'}), 415)
add_case('wrong_api', lambda e: e['requestContext'].update(apiId='other'), 403)
add_case('wrong_stage', lambda e: e['requestContext'].update(stage='production'), 403)
add_case('compressed', lambda e: e['headers'].update({'content-encoding': 'gzip'}))


# Additional valid-shape tampering and parser edge cases.
add_case('signed_valid_timestamp', lambda e: e.update(body=json.dumps(dict(fixture(), envelope=dict(fixture()['envelope'], timestamp='2020-01-02T00:00:00Z')))), 422)
add_case('integrity_absent', lambda e: e.update(body=json.dumps(dict(fixture(), envelope={k:v for k,v in fixture()['envelope'].items() if k != 'integrity'}))), 422)
add_case('uppercase_digest', lambda e: e.update(body=json.dumps(dict(fixture(), envelope=dict(fixture()['envelope'], integrity={'algorithm':'SHA-256','digest':fixture()['envelope']['integrity']['digest'].upper()})))), 422)
add_case('envelope_null', lambda e: e.update(body=json.dumps(dict(fixture(), envelope=None))))
add_case('uuid_v1', lambda e: e.update(body=json.dumps(dict(fixture(), event_id='11111111-1111-1111-8111-111111111111'))))
add_case('missing_wrapper_field', lambda e: e.update(body=json.dumps({k:v for k,v in fixture().items() if k != 'issued_at'})))
add_case('timezone_offset', lambda e: e.update(body=json.dumps(dict(fixture(), issued_at='2026-09-24T13:00:00+01:00'))))
add_case('bad_date', lambda e: e.update(body=json.dumps(dict(fixture(), issued_at='2026-02-30T12:00:00Z'))))
add_case('json_trailing', lambda e: e.update(body=e['body']+'{}'))
add_case('base64_oversized', lambda e: e.update(body='A'*90000, isBase64Encoded=True), 413)
add_case('header_newline', lambda e: e['headers'].update({'x-test': 'bad\nvalue'}))
add_case('http_context_type', lambda e: e.update(requestContext=[]))

if __name__ == '__main__': unittest.main()
