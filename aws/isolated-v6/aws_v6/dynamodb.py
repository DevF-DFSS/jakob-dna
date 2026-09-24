"""Low-level DynamoDB client adapter, injected by trusted host code.

Explicit AttributeValue marshalling keeps offline tests independent of boto3.
Use a low-level client, never a resource client with automatic marshalling.
"""
import json
import re
from isolated_v6.contract import canonical, digest, PROFILE, event_id, utc_millis
from isolated_v6.envelope import validate_envelope
from isolated_v6.store import Event, Receipt, StoreUnavailable

STRINGS = ('PK', 'SK', 'profile', 'request_digest', 'wrapper_json', 'principal_ref', 'binding_version')


def marshal(event):
    if type(event) is not Event or type(event.wrapper_bytes) is not bytes or type(event.receipt) is not Receipt:
        raise ValueError('invalid_record')
    if type(event.receipt.accepted_at_ms) is not int or event.receipt.status != 'accepted':
        raise ValueError('invalid_receipt')
    values = (event.pk, event.sk, event.profile, event.request_digest,
              event.wrapper_bytes.decode('utf-8'), event.principal_ref, event.binding_version)
    if any(type(v) is not str or not v for v in values):
        raise ValueError('invalid_record')
    item = {key: {'S': value} for key, value in zip(STRINGS, values)}
    item['receipt'] = {'M': {'event_id': {'S': event.receipt.event_id},
                            'accepted_at_ms': {'N': str(event.receipt.accepted_at_ms)},
                            'status': {'S': event.receipt.status}}}
    # Reuse strict decoder for validation without changing signed text.
    if unmarshal(item) != event:
        raise ValueError('noncanonical_record')
    return item


def scalar(value, kind):
    if type(value) is not dict or set(value) != {kind} or type(value[kind]) is not str:
        raise ValueError('invalid_attribute')
    return value[kind]


def unmarshal(item):
    if type(item) is not dict or set(item) != set(STRINGS) | {'receipt'}:
        raise ValueError('invalid_record_fields')
    s = {key: scalar(item[key], 'S') for key in STRINGS}
    if any(not v for v in s.values()):
        raise ValueError('empty_attribute')
    r = item['receipt']
    if type(r) is not dict or set(r) != {'M'} or type(r['M']) is not dict or set(r['M']) != {'event_id', 'accepted_at_ms', 'status'}:
        raise ValueError('invalid_receipt')
    r = r['M']
    number = scalar(r['accepted_at_ms'], 'N')
    if not re.fullmatch(r'-?(0|[1-9][0-9]*)', number) or len(number) > 20:
        raise ValueError('invalid_number')
    receipt = Receipt(event_id(scalar(r['event_id'], 'S')), int(number), scalar(r['status'], 'S'))
    if receipt.status != 'accepted' or s['SK'] != 'EVENT#' + receipt.event_id:
        raise ValueError('receipt_identity_mismatch')
    raw = s['wrapper_json'].encode('utf-8')
    if len(raw) > 65536:
        raise ValueError('oversize_record')
    wrapper = json.loads(raw)
    if type(wrapper) is not dict or set(wrapper) != {'profile', 'event_id', 'issued_at', 'envelope'}:
        raise ValueError('invalid_wrapper')
    if canonical(wrapper) != raw or wrapper['profile'] != PROFILE or s['profile'] != PROFILE:
        raise ValueError('invalid_canonical_record')
    validate_envelope(wrapper['envelope'])
    utc_millis(wrapper['issued_at'])  # Never apply freshness to historical reads.
    if wrapper['event_id'] != receipt.event_id or digest(wrapper) != s['request_digest']:
        raise ValueError('record_digest_mismatch')
    partition = json.loads(s['PK'])
    if (type(partition) is not list or len(partition) != 2 or
            any(type(v) is not str or not v.strip() for v in partition) or
            len(partition[0].encode('utf-8')) > 256 or
            partition[1] != wrapper['envelope']['sender'] or
            canonical(partition).decode('utf-8') != s['PK']):
        raise ValueError('partition_mismatch')
    if not re.fullmatch('[0-9a-f]{64}', s['principal_ref']):
        raise ValueError('invalid_principal_ref')
    return Event(s['PK'], s['SK'], s['profile'], s['request_digest'], raw,
                 s['principal_ref'], s['binding_version'], receipt)


class DynamoEventStore:
    def __init__(self, client, table_name):
        if type(table_name) is not str or not re.fullmatch('[A-Za-z0-9_.-]{3,255}', table_name):
            raise ValueError('explicit_table_required')
        self._client, self._table = client, table_name

    def insert_if_absent(self, event):
        try:
            result = self._client.put_item(
                TableName=self._table, Item=marshal(event),
                ConditionExpression='attribute_not_exists(#pk) AND attribute_not_exists(#sk)',
                ExpressionAttributeNames={'#pk': 'PK', '#sk': 'SK'})
            if result.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                raise StoreUnavailable()
            return True
        except self._client.exceptions.ConditionalCheckFailedException:
            return False
        except Exception:
            # Includes timeouts after commit, permission/validation failures and
            # malformed responses. Never echo SDK exception/credential details.
            raise StoreUnavailable() from None

    def get(self, pk, sk):
        try:
            result = self._client.get_item(TableName=self._table,
                Key={'PK': {'S': pk}, 'SK': {'S': sk}}, ConsistentRead=True)
            if result.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
                raise StoreUnavailable()
            if 'Item' not in result:
                return None
            row = unmarshal(result['Item'])
            if (row.pk, row.sk) != (pk, sk):
                raise ValueError('wrong_record')
            return row
        except Exception:
            raise StoreUnavailable() from None
