"""PR #4 string-only canonicalization profile; no AWS dependencies."""
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from .errors import Rejected

PROTOCOL = "JEL-JKB/6.0"
FIELDS = frozenset(("protocol", "sender", "receiver", "timestamp", "context_mode",
                    "jel", "payload_ref", "instruction", "fallback"))
MAX_BYTES = 65536

def canonical_bytes(envelope: dict) -> bytes:
    """Profile: sorted ASCII field names, compact JSON, literal UTF-8 strings."""
    unsigned = {key: value for key, value in envelope.items() if key != "integrity"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def validate_envelope(envelope: dict) -> tuple[dict, int]:
    if not isinstance(envelope, dict):
        raise Rejected(400, "invalid_envelope")
    if "integrity" not in envelope:
        raise Rejected(422, "integrity_required")
    if set(envelope) != FIELDS | {"integrity"}:
        raise Rejected(400, "invalid_envelope_fields")
    for field in FIELDS:
        value = envelope[field]
        if not isinstance(value, str) or not value.strip():
            raise Rejected(400, "invalid_field")
        try:
            length = len(value.encode("utf-8"))
        except UnicodeError:
            raise Rejected(400, "invalid_unicode") from None
        if length > (256 if field in ("sender", "receiver") else 4096):
            raise Rejected(413, "field_too_large")
    if envelope["protocol"] != PROTOCOL:
        raise Rejected(409, "unsupported_protocol")
    stamp = envelope["timestamp"]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|\+00:00)", stamp):
        raise Rejected(400, "invalid_timestamp")
    try:
        instant = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        raise Rejected(400, "invalid_timestamp") from None
    delta = instant - datetime(1970, 1, 1, tzinfo=timezone.utc)
    millis = (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
    integrity = envelope["integrity"]
    if (not isinstance(integrity, dict) or set(integrity) != {"algorithm", "digest"}
            or integrity.get("algorithm") != "SHA-256"
            or not isinstance(integrity.get("digest"), str)
            or not re.fullmatch("[0-9a-f]{64}", integrity["digest"])):
        raise Rejected(422, "invalid_integrity")
    encoded = canonical_bytes(envelope)
    if len(encoded) > MAX_BYTES:
        raise Rejected(413, "envelope_too_large")
    if not hmac.compare_digest(hashlib.sha256(encoded).hexdigest(), integrity["digest"]):
        raise Rejected(422, "integrity_mismatch")
    # Copy only validated strings and integrity fields; retain exact signed text.
    snapshot = {field: envelope[field] for field in FIELDS}
    snapshot["integrity"] = dict(integrity)
    return snapshot, millis

