"""Synthetic offline decision tests; no credentials, AWS SDK, or network access."""
import copy
import unittest
from datetime import datetime
from model import Model, PROFILE, Rejected, digest

P = ('https://issuer.invalid', 'synthetic-subject', 'synthetic-client')
Q = ('https://issuer.invalid', 'other-subject', 'synthetic-client')
NOW = datetime.fromisoformat('2026-09-24T12:00:00+00:00').timestamp()


def fixture():
    envelope = dict(protocol='JEL-JKB/6.0', sender='sender', receiver='receiver',
                    timestamp='2020-01-01T00:00:00.000Z', context_mode='HIGH_BANDWIDTH',
                    jel='synthetic', payload_ref='urn:synthetic:test',
                    instruction='ACCEPT', fallback='STOP')
    envelope['integrity'] = {'algorithm': 'SHA-256', 'digest': digest(envelope)}
    return dict(profile=PROFILE, event_id='11111111-1111-4111-8111-111111111111',
                issued_at='2026-09-24T12:00:00.000Z', envelope=envelope)


class Decisions(unittest.TestCase):
    def setUp(self):
        binding = dict(tenant='tenant-a', senders=['sender'], receivers=['receiver'], instructions=['ACCEPT'])
        self.model = Model({P: binding, Q: dict(binding, tenant='tenant-b')})
        self.body = fixture()

    def reject(self, status, principal=P, now=NOW):
        count = len(self.model.rows)
        with self.assertRaises(Rejected) as result:
            self.model.submit(principal, self.body, now)
        self.assertEqual(status, result.exception.status)
        self.assertEqual(count, len(self.model.rows))

    def test_missing_auth(self): self.reject(401, None)
    def test_unknown_principal(self): self.reject(403, ('wrong', 'wrong', 'wrong'))
    def test_sender_spoof(self):
        self.body['envelope']['sender'] = 'other'
        self.reject(403)
    def test_receiver_denial(self):
        self.body['envelope']['receiver'] = 'other'
        self.reject(403)
    def test_instruction_denial(self):
        self.body['envelope']['instruction'] = 'EXECUTE'
        self.reject(403)
    def test_tenant_injection(self):
        self.body['tenant'] = 'tenant-b'
        self.reject(422)
    def test_missing_integrity(self):
        del self.body['envelope']['integrity']
        self.reject(422)
    def test_wrong_integrity(self):
        self.body['envelope']['jel'] = 'tampered'
        self.reject(422)
    def test_freshness_boundaries(self):
        for offset in (-30, 300):
            with self.subTest(offset=offset):
                self.assertIn(self.model.submit(P, self.body, NOW + offset)[0], (200, 201))
        for offset in (-30.001, 300.001):
            self.reject(422, now=NOW + offset)
    def test_retry_original_receipt(self):
        first = self.model.submit(P, self.body, NOW)
        retry = self.model.submit(P, self.body, NOW + 10)
        self.assertEqual((first[0], retry[0]), (201, 200))
        self.assertEqual(first[1], retry[1])
        self.assertEqual(1, len(self.model.rows))
    def test_changed_wrapper_conflict(self):
        self.model.submit(P, self.body, NOW)
        self.body['issued_at'] = '2026-09-24T12:00:01.000Z'
        self.reject(409)
    def test_distinct_events_same_time(self):
        self.model.submit(P, self.body, NOW)
        self.body['event_id'] = '22222222-2222-4222-8222-222222222222'
        self.assertEqual(201, self.model.submit(P, self.body, NOW)[0])
        self.assertEqual(2, len(self.model.rows))
    def test_tenant_isolation(self):
        self.model.submit(P, self.body, NOW)
        with self.assertRaises(Rejected) as result:
            self.model.receipt(Q, 'sender', self.body['event_id'])
        self.assertEqual(404, result.exception.status)
        self.assertEqual(201, self.model.submit(Q, self.body, NOW)[0])
    def test_stale_retry_get_recovery(self):
        receipt = self.model.submit(P, self.body, NOW)[1]
        self.reject(422, now=NOW + 301)
        self.assertEqual(receipt, self.model.receipt(P, 'sender', self.body['event_id']))
    def test_revocation_denies_retry_and_read(self):
        self.model.submit(P, self.body, NOW)
        del self.model.bindings[P]
        self.reject(403)
        with self.assertRaises(Rejected) as result:
            self.model.receipt(P, 'sender', self.body['event_id'])
        self.assertEqual(403, result.exception.status)
    def test_historical_timestamp_preserved(self):
        self.model.submit(P, self.body, NOW)
        self.assertEqual('2020-01-01T00:00:00.000Z', next(iter(self.model.rows.values()))['wrapper']['envelope']['timestamp'])
    def test_no_mutation(self):
        before = copy.deepcopy(self.body)
        receipt = self.model.submit(P, self.body, NOW)[1]
        receipt['status'] = 'tampered'
        self.assertEqual(before, self.body)
        self.assertEqual('accepted', self.model.receipt(P, 'sender', self.body['event_id'])['status'])
    def test_uuid_profile_and_time_shape(self):
        for field, value in [('event_id', 'not-uuid'), ('profile', 'legacy'), ('issued_at', '2026-09-24T12:00:00')]:
            self.body = fixture()
            self.body[field] = value
            self.reject(422)


if __name__ == '__main__':
    unittest.main()
