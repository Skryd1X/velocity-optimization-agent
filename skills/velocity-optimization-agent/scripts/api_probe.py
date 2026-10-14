"""Scoped sequential API observations; no response bodies or credentials in reports."""

import argparse
import json
import time
import urllib.request
import urllib.parse
from common import context, metric, read, save


def origin(url):
    u = urllib.parse.urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
        raise ValueError("Expected HTTP URL without embedded credentials")
    return f"{u.scheme}://{u.hostname.lower()}:{u.port or (443 if u.scheme == 'https' else 80)}"


class ScopedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed):
        self.allowed = allowed

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if origin(newurl) not in self.allowed:
            raise ValueError("Redirect outside scope")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe(c):
    ctx = context(c["context"])
    url = c["url"]
    allowed = {origin(u) for u in c["allowed_origins"]}
    if origin(url) not in allowed:
        raise ValueError("URL outside scope")
    count = c.get("samples", 7)
    timeout = c.get("timeout_seconds", 10)
    limit = c.get("max_bytes", 1048576)
    interval = c.get("interval_seconds", 0.25)
    if (
        not 5 <= count <= 100
        or not 0 < timeout <= 60
        or not 1 <= limit <= 16777216
        or not 0.1 <= interval <= 10
    ):
        raise ValueError("Probe bounds exceeded")
    method = c.get("method", "GET")
    if method not in ("GET", "HEAD"):
        raise ValueError("Only GET/HEAD supported")
    opener = urllib.request.build_opener(ScopedRedirect(allowed))
    totals = []
    first = []
    records = []
    for i in range(count):
        start = time.perf_counter()
        row = {"sample": i + 1, "success": False}
        try:
            with opener.open(
                urllib.request.Request(url, method=method), timeout=timeout
            ) as response:
                ttfb = (time.perf_counter() - start) * 1000
                body = response.read(limit + 1)
                row.update(status=response.status, bytes=len(body))
                if len(body) > limit:
                    raise ValueError("Response exceeds byte bound")
                if response.status != c.get("expected_status", 200):
                    raise ValueError("Unexpected status")
                if c.get("expected_json") is not None:
                    value = json.loads(body)
                    if not isinstance(value, dict) or any(
                        value.get(k) != v for k, v in c["expected_json"].items()
                    ):
                        raise ValueError("Response correctness mismatch")
                total = (time.perf_counter() - start) * 1000
                totals.append(total)
                first.append(ttfb)
                row.update(success=True, total_ms=total, ttfb_ms=ttfb)
        except Exception as exc:
            row["error_type"] = type(exc).__name__
        records.append(row)
        if i < count - 1:
            time.sleep(interval)
    return dict(
        schema_version=1,
        context=ctx,
        revision=c.get("revision"),
        failures=sum(not r["success"] for r in records),
        metrics=[metric("total", totals), metric("ttfb", first)],
        observations=records,
        evidence="sequential API lab observation; not a load test or DB trace",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    save(a.output, probe(read(a.config)))
