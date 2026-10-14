#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const {inspectDOM, installTelemetry, sampleMotion} = require('./dom-probe.cjs');
const {analyzeMotion} = require('./motion-metrics.cjs');
const {makeProfiles} = require('./profiles.cjs');
const {loadPlaywright} = require('./playwright-runtime.cjs');

function validateConfig(config) {
  if (!config || typeof config !== 'object' || Array.isArray(config)) throw new Error('Configuration must be an object');
  const base = new URL(config.baseURL);
  if (!['http:', 'https:'].includes(base.protocol)) throw new Error('Use an HTTP(S) application URL');
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(base.hostname);
  const allowed = config.allowedOrigins || (local ? [base.origin] : []);
  if (!Array.isArray(allowed) || !allowed.includes(base.origin)) throw new Error('Remote targets require an explicit allowedOrigins entry');
  for (const origin of allowed) if (new URL(origin).origin !== origin) throw new Error('allowedOrigins must contain exact HTTP(S) origins');
  if (!Array.isArray(config.routes) || !config.routes.length) throw new Error('At least one route is required');
  for (const route of config.routes) {
    if (!/^[a-zA-Z0-9_-]+$/.test(route.id || '')) throw new Error('Route IDs must be safe filenames');
    if (!allowed.includes(new URL(route.path || '/', base).origin)) throw new Error('Route escapes allowed origins');
  }
  for (const browser of config.browsers || ['chromium']) if (!['chromium', 'firefox', 'webkit'].includes(browser)) throw new Error('Unsupported browser');
  return {...config, allowedOrigins: allowed};
}

async function actions(page, steps = []) {
  for (const step of steps) {
    const target = step.selector ? page.locator(step.selector).first() : null;
    switch (step.action) {
      case 'click': await target.click({timeout: 5000}); break;
      case 'hover': await target.hover(); break;
      case 'focus': await target.focus(); break;
      case 'fill': await target.fill(String(step.value)); break;
      case 'press': if (target) await target.press(step.key); else await page.keyboard.press(step.key); break;
      case 'wait': await page.waitForTimeout(Math.min(10000, Math.max(0, step.ms || 0))); break;
      case 'scroll': await page.evaluate(y => scrollTo(0, y), step.y || 0); break;
      case 'assert-visible': if (!await target.isVisible()) throw new Error(`Expected visible: ${step.selector}`); break;
      case 'assert-text': if (!(await target.innerText()).includes(step.value)) throw new Error(`Expected text at ${step.selector}`); break;
      default: throw new Error(`Unsupported scenario action: ${step.action}`);
    }
  }
}

