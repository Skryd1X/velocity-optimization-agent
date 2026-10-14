"use strict";
const fs = require("node:fs");
const { loadPlaywright } = require("./playwright-runtime.cjs");
function validate(c) {
  const keys = [
    "scenario",
    "environment",
    "build_mode",
    "device",
    "dataset",
    "workload",
    "cache_state",
  ];
  if (
    keys.some((k) => typeof c.context?.[k] !== "string" || !c.context[k].trim())
  )
    throw Error("Complete context required");
  const u = new URL(c.url);
  if (!["http:", "https:"].includes(u.protocol) || u.username || u.password)
    throw Error("Unsafe URL");
  const allowed = new Set(c.allowed_origins.map((x) => new URL(x).origin));
  if (!allowed.has(u.origin)) throw Error("URL outside scope");
  if (!Number.isInteger(c.samples) || c.samples < 5 || c.samples > 30)
    throw Error("Samples must be 5..30");
  if (
    c.timeout_ms !== undefined &&
    (!Number.isInteger(c.timeout_ms) ||
      c.timeout_ms < 100 ||
      c.timeout_ms > 60000)
  )
    throw Error("Timeout must be 100..60000 ms");
  if (c.context.cache_state !== "fresh-browser-context")
    throw Error("This runner requires fresh-browser-context");
  return allowed;
}
async function benchmark(c, pw = loadPlaywright()) {
  const allowed = validate(c),
    browser = await pw.chromium.launch({ headless: true });
  const values = [],
    observations = [];
  try {
    for (let i = 0; i < c.samples; i++) {
      const context = await browser.newContext({
        viewport: c.viewport || { width: 1280, height: 800 },
        serviceWorkers: "block",
      });
      let outOfScope = 0;
      await context.route("**/*", async (route) => {
        const u = new URL(route.request().url());
        if (
          ["http:", "https:"].includes(u.protocol) &&
          !allowed.has(u.origin)
        ) {
          outOfScope++;
          await route.abort();
        } else await route.continue();
      });
      const page = await context.newPage();
      const errors = [];
      page.on("pageerror", (e) => errors.push(e.name));
      try {
        const response = await page.goto(c.url, {
          waitUntil: "load",
          timeout: c.timeout_ms || 15000,
        });
        if (response?.status() !== 200) throw Error("Unexpected status");
        if (c.ready_selector)
          await page
            .locator(c.ready_selector)
            .waitFor({ state: "visible", timeout: 5000 });
        await page.waitForFunction(
          () => performance.getEntriesByType("navigation")[0]?.loadEventEnd > 0,
          {},
          { timeout: 1000 },
        );
        const timings = await page.evaluate(() => {
          const n = performance.getEntriesByType("navigation")[0];
          const r = performance.getEntriesByType("resource");
          return {
            load_ms: n.loadEventEnd - n.startTime,
            resources: r.length,
            transfer_bytes: r.reduce((s, x) => s + x.transferSize, 0),
          };
        });
        if (errors.length || outOfScope)
          throw Error("Page errors or blocked scope");
        values.push(timings.load_ms);
        observations.push({ success: true, ...timings });
      } catch (error) {
        observations.push({
          success: false,
          error_type: error.name,
          page_errors: errors,
          out_of_scope: outOfScope,
        });
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  return {
    schema_version: 1,
    context: c.context,
    revision: c.revision,
    failures: observations.filter((x) => !x.success).length,
    metrics: [
      {
        name: "navigation_load",
        unit: "ms",
        direction: "lower",
        samples: values,
      },
    ],
    observations,
    evidence:
      "Chromium lab navigation; fresh browser cache, not guaranteed cold server/OS cache; no field INP or physical-device claim",
  };
}
if (require.main === module) {
  const i = process.argv.indexOf("--config");
  if (i < 0) throw Error("--config required");
  const c = JSON.parse(fs.readFileSync(process.argv[i + 1], "utf8"));
  if (!c.output) throw Error("Fresh output file required");
  benchmark(c)
    .then((r) =>
      fs.writeFileSync(c.output, JSON.stringify(r, null, 2) + "\n", {
        flag: "wx",
      }),
    )
    .catch((e) => {
      console.error(e.message);
      process.exitCode = 1;
    });
}
module.exports = { benchmark, validate };
