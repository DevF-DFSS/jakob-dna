"""Bounded HTTP API v2 event adapter; transport context is not authentication."""
import base64
import binascii
import json
import re
from dataclasses import dataclass
from urllib.parse import quote, unquote
from .contract import event_id
from .errors import Rejected

MAX_BYTES = 65536
POST = 'POST /v6/events'
GET = 'GET /v6/senders/{sender}/events/{event_id}'


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise Rejected(400, 'duplicate_json_member')
        result[key] = value
    return result


def invalid_number(_):
    raise Rejected(400, 'invalid_json_number')


def json_body(body, encoded):
    if type(body) is not str or type(encoded) is not bool:
        raise Rejected(400, 'invalid_body')
    limit = 4 * ((MAX_BYTES + 2) // 3) if encoded else MAX_BYTES
    if len(body) > limit:
        raise Rejected(413, 'request_too_large')
    try:
        if encoded:
            raw = base64.b64decode(body, validate=True)
            if base64.b64encode(raw).decode('ascii') != body:
                raise ValueError()
        else:
            raw = body.encode('utf-8')
        if len(raw) > MAX_BYTES:
            raise Rejected(413, 'request_too_large')
        text = raw.decode('utf-8')
        # Bound nesting before JSON allocation, respecting escaped quotes.
        depth, quoted, escaped = 0, False, False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == '\\':
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in '[{':
                depth += 1
                if depth > 16:
                    raise Rejected(400, 'json_too_deep')
            elif char in ']}':
                depth -= 1
        return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid_number)
    except Rejected:
        raise
    except (ValueError, UnicodeError, binascii.Error, RecursionError):
        raise Rejected(400, 'invalid_json_body') from None


@dataclass(frozen=True)
class Request:
    method: str
    body: dict | None = None
    sender: str | None = None
    event_id: str | None = None


def parse(event, expected_api, expected_stage):
    if type(event) is not dict or event.get('version') != '2.0':
        raise Rejected(400, 'invalid_http_event')
    context = event.get('requestContext')
    if type(context) is not dict or type(context.get('http')) is not dict:
        raise Rejected(400, 'invalid_http_context')
    if context.get('apiId') != expected_api or context.get('stage') != expected_stage:
        raise Rejected(403, 'unexpected_ingress')
    if event.get('rawQueryString') != '' or event.get('queryStringParameters') not in (None, {}):
        raise Rejected(400, 'query_not_supported')
    headers = event.get('headers')
    if type(headers) is not dict or len(headers) > 64:
        raise Rejected(400, 'invalid_headers')
    normalized = {}
    total = 0
    for key, value in headers.items():
        if type(key) is not str or type(value) is not str or not re.fullmatch(r'[A-Za-z0-9!#$%&\'*+.^_`|~-]+', key):
            raise Rejected(400, 'invalid_headers')
        total += len(key) + len(value)
        if total > 16384 or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise Rejected(400, 'invalid_headers')
        lower = key.lower()
        if lower in normalized:
            raise Rejected(400, 'duplicate_header')
        normalized[lower] = value
    if 'content-encoding' in normalized or 'transfer-encoding' in normalized:
        raise Rejected(400, 'unsupported_encoding')
    version = normalized.get('x-jel-protocol-version')
    if version is not None and version != 'JEL-JKB/6.0':
        raise Rejected(409, 'protocol_header_conflict')
    method = context['http'].get('method')
    path = event.get('rawPath')
    if type(path) is not str or len(path) > 4096:
        raise Rejected(400, 'invalid_path')
    if method == 'POST' and event.get('routeKey') == POST and path == '/v6/events':
        if normalized.get('content-type', '').lower() not in ('application/json', 'application/json; charset=utf-8'):
            raise Rejected(415, 'json_required')
        body = json_body(event.get('body'), event.get('isBase64Encoded'))
        return Request(method, body=body)
    if method == 'GET' and event.get('routeKey') == GET:
        if event.get('body') not in (None, '') or event.get('isBase64Encoded') is not False:
            raise Rejected(400, 'unexpected_body')
        match = re.fullmatch(r'/v6/senders/([^/]+)/events/([^/]+)', path)
        if match:
            try:
                sender = unquote(match[1], encoding='utf-8', errors='strict')
                if quote(sender, safe='') != match[1] or not sender.strip() or len(sender.encode('utf-8')) > 256:
                    raise ValueError()
            except (ValueError, UnicodeError):
                raise Rejected(400, 'invalid_sender_path') from None
            uid = event_id(match[2])
            return Request(method, sender=sender, event_id=uid)
    raise Rejected(404, 'route_not_found')
