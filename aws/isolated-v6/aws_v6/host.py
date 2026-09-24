"""Injectable host boundary. No built-in JWT/authorizer-claims authentication."""
from typing import Protocol
from isolated_v6.auth import Principal
from isolated_v6.service import Ingress


class AuthenticationAdapter(Protocol):
    def authenticate(self, event, context) -> Principal | None:
        """Trusted code verifies identity; untrusted claims alone are insufficient."""
        ...


class DenyAll:
    def authenticate(self, event, context):
        return None


class LambdaHost:
    def __init__(self, ingress: Ingress, authentication: AuthenticationAdapter):
        self.ingress, self.authentication = ingress, authentication

    def __call__(self, event, context):
        try:
            principal = self.authentication.authenticate(event, context)
        except Exception:
            return Ingress._response(503, {'code': 'authentication_unavailable'})
        return self.ingress.handle(event, trusted_principal=principal)


def handler(event, context):
    """Packaged fail-closed candidate entry point; deliberately not wired to SDK.

    Replace via reviewed composition only after auth/invocation/SDK gates pass.
    No environment flag or caller-controlled claims can enable this function.
    """
    return Ingress._response(503, {'code': 'deployment_candidate_not_activated'})
