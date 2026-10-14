'use strict';
const fs = require('node:fs');
const path = require('node:path');
const runtime = require('./playwright-runtime.cjs').loadPlaywright();
const {devices} = runtime;
const output = process.argv[2] || path.join(__dirname, '../assets/device-catalog.json');
fs.mkdirSync(path.dirname(path.resolve(output)), {recursive: true});
fs.writeFileSync(output, JSON.stringify({source: 'Playwright deviceDescriptors',
  version: require('./playwright-runtime.cjs').playwrightVersion(), retrieved_on: new Date().toISOString().slice(0, 10),
  note: 'Browser emulation descriptors, not an exhaustive physical-device inventory.', devices}, null, 2) + '\n');
console.log(`Saved ${Object.keys(devices).length} descriptors`);
