# Functional bug audit

Inventory and prioritize real user journeys. Check authorization/roles, navigation/back/deep links, search/filter/sort, forms, loading/empty/error/success, optimistic updates, cancellation, replay/retry, double taps, stale responses, races, offline recovery and data consistency as applicable.

For every bug record preconditions, input, expected/actual result, location, severity, confidence, root cause and evidence. A source suspicion is not automatically a runtime-confirmed defect. Inspect both abuse/edge cases and ordinary successful paths. Verify state/side effects, not only status codes or toast text.

Use synthetic roles/accounts/data and sandbox integrations for writes, payments and notifications. Do not send live messages or make purchases as a generic quality test. Test load/concurrency only in an explicitly authorized environment and preserve relevant security controls.

Write regression checks that fail on the original defect when feasible. Then repair the boundary and sibling paths. Keep unrelated baseline failures separate. Design changes must preserve business behavior; data-path changes must preserve what the UI shows and when it updates. Fresh integrated acceptance follows all companion changes.
