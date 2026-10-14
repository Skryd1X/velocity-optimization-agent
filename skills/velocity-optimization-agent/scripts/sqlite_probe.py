"""Read-only bounded SQLite query observations with result hashes."""

import argparse
import sqlite3
import time
import hashlib
import json
from pathlib import Path
from common import read, save, metric, context


def probe(database, query, params, ctx, samples=7, max_rows=10000, timeout=2):
    context(ctx)
    if not 5 <= samples <= 100 or not 1 <= max_rows <= 100000 or not 0 < timeout <= 30:
        raise ValueError("Query bounds exceeded")
    allowed = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
        sqlite3.SQLITE_RECURSIVE,
    }
    con = sqlite3.connect(
        Path(database).resolve(strict=True).as_uri() + "?mode=ro", uri=True
    )
    con.set_authorizer(
        lambda action, *args: sqlite3.SQLITE_OK
        if action in allowed
        else sqlite3.SQLITE_DENY
    )
    times = []
    observations = []
    plan = []
    try:
        plan = [list(row) for row in con.execute("EXPLAIN QUERY PLAN " + query, params)]
        for i in range(samples):
            start = time.perf_counter()
            con.set_progress_handler(
                lambda: int(time.perf_counter() - start > timeout), 1000
            )
            try:
                rows = con.execute(query, params).fetchmany(max_rows + 1)
                if len(rows) > max_rows:
                    raise ValueError("Row limit exceeded")
                elapsed = (time.perf_counter() - start) * 1000
                times.append(elapsed)
                digest = hashlib.sha256(
                    json.dumps(
                        rows,
                        default=lambda v: {"bytes": v.hex()},
                        ensure_ascii=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                observations.append(
                    dict(success=True, rows=len(rows), result_sha256=digest, ms=elapsed)
                )
            except (sqlite3.Error, ValueError) as exc:
                observations.append(dict(success=False, error_type=type(exc).__name__))
    finally:
        con.close()
    return dict(
        schema_version=1,
        context=ctx,
        failures=sum(not r["success"] for r in observations),
        metrics=[metric("query", times)],
        observations=observations,
        plan=plan,
        query_sha256=hashlib.sha256(query.encode()).hexdigest(),
        cache_note="Repeated reads; first observation may warm cache. No production inference.",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--database", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--params")
    p.add_argument("--context", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    save(
        a.output,
        probe(
            a.database,
            Path(a.query).read_text(encoding="utf-8"),
            read(a.params) if a.params else [],
            read(a.context),
        ),
    )
