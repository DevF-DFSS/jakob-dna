"""Authentication is an external trusted-code boundary, NOT event claims.

No JWT verification here. Only trusted host code may construct Principal and pass
it separately. Python objects are not a cryptographic boundary against host code.
"""
from dataclasses import dataclass
from threading import RLock
from .errors import Rejected


@dataclass(frozen=True)
class Principal:
    issuer: str
    subject: str
    client_id: str
    scopes: frozenset[str]

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() or len(v.encode('utf-8')) > 2048
               for v in (self.issuer, self.subject, self.client_id)):
            raise ValueError('invalid_principal')
        if type(self.scopes) is not frozenset or any(type(v) is not str for v in self.scopes):
            raise ValueError('invalid_scopes')

    @property
    def key(self):
        return self.issuer, self.subject, self.client_id


@dataclass(frozen=True)
class Binding:
    tenant: str
    senders: frozenset[str]
    receivers: frozenset[str]
    instructions: frozenset[str]
    version: str

    def __post_init__(self):
        if any(type(v) is not str or not v.strip() or len(v.encode('utf-8')) > 256
               for v in (self.tenant, self.version)):
            raise ValueError('invalid_binding')
        for values in (self.senders, self.receivers, self.instructions):
            if type(values) is not frozenset or not values or any(
                type(v) is not str or not v.strip() or len(v.encode('utf-8')) > 4096 for v in values
            ):
                raise ValueError('invalid_binding')


def authenticated(principal, scope):
    if type(principal) is not Principal:
        raise Rejected(401, 'authentication_required')
    if scope not in principal.scopes:
        raise Rejected(403, 'scope_denied')


class Registry:
    """Server-owned policy snapshot; revocation applies to subsequent checks.

    An operation authorized before concurrent revocation may finish. No claim of
    cancellation of in-flight requests or distributed revocation is made.
    """
    def __init__(self, bindings):
        self._lock = RLock()
        self._bindings = dict(bindings)
        for key, binding in self._bindings.items():
            if (type(key) is not tuple or len(key) != 3 or
                    any(type(v) is not str or not v.strip() for v in key) or type(binding) is not Binding):
                raise ValueError('invalid_registry')

    def revoke(self, key):
        with self._lock:
            self._bindings.pop(key, None)

    def authorize(self, principal, sender, envelope=None):
        with self._lock:
            binding = self._bindings.get(principal.key)
        if binding is None or sender not in binding.senders:
            raise Rejected(403, 'binding_denied')
        if envelope is not None and (envelope['receiver'] not in binding.receivers or
                                      envelope['instruction'] not in binding.instructions):
            raise Rejected(403, 'binding_denied')
        return binding
