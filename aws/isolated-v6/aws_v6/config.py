"""Startup policy validation; reads only named non-secret settings."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from isolated_v6.auth import Binding, Registry


@dataclass(frozen=True)
class Settings:
    table: str
    region: str
    api_id: str
    issuer: str
    audience: str
    clients: frozenset[str]
    alias_arn: str
    bindings_version: str
    bindings_sha256: str


def pairs(items):
    result={}
    for k,v in items:
        if k in result: raise ValueError('duplicate_config_member')
        result[k]=v
    return result


def settings(env):
    keys=('V6_TABLE_NAME','EXPECTED_REGION','AWS_REGION','EXPECTED_API_ID','EXPECTED_STAGE',
          'EXPECTED_ISSUER','EXPECTED_AUDIENCE','EXPECTED_CLIENT_IDS','EXPECTED_ALIAS_ARN','BINDINGS_VERSION','BINDINGS_SHA256')
    v={k:env.get(k) for k in keys}
    if any(type(x) is not str or not x or x != x.strip() or len(x)>4096 for x in v.values()):
        raise ValueError('missing_or_invalid_config')
    if not re.fullmatch(r'jel-v6-[A-Za-z0-9_.-]{1,240}',v['V6_TABLE_NAME']): raise ValueError('isolated_table_required')
    if v['EXPECTED_STAGE']!='sandbox' or v['AWS_REGION']!=v['EXPECTED_REGION']: raise ValueError('invalid_scope')
    if not re.fullmatch(r'[a-z]{2}(?:-[a-z]+)+-[0-9]',v['EXPECTED_REGION']): raise ValueError('invalid_region')
    if not re.fullmatch(r'[a-z0-9]{6,32}',v['EXPECTED_API_ID']): raise ValueError('invalid_api')
    url=urlsplit(v['EXPECTED_ISSUER'])
    if (url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment or url.port not in (None,443)):
        raise ValueError('invalid_issuer')
    if any(ord(ch)<33 or ord(ch)==127 for ch in v['EXPECTED_AUDIENCE']): raise ValueError('invalid_audience')
    clients=json.loads(v['EXPECTED_CLIENT_IDS'])
    if (type(clients) is not list or not clients or len(clients)>64 or
        any(type(x) is not str or not x or x!=x.strip() or len(x)>256 or any(ord(ch)<33 or ord(ch)==127 for ch in x) for x in clients) or len(set(clients))!=len(clients)):
        raise ValueError('invalid_clients')
    alias=v['EXPECTED_ALIAS_ARN']
    if not re.fullmatch(r'arn:aws(?:-us-gov|-cn)?:lambda:'+re.escape(v['EXPECTED_REGION'])+r':[0-9]{12}:function:[A-Za-z0-9_-]+-v6:sandbox',alias):
        raise ValueError('invalid_alias')
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',v['BINDINGS_VERSION']) or not re.fullmatch('[0-9a-f]{64}',v['BINDINGS_SHA256']):
        raise ValueError('invalid_binding_version')
    return Settings(v['V6_TABLE_NAME'],v['EXPECTED_REGION'],v['EXPECTED_API_ID'],v['EXPECTED_ISSUER'],
                    v['EXPECTED_AUDIENCE'],frozenset(clients),alias,v['BINDINGS_VERSION'],v['BINDINGS_SHA256'])


def load_registry(config, path=None):
    # Fixed package path in production; path injection is only for offline tests.
    path=Path(path) if path is not None else Path(__file__).with_name('bindings.json')
    with path.open('rb') as stream: raw=stream.read(65537)
    if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=config.bindings_sha256: raise ValueError('binding_digest_mismatch')
    document=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
    if type(document) is not dict or set(document)!={'version','bindings'} or document['version']!=config.bindings_version:
        raise ValueError('binding_version_mismatch')
    entries=document['bindings']
    if type(entries) is not list or not entries or len(entries)>128: raise ValueError('empty_or_invalid_bindings')
    bindings={}
    for entry in entries:
        if type(entry) is not dict or set(entry)!={'issuer','subject','client_id','tenant','senders','receivers','instructions'}:
            raise ValueError('invalid_binding_fields')
        key=tuple(entry[k] for k in ('issuer','subject','client_id'))
        if any(type(x) is not str or not x.strip() or x!=x.strip() for x in key): raise ValueError('invalid_identity')
        if key[0]!=config.issuer or key[2] not in config.clients or key in bindings: raise ValueError('invalid_identity_binding')
        for field in ('senders','receivers','instructions'):
            values=entry[field]
            if type(values) is not list or not values or any(type(x) is not str for x in values) or len(values)!=len(set(values)):
                raise ValueError('invalid_authorization_set')
        if any(len(x.encode('utf-8'))>256 for field in ('senders','receivers') for x in entry[field]):
            raise ValueError('binding_identifier_too_large')
        bindings[key]=Binding(entry['tenant'],frozenset(entry['senders']),frozenset(entry['receivers']),
                              frozenset(entry['instructions']),config.bindings_version)
    return Registry(bindings)
