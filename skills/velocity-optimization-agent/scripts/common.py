import json
import math
from pathlib import Path

CONTEXT_KEYS = (
    "scenario",
    "environment",
    "build_mode",
    "device",
    "dataset",
    "workload",
    "cache_state",
)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def context(value):
    if any(
        not isinstance(value.get(k), str) or not value[k].strip() for k in CONTEXT_KEYS
    ):
        raise ValueError("Complete measurement context required")
    return {k: value[k] for k in CONTEXT_KEYS}


def metric(name, samples, unit="ms", direction="lower", **extra):
    return dict(name=name, samples=samples, unit=unit, direction=direction, **extra)


def percentile(samples):
    return sorted(samples)[math.ceil(0.95 * len(samples)) - 1]
