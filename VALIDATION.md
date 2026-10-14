# Validation record

Date: 2026-10-14. Version: 1.0.0. Creator: Skryd1X.

## Executed and passed

- Canonical skill validation passed with the skill-creator validator.
- Package validation passed: one active SKILL.md, Python syntax, JSON, local documentation links, exact hashes for ten shared files and 207 device descriptors.
- 22 Python unit tests passed: discovery bounds/mixed signals, comparison correctness/conditions/budgets, read-only SQLite/row/time bounds, companion discovery/failure caching/registry locking/task recursion/loading, acceptance boundaries and both-client installer/no-overwrite.
- Five Node unit tests passed: URL scope, sample/cache requirements and descriptor snapshot.
- Synthetic database integration: 50,000 SQLite rows, 15 reads before and after adding a fixture index; identical result hashes; SCAN changed to SEARCH. Observed query p95: 3.888 -> 0.342 ms.
- Synthetic API integration: seven sequential reads before and after removing an artificial handler delay; expected JSON checked. Observed total p95: 121.256 -> 26.267 ms.
- Synthetic browser integration: three defective and three repaired layouts, 14 navigation measurements, plus 300 repaired layout/interaction profiles. Overflow and button occlusion were detected before repair; all repaired checks passed and button actions completed.
- Chromium navigation load median: 214.700 -> 37.900 ms; p95 230.300 -> 40.900 ms after removing an artificial blocking-script delay.
- Both real companions fetched at the bundled immutable commits into an isolated fixture project; repeated ensure reused installed directories. Status remained needs-reload. No current-host companion execution claim.
- An empty/pending acceptance ledger was rejected as intended.
- Original Python helpers passed Ruff 0.14.0 checks (test bootstrap import-order exception). Original browser runner/tests formatted with Prettier 3.6.2. Shared Kinesis files retain exact upstream bytes.

## Evidence and limits

Raw synthetic observations are in validation/fixtures.json, validation/browser-matrix.json and validation/browser-comparison.json. Companion receipts are in validation/companion-installation.json. Earlier browser reports retain earlier local checks.

These timings demonstrate helper behavior on deliberately constructed fixtures; they are not improvements to a customer product. The 300-profile matrix is Chromium emulation, not physical-device coverage or every descriptor's preferred browser engine. It does not establish field Web Vitals, native GPU/energy/thermal behavior, actual production database capacity or absence of unknown bugs.

The included Windows/Linux CI workflow is prepared but not run remotely. Claude/Codex host behavior scenarios are documented, not executed evaluations. No Velocity publication, global installation, production deployment or persistent monitoring was performed.
