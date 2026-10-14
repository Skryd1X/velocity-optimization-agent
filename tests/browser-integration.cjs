"use strict";
const http = require("node:http"),
  assert = require("node:assert/strict"),
  fs = require("node:fs"),
  path = require("node:path");
const {
  benchmark,
} = require("../skills/velocity-optimization-agent/scripts/benchmark-web.cjs");
const {
  inspectDOM,
} = require("../skills/velocity-optimization-agent/scripts/dom-probe.cjs");
const {
  makeProfiles,
} = require("../skills/velocity-optimization-agent/scripts/profiles.cjs");
const {
  loadPlaywright,
} = require("../skills/velocity-optimization-agent/scripts/playwright-runtime.cjs");
async function main() {
  let repaired = false;
  const server = http.createServer((req, res) => {
    if (req.url === "/data") {
      setTimeout(
        () => {
          res.setHeader("Content-Type", "application/json");
          res.end('{"status":"ok"}');
        },
        repaired ? 1 : 180,
      );
      return;
    }
    if (req.url === "/blocking.js") {
      setTimeout(
        () => {
          res.setHeader("Content-Type", "text/javascript");
          res.end("window.fixtureReady=true;");
        },
        repaired ? 1 : 180,
      );
      return;
    }
    res.setHeader("Content-Type", "text/html");
    res.end(
      `<!doctype html><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;font:16px system-ui}main{${repaired ? "width:100%;box-sizing:border-box" : "width:1600px"};padding:20px}button{width:120px;height:48px}.overlay{position:fixed;inset:0;${repaired ? "pointer-events:none;opacity:0" : "background:#0002"}} </style><main><h1>Fixture</h1><button id="action">Continue</button><output id="result"></output></main><div class="overlay"></div><script src="/blocking.js"></script><script>document.querySelector('button').onclick=()=>document.querySelector('output').textContent='Done';</script>`,
    );
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const pw = loadPlaywright(),
    browser = await pw.chromium.launch({ headless: true });
  const report = {
    schema_version: 1,
    fixture: "synthetic UI/navigation defects",
    layouts: [],
  };
  const config = {
    url: origin,
    allowed_origins: [origin],
    samples: 7,
    ready_selector: "main",
    context: {
      scenario: "fixture-home",
      environment: "local-fixture",
      build_mode: "release",
      device: "chromium-1280x800",
      dataset: "fixture-v1",
      workload: "navigation",
      cache_state: "fresh-browser-context",
    },
  };
  try {
    report.before = await benchmark(config, pw);
    assert.equal(report.before.failures, 0);
    for (const phase of ["before", "after"]) {
      repaired = phase === "after";
      for (const viewport of [
        { width: 320, height: 720 },
        { width: 768, height: 1024 },
        { width: 1440, height: 900 },
      ]) {
        const page = await browser.newPage({ viewport });
        await page.goto(origin);
        const result = await page.evaluate(inspectDOM, {
          controls: [{ selector: "#action", required: true, inViewport: true }],
        });
        if (phase === "before") {
          assert.ok(
            result.issues.some((x) => x.code === "horizontal-overflow"),
          );
          assert.ok(result.issues.some((x) => x.code === "occluded-control"));
        } else {
          assert.deepEqual(result.issues, []);
          await page.locator("#action").click();
          assert.equal(await page.locator("#result").textContent(), "Done");
        }
        report.layouts.push({ phase, viewport, issues: result.issues });
        await page.close();
      }
    }
    report.after = await benchmark(config, pw);
    assert.equal(report.after.failures, 0);
    const median = (a) =>
      a.slice().sort((a, b) => a - b)[Math.floor(a.length / 2)];
    assert.ok(
      median(report.after.metrics[0].samples) <
        median(report.before.metrics[0].samples) * 0.5,
    );
    const profiles = makeProfiles({
      tier: "full",
      breakpoints: [600, 768, 1024],
      devices: pw.devices,
      sweep: true,
    });
    report.full_profile_count = profiles.length;
    assert.ok(report.full_profile_count >= 250);
    report.matrix_runs = [];
    if (process.env.VELOCITY_FULL_MATRIX === "1") {
      for (const profile of profiles) {
        const { id, deviceName, preferredBrowser, ...options } = profile;
        const page = await browser.newPage(options);
        try {
          await page.goto(origin);
          const result = await page.evaluate(inspectDOM, {
            controls: [{ selector: "#action", required: true, inViewport: true }],
          });
          assert.deepEqual(result.issues, [], id);
          await page.locator("#action").click();
          assert.equal(await page.locator("#result").textContent(), "Done", id);
          report.matrix_runs.push({ id, viewport: profile.viewport, browser: "chromium", issues: result.issues, interaction: "passed" });
        } finally { await page.close(); }
      }
    }
    report.passed = true;
    report.boundary =
      "Synthetic Chromium layout/interaction and navigation runs; emulated device matrix is not physical-device or preferred-engine coverage";
    const target = process.env.VELOCITY_BROWSER_REPORT;
    if (target) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, JSON.stringify(report, null, 2) + "\n", {
        flag: "wx",
      });
    }
    console.log(
      JSON.stringify({
        passed: true,
        layout_runs: report.layouts.length,
        navigation_runs: 14,
        full_profile_count: report.full_profile_count,
        matrix_runs: report.matrix_runs.length,
        before_median: median(report.before.metrics[0].samples),
        after_median: median(report.after.metrics[0].samples),
      }),
    );
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
}
main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
