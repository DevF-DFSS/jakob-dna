"""Offline test runner; deny socket use and record machine-readable results."""
import argparse
import json
from pathlib import Path
import socket
import ssl  # Load socket subclasses before installing the offline guard.
import sys
import unittest
import boto3
import botocore.credentials
import botocore.httpsession


def run(core, candidate):
    sys.path[:0] = [str(core), str(candidate), str(candidate / 'tools')]
    def blocked(*args, **kwargs):
        raise AssertionError('network_forbidden_in_offline_checks')
    socket.socket = blocked
    socket.create_connection = blocked
    botocore.credentials.CredentialResolver.load_credentials = blocked
    botocore.httpsession.URLLib3Session.send = blocked
    suite = unittest.TestSuite()
    for directory in [core / 'tests', candidate / 'tests']:
        suite.addTests(unittest.TestLoader().discover(str(directory)))
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    return {'tests_run':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
            'skipped':len(result.skipped), 'passed':result.wasSuccessful(), 'network':'socket and SDK HTTP send denied; credential resolver denied'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--core',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.core.resolve(),Path(__file__).resolve().parents[1])
    print(json.dumps(result,sort_keys=True))
    return 0 if result['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
