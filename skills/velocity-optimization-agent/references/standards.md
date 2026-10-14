# Official guidance and freshness

Research baseline: 2026-10-14. Retrieve the current official guidance for the detected versions during each audit, record applicability/date/URL, and label offline freshness unverified. Do not merge conflicting recommendations into one universal checklist or claim certification.

| Source | Application |
| --- | --- |
| [Google Web Vitals](https://web.dev/articles/vitals) | Field loading/interactivity/stability. Current starting targets: LCP <= 2.5 s, INP <= 200 ms, CLS <= 0.1 at p75 of real visits. Lab measurements are separate; Lighthouse TBT is not INP. |
| [Apple performance engineering](https://developer.apple.com/documentation/xcode/improving-your-app-s-performance/) | Measure/profile/change/retest; Instruments/XCTest/MetricKit and actual devices where relevant. |
| [Android performance measurement](https://developer.android.com/topic/performance/measuring-performance) | Release/profile builds, startup, frame timing, memory, ANR/hangs and representative journeys. |
| [PostgreSQL plans](https://www.postgresql.org/docs/current/using-explain.html) | Actual query/data plans; ANALYZE executes statements and needs appropriate scope. |
| [SQLite query plans](https://www.sqlite.org/eqp.html) | Read-only plan inspection; selective scans/index use evaluated in context. |
| [Telegram Mini Apps](https://core.telegram.org/bots/webapps) | Host viewport, stable height, safe/content insets, theme and lifecycle. |
| [React Profiler](https://react.dev/reference/react/Profiler) | Framework render profiling and costs, not a proxy for entire network/user latency. |
| [Flutter performance](https://docs.flutter.dev/perf/best-practices) | Framework/platform profiling and rendering cost. |
| [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/) | Attributed multi-service timing where instrumentation is appropriate and authorized. |
| [Microsoft ASP.NET Core](https://learn.microsoft.com/en-us/aspnet/core/performance/overview) | Applicable backend/runtime recommendations. |
| [AWS performance efficiency](https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html) | Resource/workload suitability, measurement and operational tradeoffs. |
| [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) and [focus visibility](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) | Accessible adaptation and unobscured keyboard use. |

Link to standards rather than copying their text wholesale. Performance budgets outside the cited web metrics are project/device/workload decisions and must be justified by measured behavior.
