# Reproducible measurement

Measure useful work: complete page/app startup, a meaningful API operation, a database result, an interaction or rendering a required state. Specify when the timer starts/stops and whether the data and interaction succeeded. Distinguish end-to-end latency from a query's execution time, framework render time and network transfer.

Before/after context must identify scenario, environment, build mode, device/hardware, dataset, workload and cache state. Revisions may differ, but comparable context should not. Match tool/version and statistical procedure; changing data size, concurrency, hardware or warmed cache is not evidence of a code improvement. Separate intentionally changed architecture experiments from ordinary comparisons.

Repeat representative runs with warmups disclosed. Use median, p95/p99 when sample volume supports meaningful interpretation, raw samples and error rates. Five samples can support a small local comparison but do not establish a reliable production tail distribution. Treat small/noisy changes as inconclusive until further evidence is justified. Don't keep rerunning merely to obtain a favorable sample.

Web: measure field LCP/INP/CLS through a maintained implementation/RUM where authorized. Lab navigation/paint/resource timings are diagnostic evidence; observed LCP until a local sampling cutoff is not full field conformance. Lighthouse TBT is not INP. Native: use release/profile builds and platform profilers. GPU/display/battery/thermal behavior needs suitable device evidence.

Record correctness and failures for every benchmark. A timeout, truncated response or wrong result cannot count as a fast successful operation. Keep timeout bounds, sampling rates and workload within authorized scope. Stress/load tests belong in an approved isolated environment. Avoid storing response bodies, SQL parameters, auth headers or customer data in public reports.
