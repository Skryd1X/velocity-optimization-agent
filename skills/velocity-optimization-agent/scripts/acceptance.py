"""Validate declared closure structure; this cannot authenticate external evidence."""

import argparse
import json
from common import read

REQUIRED = {
    "discovery",
    "performance",
    "data",
    "functional",
    "responsive",
    "accessibility",
    "security",
}


def check(ledger):
    errors = []
    checks = ledger.get("checks", {})
    if set(checks) < REQUIRED or not REQUIRED <= set(checks):
        errors.append("Missing required coverage categories")
    for name in REQUIRED:
        item = checks.get(name, {})
        if (
            item.get("status") == "not-applicable"
            and item.get("reason")
            and name in {"data", "responsive"}
        ):
            continue
        if item.get("status") != "passed" or not item.get("evidence"):
            errors.append("Unverified coverage: " + name)
    if ledger.get("integrated_passes", 0) < 2:
        errors.append("Two integrated verification passes required")
    performance = ledger.get("performance", {})
    if performance.get("status") not in {
        "comparison-passed",
        "baseline-within-budget",
    } or not performance.get("evidence"):
        errors.append("Performance acceptance evidence required")
    for item in ledger.get("findings", []):
        status = item.get("status")
        severity = item.get("severity")
        if severity not in {"blocking", "high", "medium", "low"}:
            errors.append("Unknown finding severity")
        if status == "verified" and not item.get("validation"):
            errors.append("Verified finding lacks validation")
        if status == "false-positive" and not (
            item.get("reason") and item.get("validation")
        ):
            errors.append("False positive lacks evidence")
        if status not in {"verified", "false-positive", "residual"}:
            errors.append("Finding remains unverified")
        if status == "residual" and (
            severity in {"blocking", "high"} or not item.get("reason")
        ):
            errors.append("Unacceptable residual finding")
    for item in ledger.get("companions", []):
        if item.get("required") and (
            item.get("status") != "ready" or not item.get("integrated_validation")
        ):
            errors.append("Required companion not integrated and verified")
    return {
        "passed": not errors,
        "errors": errors,
        "evidence_boundary": "Declared structure only; inspect and reproduce linked evidence before claiming product acceptance",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("ledger")
    a = p.parse_args()
    result = check(read(a.ledger))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
