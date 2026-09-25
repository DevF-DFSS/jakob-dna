"""Finite outcome-only log records; never accept request/configuration objects."""
import json


def emit_outcome(status):
    if type(status) is not int:
        outcome = 'unavailable'
    elif 200 <= status < 300:
        outcome = 'accepted'
    elif 400 <= status < 500:
        outcome = 'rejected'
    else:
        outcome = 'unavailable'
    try:
        print(json.dumps({'kind': 'v6_outcome', 'outcome': outcome}, sort_keys=True))
    except Exception:
        # Observability failure cannot alter an accepted immutable receipt.
        pass
