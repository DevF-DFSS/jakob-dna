"""Offline compatibility checks on sanitized audit evidence. No AWS/network access."""
import json
from pathlib import Path

COMPATIBLE = "✅ COMPATIBLE"
MIGRATE = "⚠️ MIGRATION REQUIRED"
UNRESOLVED = "🐈📦 UNRESOLVED"
BLOCKED = "🚫 BLOCKED"

def table_status(table):
    keys = {k["KeyType"]: k["AttributeName"] for k in table.get("KeySchema", [])}
    types = {a["AttributeName"]: a["AttributeType"] for a in table.get("AttributeDefinitions", [])}
    if not keys or not types:
        return UNRESOLVED
    return COMPATIBLE if keys == {"HASH": "userId", "RANGE": "timestamp"} and types.get("userId") == "S" and types.get("timestamp") == "N" else MIGRATE

def function_status(function):
    runtime = function.get("Runtime")
    if runtime is None:
        return UNRESOLVED
    # Match source syntax/runtime family only; this is not lifecycle/service proof.
    if runtime not in ("python3.10", "python3.11", "python3.12", "python3.13", "python3.14"):
        return MIGRATE
    if function.get("Handler") != "lambda_function.lambda_handler":
        return MIGRATE
    if function.get("table_name_present") is not True:
        return MIGRATE if function.get("table_name_present") is False else UNRESOLVED
    return COMPATIBLE

def route_status(route):
    auth = route.get("AuthorizationType")
    if auth is None:
        return UNRESOLVED
    # Non-NONE still needs identity binding, issuer/audience and policy review.
    return BLOCKED if auth == "NONE" else UNRESOLVED

def summarize(evidence):
    rows = []
    for region in evidence.get("details", {}).get("regions", []):
        for table in region.get("tables", []):
            rows.append({"kind": "table", "region": region["region"],
                         "name": table.get("TableName"), "status": table_status(table)})
        for function in region.get("functions", []):
            rows.append({"kind": "function_configuration", "region": region["region"],
                         "name": function.get("FunctionName"), "status": function_status(function)})
        for api in region.get("apis", []):
            for route in api.get("routes", []):
                rows.append({"kind": "route_ingress", "region": region["region"],
                             "name": api["id"] + " " + route["RouteKey"],
                             "status": route_status(route)})
    return rows

if __name__ == "__main__":
    print(json.dumps(summarize(json.loads(Path(__file__).with_name("evidence.json").read_text())),
                     ensure_ascii=False, indent=2))
