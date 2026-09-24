"""Offline regression tests: all AWS SDK interactions are replaced before use."""
import base64
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "03_DFSS_Operations/Codebases/lambda_function.py"


def sign(envelope):
    unsigned = {k: v for k, v in envelope.items() if k != "integrity"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    envelope["integrity"] = {"algorithm": "SHA-256",
                             "digest": hashlib.sha256(encoded).hexdigest()}
    return envelope


def fixture():
    return sign({"protocol": "JEL-JKB/6.0", "sender": "offline-sender",
                 "receiver": "offline-receiver", "timestamp": "2026-09-24T00:00:00.123Z",
                 "context_mode": "HIGH_BANDWIDTH", "jel": "\U0001f431\U0001f4e6",
                 "payload_ref": "urn:offline:fixture", "instruction": "REHYDRATE_AND_VALIDATE",
                 "fallback": "STOP_AND_REPORT_DRIFT"})


class Condition:
    def __init__(self, fields):
        self.fields = fields
    def __and__(self, other):
        return Condition(self.fields + other.fields)


class Attr:
    def __init__(self, name):
        self.name = name
    def not_exists(self):
        return Condition([self.name])


class Conflict(Exception):
    pass


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("tested_lambda", SOURCE)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.records = {}
        self.table = Mock()
        self.table.meta.client.exceptions.ConditionalCheckFailedException = Conflict
        def put_item(*, Item, ConditionExpression):
            self.assertEqual(ConditionExpression.fields, ["userId", "timestamp"])
            key = (Item["userId"], Item["timestamp"])
            if key in self.records:
                raise Conflict()
            self.records[key] = copy.deepcopy(Item)
        self.table.put_item.side_effect = put_item
        self.resource = Mock()
        self.resource.Table.return_value = self.table
        sdk = types.ModuleType("boto3")
        sdk.resource = Mock(return_value=self.resource)
        conditions = types.ModuleType("boto3.dynamodb.conditions")
        conditions.Attr = Attr
        self.sdk = sdk
        self.modules = patch.dict(sys.modules, {"boto3": sdk,
            "boto3.dynamodb": types.ModuleType("boto3.dynamodb"),
            "boto3.dynamodb.conditions": conditions})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.env = patch.dict(os.environ, {"TABLE_NAME": "offline-only",
            "DRIFT_CHECK_ENABLED": "false", "JEL_PROTOCOL_VERSION": "2.6B"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def invoke(self, event):
        return self.module.lambda_handler(event, None)

    def reject(self, event, status):
        result = self.invoke(event)
        self.assertEqual(result["statusCode"], status, result)
        self.sdk.resource.assert_not_called()
        self.table.put_item.assert_not_called()

    def test_direct_envelope_uses_normalized_schema(self):
        body = fixture()
        self.assertEqual(self.invoke(body)["statusCode"], 200)
        item = next(iter(self.records.values()))
        self.assertEqual(set(item), {"userId", "timestamp", "schema_version", "envelope"})
        self.assertEqual(item["userId"], body["sender"])
        self.assertEqual(item["timestamp"], 1790208000123)
        self.assertIsInstance(item["timestamp"], int)
        self.assertEqual(item["envelope"], body)
        self.resource.Table.assert_called_once_with("offline-only")

    def test_gateway_json_and_header_case(self):
        self.assertEqual(self.invoke({"body": json.dumps(fixture()),
            "headers": {"X-JEL-Protocol-Version": "JEL-JKB/6.0"}})["statusCode"], 200)

    def test_base64_gateway(self):
        encoded = base64.b64encode(json.dumps(fixture()).encode()).decode()
        self.assertEqual(self.invoke({"body": encoded, "isBase64Encoded": True})["statusCode"], 200)

    def test_missing_integrity_has_no_aws_interaction(self):
        body = fixture(); del body["integrity"]
        self.reject(body, 422)

    def test_bad_integrity_has_no_aws_interaction(self):
        body = fixture(); body["integrity"]["digest"] = "0" * 64
        self.reject(body, 422)

    def test_integrity_types_and_algorithms(self):
        for integrity in (None, "", [], {}, {"algorithm": "MD5", "digest": "0"*64},
                          {"algorithm": "SHA-256", "digest": 123},
                          {"algorithm": "SHA-256", "digest": "A"*64},
                          {"algorithm": "SHA-256", "digest": "0"*63},
                          {"algorithm": "SHA-256", "digest": "0"*64, "extra": True}):
            with self.subTest(integrity_type=type(integrity).__name__):
                body = fixture(); body["integrity"] = integrity
                self.reject(body, 422)

    def test_every_signed_field_is_bound(self):
        for field in self.module.FIELDS - {"protocol", "timestamp"}:
            with self.subTest(field=field):
                body = fixture(); body[field] += "-tampered"
                self.reject(body, 422)
        body = fixture(); body["timestamp"] = "2026-09-24T00:00:00.124Z"
        self.reject(body, 422)

    def test_protocol_cannot_be_disabled_by_legacy_environment(self):
        body = fixture(); body["protocol"] = "2.6B"; sign(body)
        self.reject(body, 409)

    def test_conflicting_header(self):
        self.reject({"body": json.dumps(fixture()),
                     "headers": {"X-JEL-Protocol-Version": "2.6B"}}, 409)

    def test_missing_and_nonstring_fields(self):
        for field in self.module.FIELDS:
            for value in (None, "", "  ", {}, 4):
                with self.subTest(field=field, value_type=type(value).__name__):
                    body = fixture(); body[field] = value
                    self.reject(body, 400)
            body = fixture(); del body[field]
            self.reject(body, 400)

    def test_legacy_and_unknown_fields_rejected(self):
        for field in ("key", "value", "payload", "buffer_sha256", "unknown"):
            body = fixture(); body[field] = "injected"
            self.reject(body, 400)
        self.reject({"headers": {"x-jel-protocol-version": "2.6B"}, "body": {}}, 409)

    def test_invalid_timestamps(self):
        for stamp in ("yesterday", "2026-02-30T00:00:00Z", "2026-09-24T00:00:00",
                      "2026-09-24T00:00:00+01:00", "2026-09-24T00:00:00.0001Z",
                      "2026-09-24T00:00:60Z"):
            body = fixture(); body["timestamp"] = stamp; sign(body)
            self.reject(body, 400)

    def test_utc_equivalent_timestamp_collides_without_overwrite(self):
        self.invoke(fixture())
        body = fixture(); body["timestamp"] = "2026-09-24T00:00:00.123+00:00"; sign(body)
        self.assertEqual(self.invoke(body)["statusCode"], 409)
        self.assertEqual(len(self.records), 1)

    def test_duplicate_and_conflicting_record_do_not_overwrite(self):
        self.invoke(fixture())
        before = copy.deepcopy(self.records)
        self.assertEqual(self.invoke(fixture())["statusCode"], 409)
        body = fixture(); body["payload_ref"] = "urn:offline:changed"; sign(body)
        self.assertEqual(self.invoke(body)["statusCode"], 409)
        self.assertEqual(self.records, before)

    def test_malformed_json_and_nonobjects(self):
        for body in ("{", "[]", "null", "1", "NaN", "Infinity"):
            self.reject({"body": body}, 400)

    def test_duplicate_json_fields(self):
        body = json.dumps(fixture())
        self.reject({"body": body[:-1] + ', "sender": "different"}'}, 400)

    def test_transport_errors(self):
        for event in (None, [], {"body": "!", "isBase64Encoded": True},
                      {"body": "/w==", "isBase64Encoded": True},
                      {"body": {}, "isBase64Encoded": "true"},
                      {"body": fixture(), "headers": [] + [1]}):
            self.reject(event, 400)

    def test_size_limits(self):
        self.reject({"body": " " * 65537}, 413)
        body = fixture(); body["sender"] = "x" * 257; sign(body)
        self.reject(body, 413)

    def test_lone_surrogate_rejected(self):
        body = fixture(); body["jel"] = "\ud800"
        self.reject(body, 400)

    def test_serialization_order_and_whitespace_do_not_change_digest(self):
        body = fixture()
        body = dict(reversed(list(body.items())))
        self.assertEqual(self.invoke({"body": json.dumps(body, indent=4)})["statusCode"], 200)

    def test_published_digest_vector(self):
        body = fixture()
        expected = "527dc5732b4939e263cf060d4dd6276b1dc2d590b61bb2e4d86996d1c954eec0"
        self.assertEqual(body["integrity"]["digest"], expected)
        self.assertEqual(hashlib.sha256(self.module.canonical_bytes(body)).hexdigest(), expected)

    def test_duplicate_nested_integrity_field_rejected(self):
        body = json.dumps(fixture()).replace('"algorithm": "SHA-256"',
            '"algorithm": "MD5", "algorithm": "SHA-256"')
        self.reject({"body": body}, 400)

    def test_conflicting_duplicate_header_names_rejected(self):
        self.reject({"body": fixture(), "headers": {
            "x-jel-protocol-version": "JEL-JKB/6.0",
            "X-JEL-Protocol-Version": "2.6B"}}, 409)

    def test_invalid_empty_headers_rejected(self):
        self.reject({"body": fixture(), "headers": []}, 400)

    def test_no_client_on_import(self):
        self.sdk.resource.assert_not_called()
        self.assertIsNone(self.module._dynamodb)

    def test_table_name_required(self):
        with patch.dict(os.environ, {"TABLE_NAME": ""}), self.assertLogs(self.module.LOGGER):
            self.assertEqual(self.invoke(fixture())["statusCode"], 500)
        self.sdk.resource.assert_not_called()
        self.table.put_item.assert_not_called()

    def test_storage_error_is_not_success_and_does_not_leak(self):
        self.table.put_item.side_effect = RuntimeError("SYNTHETIC_PRIVATE_EXCEPTION")
        with self.assertLogs(self.module.LOGGER) as logs:
            result = self.invoke(fixture())
        self.assertEqual(result["statusCode"], 500)
        self.assertNotIn("SYNTHETIC_PRIVATE_EXCEPTION", str(result) + str(logs.output))
        self.assertNotIn("urn:offline", str(logs.output))

    def test_client_reused_after_success(self):
        self.invoke(fixture())
        body = fixture(); body["sender"] = "second"; sign(body)
        self.invoke(body)
        self.sdk.resource.assert_called_once_with("dynamodb")


if __name__ == "__main__":
    unittest.main()
