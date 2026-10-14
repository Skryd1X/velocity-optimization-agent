"""Real helper runs on synthetic local API and indexed SQLite fixtures."""

import json
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/velocity-optimization-agent/scripts"))
from common import save
import api_probe
import sqlite_probe
import compare


def run(output):
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    ctx = dict(
        scenario="lookup",
        environment="local-fixture",
        build_mode="release",
        device="local-host",
        dataset="synthetic-50000-v1",
        workload="sequential-read",
        cache_state="repeated-read",
    )
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "fixture.sqlite"
        con = sqlite3.connect(db)
        con.execute(
            "create table items(id integer primary key, category integer, title text)"
        )
        con.executemany(
            "insert into items values (?,?,?)",
            ((i, i % 1000, "Item " + str(i)) for i in range(50000)),
        )
        con.commit()
        query = "select id,title from items where category=? order by id"
        before = sqlite_probe.probe(db, query, [777], ctx, samples=15)
        con.execute("create index items_category on items(category)")
        con.commit()
        con.close()
        after = sqlite_probe.probe(db, query, [777], ctx, samples=15)
        assert {r["result_sha256"] for r in before["observations"]} == {
            r["result_sha256"] for r in after["observations"]
        }
        result = compare.compare(before, after)
        assert result["passed"], result
        assert any("SCAN" in str(row) for row in before["plan"])
        assert any("SEARCH" in str(row) for row in after["plan"])
    delay = [0.1]

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(delay[0])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok","count":50}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        config = dict(
            url=url,
            allowed_origins=[url],
            samples=7,
            interval_seconds=0.1,
            expected_json={"status": "ok", "count": 50},
            context=dict(ctx, scenario="API-fixture", cache_state="fixture-delay"),
        )
        api_before = api_probe.probe(config)
        delay[0] = 0.001
        api_after = api_probe.probe(config)
        api_result = compare.compare(api_before, api_after)
        assert api_result["passed"], api_result
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    evidence = dict(
        passed=True,
        database=dict(before=before, after=after, comparison=result),
        api=dict(before=api_before, after=api_after, comparison=api_result),
        boundary="Synthetic SQLite index repair and artificial API delay removal; not a production improvement claim",
    )
    save(output, evidence)
    print(
        json.dumps(
            {
                "passed": True,
                "db_p95_before": result["metrics"][0]["before_p95"],
                "db_p95_after": result["metrics"][0]["after_p95"],
                "api_p95_before": api_result["metrics"][0]["before_p95"],
                "api_p95_after": api_result["metrics"][0]["after_p95"],
            }
        )
    )


if __name__ == "__main__":
    run(sys.argv[1])
