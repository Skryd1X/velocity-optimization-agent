import sys
import unittest
import tempfile
import json
import sqlite3
import threading
import subprocess
import importlib.util
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "skills/velocity-optimization-agent/scripts"
sys.path.insert(0, str(S))
import discover
import compare
import api_probe
import sqlite_probe
import companion_guard
import acceptance

spec = importlib.util.spec_from_file_location(
    "velocity_installer", ROOT / "scripts/install.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
CTX = dict(
    scenario="lookup",
    environment="synthetic-local",
    build_mode="release",
    device="local-host",
    dataset="fixture-v1",
    workload="sequential-read",
    cache_state="warm",
)


def measurement(values, failures=0):
    return dict(
        context=CTX,
        failures=failures,
        metrics=[dict(name="time", unit="ms", direction="lower", samples=values)],
    )


class Tools(unittest.TestCase):
    def test_installer_both_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            paths = installer.install("both", Path(d))
            self.assertEqual(len(paths), 2)
            for p in paths:
                self.assertTrue((p / "SKILL.md").is_file())
            with self.assertRaises(FileExistsError):
                installer.install("both", Path(d))

    def test_metadata_must_be_frontmatter(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "SKILL.md").write_text(
                "Example\\nname: aegis-security-agent\\n version: 1.0.0\\n"
            )
            self.assertFalse(companion_guard.metadata(p, "aegis-security-agent"))

    def test_invalid_failure_counter(self):
        with self.assertRaises(ValueError):
            compare.compare(measurement([3] * 7), measurement([2] * 7, -1))

    def test_discovery_mixed_and_exclusion(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "package.json").write_text(
                json.dumps(
                    {
                        "dependencies": {
                            "next": "1",
                            "expo": "1",
                            "@telegram-apps/sdk": "1",
                        }
                    }
                )
            )
            (p / "node_modules").mkdir()
            (p / "node_modules/package.json").write_text("{}")
            r = discover.discover(p)
            self.assertEqual(
                {x["platform"] for x in r["signals"]},
                {"web", "native-mobile", "telegram-mini-app"},
            )
            self.assertEqual(r["files_seen"], 1)

    def test_discovery_bound(self):
        with tempfile.TemporaryDirectory() as d:
            for i in range(3):
                (Path(d) / str(i)).touch()
            self.assertTrue(discover.discover(d, 1)["truncated"])

    def test_compare_improvement(self):
        self.assertTrue(
            compare.compare(measurement([10] * 7), measurement([2] * 7))["passed"]
        )

    def test_compare_regression(self):
        self.assertFalse(
            compare.compare(measurement([2] * 7), measurement([10] * 7))["passed"]
        )

    def test_compare_errors(self):
        self.assertFalse(
            compare.compare(measurement([10] * 7), measurement([2] * 7, 1))["passed"]
        )

    def test_compare_context(self):
        a = measurement([2] * 7)
        a["context"] = dict(CTX, dataset="different")
        with self.assertRaises(ValueError):
            compare.compare(measurement([10] * 7), a)

    def test_compare_invalid_samples(self):
        for values in ([1] * 4, [float("nan")] * 7, [True] * 7):
            with self.assertRaises(ValueError):
                compare.compare(measurement([10] * 7), measurement(values))

    def test_budget(self):
        a = measurement([2] * 7)
        a["metrics"][0]["budget_p95"] = 1
        self.assertFalse(compare.compare(measurement([10] * 7), a)["passed"])

    def test_readonly_sql_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "db.sqlite"
            c = sqlite3.connect(p)
            c.execute("create table t(x)")
            c.executemany("insert into t values (?)", [(1,), (2,)])
            c.commit()
            c.close()
            r = sqlite_probe.probe(p, "select x from t order by x", [], CTX)
            self.assertEqual(r["failures"], 0)
            self.assertEqual(len({x["result_sha256"] for x in r["observations"]}), 1)
            with self.assertRaises(sqlite3.Error):
                sqlite_probe.probe(p, "delete from t", [], CTX)
            with self.assertRaises(sqlite3.Error):
                sqlite_probe.probe(
                    p,
                    "attach database :name as other",
                    {"name": str(Path(d) / "other")},
                    CTX,
                )
            self.assertEqual(
                sqlite_probe.probe(p, "select * from t", [], CTX, max_rows=1)[
                    "failures"
                ],
                7,
            )
            self.assertGreater(
                sqlite_probe.probe(
                    p,
                    "WITH RECURSIVE x(a) AS (SELECT 1 UNION ALL SELECT a+1 FROM x WHERE a<100000000) SELECT sum(a) FROM x",
                    [],
                    CTX,
                    timeout=0.001,
                )["failures"],
                0,
            )

    def test_companion_missing_once(self):
        with tempfile.TemporaryDirectory() as d:
            s = {}
            self.assertTrue(
                companion_guard.ensure(s, "aegis-security-agent", "codex", d)[
                    "suggest_install"
                ]
            )
            self.assertFalse(
                companion_guard.ensure(s, "aegis-security-agent", "codex", d)[
                    "suggest_install"
                ]
            )

    def test_companion_failure_no_retry(self):
        with tempfile.TemporaryDirectory() as d:
            s = {}
            calls = []

            def fail(*args):
                calls.append(1)
                raise OSError("fixture")

            for _ in range(2):
                self.assertEqual(
                    companion_guard.ensure(
                        s,
                        "aegis-security-agent",
                        "codex",
                        d,
                        allow_install=True,
                        fetcher=fail,
                    )["status"],
                    "failed",
                )
            self.assertEqual(len(calls), 1)

    def test_existing_companion_reload(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".agents/skills/aegis-security-agent"
            p.mkdir(parents=True)
            (p / "SKILL.md").write_text(
                '---\nname: aegis-security-agent\nmetadata:\n  version: "1.0.0"\n---\n'
            )
            s = {}
            self.assertEqual(
                companion_guard.ensure(s, "aegis-security-agent", "codex", d)["status"],
                "needs-reload",
            )
            self.assertEqual(
                companion_guard.ensure(
                    s, "aegis-security-agent", "codex", d, loaded=True
                )["status"],
                "ready",
            )

    def test_existing_incompatible_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".agents/skills/aegis-security-agent"
            p.mkdir(parents=True)
            (p / "SKILL.md").write_text("invalid")
            self.assertEqual(
                companion_guard.ensure(
                    {}, "aegis-security-agent", "codex", d, allow_install=True
                )["status"],
                "failed",
            )
            self.assertEqual((p / "SKILL.md").read_text(), "invalid")

    def test_companion_task_guard(self):
        s = {
            "companions": {
                "test:aegis-security-agent": {"status": "ready"},
                "test:kinesis-design-studio": {"status": "ready"},
            }
        }
        a = companion_guard.claim(s, "aegis-security-agent", "auth", "abc")
        self.assertTrue(a["dispatch"])
        self.assertFalse(
            companion_guard.claim(s, "aegis-security-agent", "auth", "abc")["dispatch"]
        )
        self.assertFalse(
            companion_guard.claim(s, "kinesis-design-studio", "auth", "def")["dispatch"]
        )
        with self.assertRaises(ValueError):
            companion_guard.claim(s, "aegis-security-agent", "auth", "abc", 2)
        companion_guard.finish(s, a["key"], "completed", ["fixture evidence"])
        self.assertFalse(
            companion_guard.claim(s, "aegis-security-agent", "auth", "abc")["dispatch"]
        )

    def test_companion_unloaded_not_dispatched(self):
        self.assertFalse(
            companion_guard.claim({}, "aegis-security-agent", "auth", "abc")["dispatch"]
        )

    def test_busy_registry(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            Path(str(p) + ".lock").touch()
            r = subprocess.run(
                [
                    sys.executable,
                    str(S / "companion_guard.py"),
                    "--state",
                    str(p),
                    "ensure",
                    "--name",
                    "aegis-security-agent",
                    "--client",
                    "codex",
                    "--root",
                    d,
                ],
                capture_output=True,
            )
            self.assertEqual(r.returncode, 3)
            self.assertFalse(p.exists())

    def test_acceptance_boundaries(self):
        ledger = dict(
            checks={
                k: dict(status="passed", evidence=["fixture"])
                for k in acceptance.REQUIRED
            },
            integrated_passes=2,
            performance=dict(status="comparison-passed", evidence=["fixture"]),
        )
        self.assertTrue(acceptance.check(ledger)["passed"])
        ledger["companions"] = [dict(required=True, status="needs-reload")]
        self.assertFalse(acceptance.check(ledger)["passed"])
        ledger.pop("companions")
        ledger["findings"] = [
            dict(severity="high", status="residual", reason="fixture")
        ]
        self.assertFalse(acceptance.check(ledger)["passed"])

    def test_api_scope(self):
        with self.assertRaises(ValueError):
            api_probe.probe(
                dict(
                    context=CTX,
                    url="https://example.com",
                    allowed_origins=["http://localhost"],
                )
            )
        with self.assertRaises(ValueError):
            api_probe.origin("https://user:password@example.com")

    def test_api_response_correctness(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"wrong"}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            c = dict(
                context=CTX,
                url=url,
                allowed_origins=[url],
                samples=5,
                interval_seconds=0.1,
                expected_json={"status": "ok"},
            )
            self.assertEqual(api_probe.probe(c)["failures"], 5)
            c["expected_json"] = {"status": "wrong"}
            self.assertEqual(api_probe.probe(c)["failures"], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
