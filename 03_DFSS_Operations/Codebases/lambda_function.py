"""JaKoB Apex Lambda scaffold for Python 3.11.

Configure TABLE_NAME and BUFFER_SHARED_SECRET in Lambda environment/Secrets Manager.
Do not put production secrets in this source file.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO"))
TABLE_NAME = os.environ.get("TABLE_NAME", "jakob-memory-store")
DRIFT_CHECK_ENABLED = os.getenv("DRIFT_CHECK_ENABLED", "true").lower() == "true"
JEL_PROTOCOL_VERSION = os.getenv("JEL_PROTOCOL_VERSION", "2.6B")
SECURITY_AUTH_MODE = os.getenv("SECURITY_AUTH_MODE", "C5_CLEARANCE")
DYNAMODB = boto3.resource("dynamodb")


def drift_checker(event: dict[str, Any]) -> dict[str, Any]:
    """Inspect protocol/version headers; returns a non-authorizing diagnostic."""
    headers = event.get("headers") or {}
    observed = headers.get("x-jel-protocol-version") or event.get("jel_protocol_version")
    status = "PASS" if not DRIFT_CHECK_ENABLED or observed == JEL_PROTOCOL_VERSION else "DRIFT"
    return {"enabled": DRIFT_CHECK_ENABLED, "expected": JEL_PROTOCOL_VERSION, "observed": observed, "status": status}


def verify_from_buffer(payload: str, supplied_digest: str | None) -> bool:
    """Compare a SHA-256 digest in constant time; integrity only, not authentication."""
    if not supplied_digest:
        return False
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, supplied_digest)


async def process_event(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body or "{}")

    payload = json.dumps(body.get("payload", {}), sort_keys=True, separators=(",", ":"))
    integrity_ok = verify_from_buffer(payload, body.get("buffer_sha256"))
    drift = drift_checker(event)

    item = {
        "key": body.get("key", "SYSTEM_STATE_V6"),
        "value": body.get("value", "ZERO_DELTA_LOCKED"),
        "protocol_version": JEL_PROTOCOL_VERSION,
        "security_auth_mode": SECURITY_AUTH_MODE,
        "integrity_ok": integrity_ok,
        "drift_status": drift["status"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if drift["status"] == "DRIFT":
        return {"statusCode": 409, "body": json.dumps({"message": "drift detected", "drift": drift})}

    DYNAMODB.Table(TABLE_NAME).put_item(Item=item)
    return {"statusCode": 200, "body": json.dumps({"stored": item["key"], "integrity_ok": integrity_ok, "drift": drift})}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda-compatible synchronous entry point wrapping async work."""
    try:
        return asyncio.run(process_event(event))
    except Exception as exc:
        LOGGER.exception("JaKoB Apex request failed")
        return {"statusCode": 500, "body": json.dumps({"message": "internal error", "detail": type(exc).__name__})}
