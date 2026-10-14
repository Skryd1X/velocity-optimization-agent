# Velocity Optimization Agent

**Created by Skryd1X.** A portable English-language skill for platform discovery, measured performance optimization, functional bug repair, responsive quality and guarded coordination with Kinesis Design Studio and Aegis Security Agent.

The agent discovers the actual system, measures complete user journeys, repairs verified root causes and repeats integrated checks. Web/mini-app/native/desktop/backend work uses appropriate platform evidence. Existing architecture, behavior, data correctness, design identity and security remain authoritative.

## Install

Clone the repository and install for Claude Code and Codex:

```text
git clone https://github.com/Skryd1X/velocity-optimization-agent.git
cd velocity-optimization-agent
python scripts/install.py --agent both --user
```

Alternatively, install into a specific existing application project:

```text
python scripts/install.py --agent both --user
python scripts/install.py --agent codex --project /path/to/application
python scripts/install.py --agent claude --project /path/to/application
```

The installer refuses to replace existing installations. Reload/restart discovery if necessary. No browser, profiler, monitoring service or companion is installed by this command.

Codex: `Use $velocity-optimization-agent to audit and optimize this project, fix bugs, verify responsive quality and coordinate Kinesis/Aegis when needed.`

Claude Code direct installation: `/velocity-optimization-agent Audit and optimize this project, fix bugs and retest.`

The local marketplace can be added with `/plugin marketplace add /absolute/path/to/velocity-optimization-agent`, then `/plugin install velocity-optimization-agent@velocity-optimization-agent-marketplace`. Plugin invocation: `/velocity-optimization-agent:velocity-optimization-agent`.

Repository: [Skryd1X/velocity-optimization-agent](https://github.com/Skryd1X/velocity-optimization-agent).

## Tools

- discover.py: bounded read-only manifest/file inventory and platform signals.
- api_probe.py: scoped sequential API latency/bytes/errors and optional JSON correctness.
- sqlite_probe.py: read-only bounded query plan/result/latency checks.
- benchmark-web.cjs: repeated browser navigation/resource/lab observations.
- compare.py: comparable-context median/tail/budget comparison without hiding failures.
- profiles.cjs and audit-ui.cjs: 207-device snapshot, generic/breakpoint/sweep profiles, layout/hit/style/motion probes.
- companion_guard.py: discovery, pinned allowlisted installation, no-overwrite/no-repeat state and bounded task claims.
- acceptance.py: declared evidence/coverage/finding/performance/companion closure gate.

Python helpers require Python 3.10+ with no third-party Python packages. Browser helpers need Node 20+ and Playwright. Optional setup from this package root: `npm ci --ignore-scripts`, then `npx playwright install chromium`. Tools can also resolve an approved Playwright installation from the invoking project.

See the skill's references/tooling.md and assets/ configurations. Helpers never prove full product quality alone. Source inspection, lab measurements, browser emulation, deployed telemetry and actual device evidence must be labeled separately.

## Companion behavior

Known repositories: https://github.com/Skryd1X/kinesis-design-studio and https://github.com/Skryd1X/aegis-security-agent. Reviewed immutable refs are in assets/companions.json. Existing compatible installations are reused. --allow-install is used only when installation is already authorized. Installed-but-not-loaded becomes needs-reload; repeated calls do not reinstall. Same-key failed attempts do not repeatedly fetch. Changed reviewed versions/conditions are explicit decisions.

A skill installation does not create a separate agent or load every host session. Use actual host discovery/activation or available authorized delegation. The coordinator owns final acceptance and prevents recursion or overlapping patches.

## Validation

```text
python scripts/validate_package.py
python -m unittest discover -s tests -p "test_*.py" -v
npm test
npm run test:browser
```

See VALIDATION.md for actual fixture results and limits. No universal bug-free/device-perfect or field-performance claim is made. Native/GPU/server validation requires the corresponding available environment. No persistent monitoring or publication occurs automatically.

Set `VELOCITY_FULL_MATRIX=1` before `npm run test:browser` to execute the complete generated synthetic Chromium layout/interaction matrix. Set `VELOCITY_BROWSER_REPORT` to a fresh JSON file path to retain raw browser evidence. The device descriptors do not imply physical-device testing or testing in every device's preferred browser engine.

The included CI workflow runs on Windows and Linux. See [GitHub Actions](https://github.com/Skryd1X/velocity-optimization-agent/actions) for current hosted results. VALIDATION.md records the original local validation before publication. Manual host behavior scenarios are in tests/evaluation-scenarios.md; automated helper checks are not a substitute for client/agent evaluation.

## License

Original work MIT, Copyright (c) 2026 Skryd1X. Device data retains Apache-2.0; see THIRD_PARTY_NOTICES.md. Companion packages retain their own terms. Official-source index: skills/velocity-optimization-agent/references/standards.md.
