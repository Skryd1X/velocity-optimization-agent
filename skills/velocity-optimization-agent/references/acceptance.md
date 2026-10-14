# Acceptance and evidence ledger

Use assets/ledger.example.json and acceptance.py. Required applicable check categories: discovery, performance, data, functional, responsive, accessibility and security. Declared required companions must be ready and their scoped tasks integrated/validated. data/ responsive can be not-applicable with a real platform/scope reason; core discovery/performance/functional/security checks cannot be skipped merely because evidence is missing.

Coverage entries need component/control, reviewed/blocked/not-applicable status and evidence or exclusion reason. Findings have stable id, severity (blocking/high/medium/low), confidence (confirmed/suspected), status (open/fixed-unverified/verified/residual/false-positive), description and evidence. Verified needs regression/validation; false-positive needs an evidence-backed reason; residual needs owner/reason. Unresolved blocking/high or open findings prevent acceptance. Minor residuals stay visible.

Performance acceptance requires passing project budgets and a comparable before/after measurement, or explicit evidence that the measured baseline was already within the budget and no change was necessary. Do not fabricate a speedup for an already-good path. At least two documented passes (baseline/initial review and final integrated review) are required.

The helper checks declared consistency only. The agent must inspect the actual measurements, screenshots/tests and companion evidence. Local/staging/emulated/deployed/physical-device evidence must be distinguished. An assignment may stop at an explicit boundary while the technical acceptance gate remains incomplete.
