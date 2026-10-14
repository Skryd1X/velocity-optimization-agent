# Executable helpers

Python 3.10+ helpers use only the standard library. Browser helpers need Node 20+ and a reviewed Playwright installation. The browser runner can resolve Playwright from the skill/package or invoking project; it does not install tools silently.

Run paths relative to the skill directory:

```text
python scripts/discover.py /path/to/project --output discovery.json
python scripts/api_probe.py --config /path/to/api-config.json --output api-baseline.json
python scripts/sqlite_probe.py --database /path/to/test.sqlite --query /path/to/query.sql --params /path/to/params.json --context /path/to/context.json --output db-baseline.json
python scripts/compare.py baseline.json final.json --output comparison.json
node scripts/benchmark-web.cjs --config /path/to/web-config.json
node scripts/profiles.cjs --tier full --breakpoints 640,768,1024 --output profiles.json
node scripts/audit-ui.cjs --config /path/to/ui-config.json
python scripts/companion_guard.py --state /path/to/registry.json ensure --name kinesis-design-studio --client codex --root /path/to/project
python scripts/acceptance.py /path/to/ledger.json
```

See assets/ for configurations. API probes use bounded sequential GET/HEAD requests, scoped redirects, error/byte counts and optional JSON correctness checks; they are not load tests or database tracing. SQLite uses read-only authorizer/time/row bounds and hashes query/results without publishing query text/parameters. Web measurements are lab navigation/resource observations, not INP/field certification.

Use the real stack's profilers/adapters for PostgreSQL/MySQL/etc., native apps and embedded hosts. These helpers support reproducibility, not universal platform automation. All output directories/files must be fresh to preserve failed evidence. Reports can include local endpoint paths/benchmark context; review/redact before publication.

SQLite context JSON has the same seven context fields shown in api-config.example.json. SQLite output deliberately omits query text, parameters and row values, but plans can expose schema names. Row/time bounds do not imply bounded size of a single database cell. Use a representative authorized local/staging copy. Browser navigation load timing is not time to a successful business action; add real journey assertions and timings through the project's supported test/profiling stack.
