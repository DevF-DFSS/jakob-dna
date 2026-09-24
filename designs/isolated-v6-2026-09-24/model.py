"""Offline design model, NOT a handler, JWT verifier, or DynamoDB implementation."""
import copy
import hashlib
import json
from datetime import datetime
from uuid import UUID

PROFILE = 'JEL-JKB/6.0-isolated/1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


class Rejected(Exception):
    def __init__(self, status):
        self.status = status


class Model:
    """Trusted principal tuple is supplied by a simulated authentication boundary.

    Registry maps (issuer, subject, client_id) to tenant/senders/receivers/instructions.
    Sequential dict operations intentionally make NO service atomicity guarantee.
    Full strict wire parsing and envelope validation remain implementation gates.
    """
    def __init__(self, bindings):
        self.bindings = copy.deepcopy(bindings)
        self.rows = {}

    def authorize(self, principal, sender):
        if principal is None:
            raise Rejected(401)
        binding = self.bindings.get(principal)
        if binding is None or sender not in binding['senders']:
            raise Rejected(403)
        return binding

    def submit(self, principal, wrapper, now):
        if set(wrapper) != {'profile', 'event_id', 'issued_at', 'envelope'}:
            raise Rejected(422)
        if wrapper['profile'] != PROFILE:
            raise Rejected(422)
        try:
            uid = UUID(wrapper['event_id'])
            if uid.version != 4 or str(uid) != wrapper['event_id']:
                raise ValueError()
            issued = wrapper['issued_at']
            if not issued.endswith('Z'):
                raise ValueError()
            seconds = datetime.fromisoformat(issued[:-1] + '+00:00').timestamp()
        except (ValueError, TypeError, AttributeError):
            raise Rejected(422) from None
        envelope = wrapper['envelope']
        binding = self.authorize(principal, envelope['sender'])
        if (envelope['receiver'] not in binding['receivers'] or
                envelope['instruction'] not in binding['instructions']):
            raise Rejected(403)
        fields = {key: value for key, value in envelope.items() if key != 'integrity'}
        if envelope.get('integrity') != {'algorithm': 'SHA-256', 'digest': digest(fields)}:
            raise Rejected(422)
        if not -30 <= now - seconds <= 300:
            raise Rejected(422)
        key = (canonical([binding['tenant'], envelope['sender']]), 'EVENT#' + str(uid))
        request_digest = digest(wrapper)
        if key in self.rows:
            row = self.rows[key]
            if row['request_digest'] != request_digest:
                raise Rejected(409)
            return 200, copy.deepcopy(row['receipt'])
        receipt = {'event_id': str(uid), 'status': 'accepted', 'accepted_at_ms': int(now * 1000)}
        self.rows[key] = {'request_digest': request_digest, 'receipt': receipt,
                          'wrapper': copy.deepcopy(wrapper)}
        return 201, copy.deepcopy(receipt)

    def receipt(self, principal, sender, event_id):
        binding = self.authorize(principal, sender)
        key = (canonical([binding['tenant'], sender]), 'EVENT#' + event_id)
        if key not in self.rows:
            raise Rejected(404)
        return copy.deepcopy(self.rows[key]['receipt'])