async function runAudit(input, playwright) {
  const config = validateConfig(input);
  const output = path.resolve(config.outputDir || 'qa-results');
  if (fs.existsSync(output)) throw new Error('Use a fresh outputDir; existing evidence will not be overwritten');
  fs.mkdirSync(output, {recursive: true});
  const report = {schema_version: 1, startedAt: new Date().toISOString(), revision: config.revision || 'unspecified',
    baseURL: config.baseURL, evidenceLayer: 'browser-emulation', runs: [], limitations: [
      'Geometry, hit-test and motion probes need project contracts and manual visual review.',
      'RAF timing in this environment does not certify real-device GPU/display smoothness.',
      'Not a full accessibility, native-device, true-zoom or security audit.'], issues: []};
  const profiles = config.profiles || makeProfiles({tier: config.tier || 'standard', breakpoints: config.breakpoints || [], devices: playwright.devices});
  if (!profiles.length) throw new Error('Profile matrix is empty');
  for (const profile of profiles) if (!/^[a-zA-Z0-9_-]+$/.test(profile.id || '')) throw new Error('Profile IDs must be safe filenames');
  let launchFailure = false;
  for (const engine of config.browsers || ['chromium']) {
    let browser;
    try { browser = await playwright[engine].launch({headless: true, ...(config.launchOptions || {})}); }
    catch (error) { report.issues.push({code: 'browser-unavailable', engine, severity: 'blocking', details: error.message}); launchFailure = true; continue; }
    try {
      for (const profile of profiles) for (const variant of config.variants || [{id: 'default', colorScheme: 'light', reducedMotion: 'no-preference'}]) {
        if (!/^[a-zA-Z0-9_-]+$/.test(variant.id || '')) throw new Error('Variant IDs must be safe filenames');
        for (const route of config.routes) {
          const id = `${engine}--${profile.id}--${variant.id}--${route.id}`;
          const directory = path.join(output, id);
          fs.mkdirSync(directory);
          const {id: profileId, deviceName, preferredBrowser, ...deviceOptions} = profile;
          if (engine === 'firefox') delete deviceOptions.isMobile;
          const context = await browser.newContext({...deviceOptions, colorScheme: variant.colorScheme || 'light',
            reducedMotion: variant.reducedMotion || 'no-preference', ...(config.recordVideo ? {recordVideo: {dir: directory}} : {})});
          const issues = [], blockedRequests = [];
          // Keep top-level navigations in scope. Subresource origins may be
          // explicitly restricted; this is not a network isolation sandbox.
          await context.route('**/*', async requestRoute => {
            const request = requestRoute.request();
            const url = new URL(request.url());
            const navigation = request.isNavigationRequest() && request.frame() === request.frame().page().mainFrame();
            if (['http:', 'https:'].includes(url.protocol) &&
                ((navigation && !config.allowedOrigins.includes(url.origin)) ||
                 (config.resourceOrigins && !config.resourceOrigins.includes(url.origin)))) {
              blockedRequests.push({url: url.origin + url.pathname, navigation});
              await requestRoute.abort();
            } else await requestRoute.continue();
          });
          await context.addInitScript(installTelemetry);
          const page = await context.newPage();
          page.setDefaultTimeout(10000);
          page.on('pageerror', error => issues.push({code: 'page-error', severity: 'major', details: error.message}));
          page.on('console', message => { if (message.type() === 'error') issues.push({code: 'console-error', severity: 'major', details: message.text()}); });
          let motion = null;
          try {
            const response = await page.goto(new URL(route.path || '/', config.baseURL).href, {waitUntil: 'domcontentloaded', timeout: 20000});
            if (response && response.status() >= 400) throw new Error(`Route returned HTTP ${response.status()}`);
            await page.evaluate(() => document.fonts.ready);
            if (route.readySelector) await page.locator(route.readySelector).waitFor({state: 'visible'});
            await page.waitForTimeout(config.settleMs ?? 100);
            const states = route.states || [{id: 'initial', actions: []}];
            for (const state of states) {
              if (!/^[a-zA-Z0-9_-]+$/.test(state.id || '')) throw new Error('State IDs must be safe filenames');
              await actions(page, state.actions);
              const contracts = {...(config.contracts || {}), ...(route.contracts || {}), ...(state.contracts || {})};
              if (!contracts.controls) contracts.controls = [{selector: '[data-design-critical]', required: false}];
              let findings = await page.evaluate(inspectDOM, contracts);
              issues.push(...findings.issues.map(issue => ({...issue, state: state.id})));
              for (const contract of contracts.controls) {
                const targets = page.locator(contract.selector);
                for (let i = 0; i < await targets.count(); i++) {
                  if (!await targets.nth(i).isVisible()) continue;
                  await targets.nth(i).scrollIntoViewIfNeeded();
                  findings = await page.evaluate(inspectDOM, {controls: [{...contract, inViewport: true}]});
                  issues.push(...findings.issues.map(issue => ({...issue, state: state.id, phase: 'control-reachability'})));
                }
              }
              await page.screenshot({path: path.join(directory, `${state.id}.png`), fullPage: true, animations: 'allow'});
              const contract = state.motion || route.motion;
              if (contract) {
                if (contract.startActions) await actions(page, contract.startActions);
                const selected = variant.reducedMotion === 'reduce' ? (contract.reducedContracts || []) : (contract.contracts || []);
                const sample = await page.evaluate(sampleMotion, {selectors: selected.map(x => x.selector), durationMs: Math.min(10000, Math.max(150, contract.durationMs || 800))});
                motion = analyzeMotion(sample, selected, contract.budgets || {});
                fs.writeFileSync(path.join(directory, `${state.id}-motion.json`), JSON.stringify({sample, analysis: motion}, null, 2));
                issues.push(...motion.issues.map(issue => ({...issue, state: state.id})));
                await page.screenshot({path: path.join(directory, `${state.id}-motion-end.png`), fullPage: true, animations: 'allow'});
              }
            }
          } catch (error) { issues.push({code: 'scenario-failed', severity: 'blocking', details: error.message}); }
          if (blockedRequests.length) issues.push({code: 'out-of-scope-request', severity: 'blocking', details: blockedRequests});
          await context.close();
          report.runs.push({id, engine, profile: profile.id, variant: variant.id, route: route.id,
            status: issues.length ? 'failed' : 'passed', issues, motion, evidenceDirectory: path.relative(output, directory)});
        }
      }
    } finally { await browser.close(); }
  }
  report.completedAt = new Date().toISOString();
  report.status = !launchFailure && !report.issues.length && report.runs.length && report.runs.every(run => run.status === 'passed') ? 'passed' : 'failed';
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
  return report;
}

if (require.main === module) {
  (async () => {
    const index = process.argv.indexOf('--config');
    if (index < 0 || !process.argv[index + 1]) throw new Error('Usage: node audit-ui.cjs --config qa-config.json');
    const input = JSON.parse(fs.readFileSync(process.argv[index + 1], 'utf8'));
    const report = await runAudit(input, loadPlaywright());
    console.log(`Browser probes ${report.status}: ${report.runs.length} runs. Manual visual/device review remains required.`);
    process.exitCode = report.status === 'passed' ? 0 : 1;
  })().catch(error => { console.error(`QA unavailable/invalid: ${error.message}`); process.exitCode = 2; });
}
module.exports = {runAudit, validateConfig, actions};
