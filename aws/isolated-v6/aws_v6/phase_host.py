"""Packaged, bounded ingress capability. Never authenticates a human approval.

CLOSED ships by default and returns before SDK/configuration construction. An
active capability requires a different reviewed artifact, not an environment
switch. Code/configuration administrators remain outside this mechanism.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import time
from isolated_v6.service import Ingress
from .activation import compose
from .telemetry import emit_outcome

CONFIG_KEYS = ('V6_TABLE_NAME', 'EXPECTED_REGION', 'AWS_REGION', 'EXPECTED_API_ID',
               'EXPECTED_STAGE', 'EXPECTED_ISSUER', 'EXPECTED_AUDIENCE',
               'EXPECTED_CLIENT_IDS', 'EXPECTED_ALIAS_ARN', 'BINDINGS_VERSION',
               'BINDINGS_SHA256')


def config_digest(env):
    values = {k: env[k] for k in CONFIG_KEYS}
    if any(type(v) is not str or not v for v in values.values()):
        raise ValueError('configuration_required')
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def members(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate_member')
        result[key] = value
    return result


def capability(raw, expected_hash, env):
    if len(raw) > 16384 or not re.fullmatch('[0-9a-f]{64}', expected_hash or ''):
        raise ValueError('capability_invalid')
    if hashlib.sha256(raw).hexdigest() != expected_hash: raise ValueError('capability_mismatch')
    c = json.loads(raw, object_pairs_hook=members)
    if type(c) is not dict or set(c) != {'schema_version','mode','config_sha256','starts_at','expires_at','principals'}:
        raise ValueError('capability_shape')
    if c['schema_version'] != 'jel-v6-capability/1': raise ValueError('capability_version')
    if c['mode'] == 'CLOSED':
        if any(c[k] is not None for k in ['config_sha256','starts_at','expires_at']) or c['principals'] != []:
            raise ValueError('closed_capability_invalid')
        return c
    if c['mode'] not in ('TEST','SANDBOX'): raise ValueError('capability_mode')
    if c['config_sha256'] != config_digest(env): raise ValueError('configuration_mismatch')
    start, end = c['starts_at'], c['expires_at']
    limit = 3600 if c['mode'] == 'TEST' else 86400
    if type(start) is not int or type(end) is not int or not 0 < end-start <= limit:
        raise ValueError('capability_window')
    ps = c['principals']
    if type(ps) is not list or not 1 <= len(ps) <= 32: raise ValueError('principals_required')
    keys = []
    for p in ps:
        if type(p) is not list or len(p) != 3 or any(type(v) is not str or not 1 <= len(v) <= 2048 for v in p):
            raise ValueError('principal_invalid')
        keys.append(tuple(p))
    if len(set(keys)) != len(keys): raise ValueError('duplicate_principal')
    return c


class PhaseHost:
    def __init__(self, c, host, clock_ms):
        self.capability, self.host, self.clock_ms = c, host, clock_ms

    def __call__(self, event, context):
        c = self.capability
        if c['mode'] == 'CLOSED' or not c['starts_at'] <= self.clock_ms()//1000 < c['expires_at']:
            return Ingress._response(503, {'code':'phase_closed'})
        # This is the existing Gateway-bound adapter, not JWT cryptography.
        principal = self.host.authentication.authenticate(event, context)
        if principal is None or list(principal.key) not in c['principals']:
            return Ingress._response(403, {'code':'phase_principal_denied'})
        return self.host.ingress.handle(event, trusted_principal=principal)


def compose_phase(env, *, capability_path=None, factory=compose, clock_ms=None):
    path = capability_path or Path(__file__).with_name('capability.json')
    raw = path.read_bytes()
    c = capability(raw, env.get('CAPABILITY_SHA256'), env)
    clock_ms = clock_ms or (lambda: time.time_ns()//1_000_000)
    if c['mode'] == 'CLOSED': return PhaseHost(c, None, clock_ms)
    if not c['starts_at'] <= clock_ms()//1000 < c['expires_at']: raise ValueError('inactive_capability')
    return PhaseHost(c, factory(env, clock_ms=clock_ms), clock_ms)


_host = None


def handler(event, context):
    global _host
    try:
        if _host is None: _host = compose_phase(os.environ)
        response = _host(event, context)
    except Exception:
        response = Ingress._response(503, {'code':'phase_unavailable'})
    emit_outcome(response.get('statusCode'))
    return response
