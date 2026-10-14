"""Compare raw samples only under identical declared measurement conditions."""

import argparse
import statistics
import math
from common import read, save, context, percentile


def compare(before, after):
    if any(
        type(x.get("failures")) is not int or x["failures"] < 0 for x in (before, after)
    ):
        raise ValueError("Nonnegative failure counts required")
    if context(before["context"]) != context(after["context"]):
        raise ValueError("Incomparable measurement contexts")
    bm = {m["name"]: m for m in before["metrics"]}
    am = {m["name"]: m for m in after["metrics"]}
    if not bm or bm.keys() != am.keys():
        raise ValueError("Metric sets differ or are empty")
    rows = []
    passed = before.get("failures") == 0 and after.get("failures") == 0
    for name, b in bm.items():
        a = am[name]
        if (
            b["unit"] != a["unit"]
            or b["direction"] != a["direction"]
            or a["direction"] not in ("lower", "higher")
        ):
            raise ValueError("Metric definitions differ")
        for m in (b, a):
            if len(m["samples"]) < 5 or any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                or v < 0
                for v in m["samples"]
            ):
                raise ValueError("At least five finite nonnegative samples required")
        bp, ap = percentile(b["samples"]), percentile(a["samples"])
        sign = 1 if a["direction"] == "lower" else -1
        delta = sign * (ap - bp)
        status = "regressed" if delta > 0 else "improved" if delta < 0 else "unchanged"
        budget = a.get("budget_p95")
        if budget is not None and (
            type(budget) not in (int, float) or not math.isfinite(budget) or budget < 0
        ):
            raise ValueError("Invalid budget")
        budget_ok = budget is None or (ap <= budget if sign == 1 else ap >= budget)
        passed = passed and delta <= 0 and budget_ok
        rows.append(
            dict(
                name=name,
                unit=a["unit"],
                before_median=statistics.median(b["samples"]),
                after_median=statistics.median(a["samples"]),
                before_p95=bp,
                after_p95=ap,
                status=status,
                budget_pass=budget_ok,
                improvement_percent=None if bp == 0 else -delta / bp * 100,
            )
        )
    return dict(
        schema_version=1,
        context=before["context"],
        passed=passed,
        metrics=rows,
        failures_before=before["failures"],
        failures_after=after["failures"],
        tail_note="Small samples are local observations, not population tail estimates",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("before")
    p.add_argument("after")
    p.add_argument("--output", required=True)
    a = p.parse_args()
    save(a.output, compare(read(a.before), read(a.after)))
