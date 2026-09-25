"""Consume Gateway-verified claims under a separately secured invoke boundary.

This module DOES NOT verify JWT signatures. A direct invoker can forge the entire
Gateway event. API/stage/alias checks are consistency checks, not origin proof.
"""
import re
from isolated_v6.auth import Principal


class GatewayClaims:
    def __init__(self, config, clock_ms):
        self.config, self.clock_ms = config, clock_ms

    def authenticate(self, event, context):
        try:
            c = self.config
            if type(event) is not dict or event.get('version') != '2.0': return None
            if getattr(context, 'invoked_function_arn', None) != c.alias_arn: return None
            rc = event['requestContext']
            if type(rc) is not dict or rc.get('apiId') != c.api_id or rc.get('stage') != 'sandbox': return None
            authorizer = rc['authorizer']
            if type(authorizer) is not dict or set(authorizer) != {'jwt'}: return None
            jwt = authorizer['jwt']
            if type(jwt) is not dict or set(jwt) != {'claims', 'scopes'}: return None
            claims, scopes = jwt['claims'], jwt['scopes']
            if type(claims) is not dict or len(claims) > 64: return None
            # Explicit single-audience, access-token profile. No azp/client_id or
            # missing-aud fallback and no client-provided identity fields.
            required = {'iss','aud','sub','client_id','token_use','scope','exp','iat','nbf'}
            if not required <= set(claims): return None
            if any(type(k) is not str or type(v) is not str or len(k) > 128 or len(v) > 4096 for k,v in claims.items()): return None
            if claims['iss'] != c.issuer or claims['aud'] != c.audience or claims['token_use'] != 'access': return None
            if claims['client_id'] not in c.clients: return None
            for name in ('sub','client_id'):
                value = claims[name]
                if not value or value != value.strip() or any(ord(ch) < 33 or ord(ch) == 127 for ch in value): return None
            for name in ('exp','iat','nbf'):
                if not re.fullmatch(r'[0-9]{1,12}', claims[name]): return None
            now = self.clock_ms() / 1000
            exp, issued, nbf = (int(claims[k]) for k in ('exp','iat','nbf'))
            if exp <= now or issued > now or nbf > now or issued >= exp or nbf >= exp: return None
            if type(scopes) is not list or not scopes or any(type(s) is not str for s in scopes): return None
            claim_scopes = claims['scope'].split(' ')
            if (len(scopes) != len(set(scopes)) or len(claim_scopes) != len(set(claim_scopes)) or
                set(scopes) != set(claim_scopes) or not set(scopes) <= {'jel-v6/read','jel-v6/write'}): return None
            return Principal(claims['iss'], claims['sub'], claims['client_id'], frozenset(scopes))
        except (KeyError, TypeError, ValueError, AttributeError, UnicodeError):
            return None
