"""Offline ingress service with separate trusted identity and storage boundaries."""
import json
import logging
from dataclasses import asdict
from .auth import authenticated
from .contract import canonical, digest, validate
from .errors import Rejected
from .http import parse
from .store import Event, EventStore, Receipt, StoreUnavailable

LOGGER = logging.getLogger(__name__)


class Ingress:
    def __init__(self, registry, store: EventStore, clock_ms, *, api_id, stage):
        if any(type(v) is not str or not v.strip() for v in (api_id, stage)):
            raise ValueError('explicit_ingress_required')
        self.registry, self.store, self.clock_ms = registry, store, clock_ms
        self.api_id, self.stage = api_id, stage

    def handle(self, event, *, trusted_principal=None):
        """Host supplies already verified identity; never derive it from event.

        This is not a Lambda handler. Host must prevent untrusted code from
        supplying trusted_principal; real authentication remains unimplemented.
        """
        try:
            # Reject unauthenticated requests even if they forge authorizer fields.
            authenticated(trusted_principal, 'jel-v6/read' if self._is_get(event) else 'jel-v6/write')
            request = parse(event, self.api_id, self.stage)
            if request.method == 'GET':
                binding = self.registry.authorize(trusted_principal, request.sender)
                pk = canonical([binding.tenant, request.sender]).decode('utf-8')
                row = self.store.get(pk, 'EVENT#' + request.event_id)
                if row is None:
                    raise Rejected(404, 'receipt_not_found')
                return self._response(200, asdict(row.receipt))
            now = self.clock_ms()
            wrapper = validate(request.body, now)
            envelope = wrapper['envelope']
            binding = self.registry.authorize(trusted_principal, envelope['sender'], envelope)
            pk = canonical([binding.tenant, envelope['sender']]).decode('utf-8')
            row = Event(pk, 'EVENT#' + wrapper['event_id'], wrapper['profile'], digest(wrapper),
                        canonical(wrapper), digest(list(trusted_principal.key)), binding.version,
                        Receipt(wrapper['event_id'], now))
            if self.store.insert_if_absent(row):
                return self._response(201, asdict(row.receipt))
            previous = self.store.get(row.pk, row.sk)
            if previous is None:
                raise StoreUnavailable()
            if previous.request_digest != row.request_digest:
                raise Rejected(409, 'event_conflict')
            return self._response(200, asdict(previous.receipt))
        except Rejected as exc:
            # Only our static code, never bodies, claims, headers or exception text.
            LOGGER.info('ingress_rejected status=%d code=%s', exc.status, exc.code)
            return self._response(exc.status, {'code': exc.code})
        except StoreUnavailable:
            LOGGER.warning('ingress_storage_unavailable')
            return self._response(503, {'code': 'storage_unavailable'})
        except Exception:
            LOGGER.error('ingress_internal_failure')
            return self._response(500, {'code': 'internal_failure'})

    @staticmethod
    def _is_get(event):
        if not isinstance(event, dict):
            return False
        context = event.get('requestContext')
        return isinstance(context, dict) and isinstance(context.get('http'), dict) and context['http'].get('method') == 'GET'

    @staticmethod
    def _response(status, body):
        return {'statusCode': status, 'headers': {'content-type': 'application/json', 'cache-control': 'no-store'},
                'body': json.dumps(body, separators=(',', ':'))}
