"""Sandbox composition root. No construction or credential discovery on import."""
import os
import time
from isolated_v6.service import Ingress
from .claims import GatewayClaims
from .config import settings, load_registry
from .dynamodb import DynamoEventStore
from .host import LambdaHost
from .telemetry import emit_outcome


def sdk_client(config):
    # Called only by an approved deployed host AFTER config/registry validation.
    # Offline tests inject a Stubber client with explicit synthetic credentials.
    import boto3
    from botocore.config import Config
    return boto3.session.Session(region_name=config.region).client('dynamodb',
        config=Config(region_name=config.region, connect_timeout=2, read_timeout=3,
                      retries={'mode':'standard','total_max_attempts':1},
                      ignore_configured_endpoint_urls=True, proxies={}))


def compose(env, *, client_factory=sdk_client, registry_path=None, clock_ms=None):
    config=settings(env)
    registry=load_registry(config, registry_path)
    clock_ms=clock_ms or (lambda:time.time_ns()//1_000_000)
    store=DynamoEventStore(client_factory(config),config.table)
    ingress=Ingress(registry,store,clock_ms,api_id=config.api_id,stage='sandbox')
    return LambdaHost(ingress,GatewayClaims(config,clock_ms))


_host=None


def handler(event, context):
    global _host
    try:
        if _host is None:
            _host=compose(os.environ)
        response = _host(event,context)
    except Exception:
        # Never emit configuration, SDK error text, claims or stack locals.
        response = Ingress._response(503,{'code':'startup_unavailable'})
    emit_outcome(response.get('statusCode'))
    return response
