# Guarded companion integration

## Discovery and installation

Sources and immutable default refs are in assets/companions.json. They are our verified local publication snapshots, not automatically the newest remote release. Update this file only after reviewing a newer version; do not silently pull changing main into a long-running task.

Use actual host discovery. Pass --loaded when the client genuinely exposes the companion and --path for a host-reported plugin path. Otherwise scan supported project/user directories for the active client. The helper validates canonical name/version and never substitutes a similarly named unrelated skill. Local presence without host loading means present/needs-reload, not ready.

Project and user directories are checked by default. Use --project-only only for an intentionally isolated environment; --include-user remains accepted for explicitness. Cached plugin locations require the path supplied by actual host discovery. Name/version inspection establishes local compatibility, not authenticity of arbitrary existing files.

Run ensure to reuse the existing installation. If absent, required and installation is already authorized, --allow-install fetches the allowlisted repo/ref and copies only skills/<canonical-name>. It does not execute remote installation scripts or modify client settings. It refuses symlinked/new destination escapes and existing installation replacement. An unavailable remote source stays failed, without an automatic same-key retry.

The registry persists dependency state and attempted conditions atomically under an exclusive lock. States: missing, present, ready, needs-reload, failed. Repeated ready/present/needs-reload calls do not reinstall. A failed attempt is retried only with a changed explicit --retry-key representing a new condition, not random timestamps. Failed existing metadata is investigated, not overwritten.

## Task ownership

Use claim with companion, finding/scope key, revision and depth. Depth beyond one is rejected; same scope/revision running/completed is not redispatched. finish requires evidence for a completed task. A failed task needs investigation; reopening requires a changed revision or explicit revised task scope, not blind recursion.

Provide scoped files/findings and expected outcomes. Kinesis handles difficult visual/responsive/motion work; Aegis handles security findings. The coordinator preserves scope and performs final integrated regression/performance checks. Serialize edits to shared files. A companion's final statement is not sufficient proof.

## Authorization and capability

Host/user authorization remains authoritative. Offer missing dependency installation once if it is not already authorized; continue independent work. Installing a skill does not load it into every client session or spawn an agent. Use the same host's skill activation, or authorized supported delegation. Never message unrelated chats or deploy while resolving a dependency.
