'use strict';
const fs = require('node:fs');
const path = require('node:path');

const generic = [
  [320, 568], [360, 640], [375, 667], [390, 844], [412, 915], [430, 932],
  [540, 720], [600, 800], [768, 1024], [820, 1180], [912, 1368], [1024, 768],
  [1280, 720], [1366, 768], [1440, 900], [1536, 864], [1920, 1080],
  [2560, 1440], [3440, 1440], [3840, 2160], [1280, 500], [1920, 600],
];

function makeProfiles({tier = 'standard', breakpoints = [], devices = {}, sweep = false} = {}) {
  if (!['quick', 'standard', 'full'].includes(tier)) throw new Error('Unknown profile tier');
  const profiles = [];
  const add = (id, viewport, extra = {}) => profiles.push({id, viewport, ...extra});
  const sizes = tier === 'quick' ? [[320, 568], [390, 844], [768, 1024], [1440, 900], [1920, 1080]] : generic;
  for (const [width, height] of sizes) {
    add(`viewport-${width}x${height}`, {width, height}, {deviceScaleFactor: 1});
    if (tier !== 'quick' && width <= 1024) add(`landscape-${height}x${width}`, {width: height, height: width}, {hasTouch: true});
  }
  const selected = tier === 'full' ? Object.keys(devices) : ['iPhone 13', 'Pixel 7', 'iPad Pro 11'];
  if (tier !== 'quick') for (const name of selected) {
    if (!devices[name]) continue;
    const descriptor = devices[name];
    const {defaultBrowserType, ...options} = descriptor;
    add(`device-${name.replace(/[^a-zA-Z0-9]+/g, '-').toLowerCase()}`, options.viewport,
      {...options, deviceName: name, preferredBrowser: defaultBrowserType});
  }
  for (const point of breakpoints) {
    if (!Number.isInteger(point) || point < 100 || point > 10000) throw new Error('Breakpoints must be integer CSS widths between 100 and 10000');
    for (const delta of [-1, 0, 1]) add(`breakpoint-${point}-${delta === -1 ? 'below' : delta === 1 ? 'above' : 'exact'}`, {width: point + delta, height: 900});
  }
  if (sweep || tier === 'full') {
    for (let width = 240; width <= 3840; width += 73) add(`sweep-${width}`, {width, height: width < 600 ? 844 : 900});
  }
  return profiles;
}

if (require.main === module) {
  const args = process.argv.slice(2);
  const get = (flag, fallback) => { const i = args.indexOf(flag); return i === -1 ? fallback : args[i + 1]; };
  let devices;
  try { devices = require('./playwright-runtime.cjs').loadPlaywright().devices; }
  catch { devices = JSON.parse(fs.readFileSync(path.join(__dirname, '../assets/device-catalog.json'), 'utf8')).devices; }
  const profiles = makeProfiles({tier: get('--tier', 'standard'), breakpoints: get('--breakpoints', '').split(',').filter(Boolean).map(Number), devices, sweep: args.includes('--sweep')});
  const result = JSON.stringify({schema_version: 1, profiles}, null, 2);
  const output = get('--output', null);
  if (output) fs.writeFileSync(output, result + '\n'); else console.log(result);
}
module.exports = {makeProfiles};
