"""Exact transport contract, identity, and freshness validation."""
import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import UUID
from .envelope import validate_envelope
from .errors import Rejected

PROFILE = 'JEL-JKB/6.0-isolated/1'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def event_id(value):
    try:
        uid = UUID(value)
        if uid.version != 4 or str(uid) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise Rejected(400, 'invalid_event_id') from None
    return value


def utc_millis(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,3})?(?:Z|\+00:00)', value
    ):
        raise Rejected(400, 'invalid_issued_at')
    try:
        delta = datetime.fromisoformat(value.replace('Z', '+00:00')) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    except ValueError:
        raise Rejected(400, 'invalid_issued_at') from None
    return (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000


def validate(wrapper, now_ms):
    if not isinstance(wrapper, dict) or set(wrapper) != {'profile', 'event_id', 'issued_at', 'envelope'}:
        raise Rejected(400, 'invalid_wrapper')
    if wrapper['profile'] != PROFILE:
        raise Rejected(409, 'unsupported_profile')
    event_id(wrapper['event_id'])
    issued = utc_millis(wrapper['issued_at'])
    envelope, _ = validate_envelope(wrapper['envelope'])
    if type(now_ms) is not int:
        raise RuntimeError('invalid_clock')
    if not -30000 <= now_ms - issued <= 300000:
        raise Rejected(422, 'outside_freshness_window')
    return dict(wrapper, envelope=envelope)
