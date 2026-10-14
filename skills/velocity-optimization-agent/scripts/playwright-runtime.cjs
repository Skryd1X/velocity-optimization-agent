'use strict';
const {createRequire} = require('node:module');
const path = require('node:path');

/** Resolve reviewed tooling from the skill/package or the invoking project. */
function loadPlaywright() {
  try { return require('playwright'); } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  const fromProject = createRequire(path.join(process.cwd(), 'package.json'));
  try { return fromProject('playwright'); } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  throw new Error('Playwright is unavailable. Use a reviewed local installation in the package or invoking project; no tools were installed automatically.');
}
function playwrightVersion() {
  try { return require('playwright/package.json').version; } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  return createRequire(path.join(process.cwd(), 'package.json'))('playwright/package.json').version;
}
module.exports = {loadPlaywright, playwrightVersion};
