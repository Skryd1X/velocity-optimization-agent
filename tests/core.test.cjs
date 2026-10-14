"use strict";
const test = require("node:test"),
  assert = require("node:assert/strict");
const {
  validate,
} = require("../skills/velocity-optimization-agent/scripts/benchmark-web.cjs");
const catalog = require("../skills/velocity-optimization-agent/assets/device-catalog.json");
function config() {
  return {
    url: "http://localhost:8000",
    allowed_origins: ["http://localhost:8000"],
    samples: 7,
    context: {
      scenario: "home",
      environment: "fixture",
      build_mode: "release",
      device: "browser",
      dataset: "v1",
      workload: "navigation",
      cache_state: "fresh-browser-context",
    },
  };
}
test("scope accepts declared origin", () =>
  assert.equal(validate(config()).size, 1));
test("scope rejects unrelated origin", () =>
  assert.throws(() => validate({ ...config(), url: "https://example.com" })));
test("samples are bounded", () =>
  assert.throws(() => validate({ ...config(), samples: 100 })));
test("fresh cache contract", () =>
  assert.throws(() =>
    validate({
      ...config(),
      context: { ...config().context, cache_state: "warm" },
    }),
  ));
test("device snapshot is substantive", () =>
  assert.ok(JSON.stringify(catalog).includes("iPhone")));
