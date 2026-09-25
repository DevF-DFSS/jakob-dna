"""Run installed cfn-lint with socket/credential discovery blocked."""
import sys
import socket
import ssl
from unittest.mock import patch
import botocore.credentials
import cfnlint.runner


def blocked(*args, **kwargs):
    raise RuntimeError('offline_network_or_credentials_forbidden')


def main():
    with patch.object(socket,'socket',side_effect=blocked), patch.object(socket,'create_connection',side_effect=blocked), \
         patch.object(botocore.credentials.CredentialResolver,'load_credentials',side_effect=blocked):
        # Uses locally installed schemas; never request update-specs or registry.
        from cfnlint.runner import main as lint
        return lint()

if __name__=='__main__': raise SystemExit(main())
