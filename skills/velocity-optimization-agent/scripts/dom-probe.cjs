'use strict';

/** Runs inside the page. No application state is changed by this probe. */
function inspectDOM(contracts = {}) {
  const issues = [];
  const records = [];
  const rect = element => {
    const r = element.getBoundingClientRect();
    return {x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom};
  };
  const shown = element => {
    if (element.checkVisibility) {
      return element.checkVisibility({checkOpacity: true, checkVisibilityCSS: true});
    }
    const style = getComputedStyle(element);
    const r = rect(element);
    return r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0;
  };
  const describe = element => element.id ? `#${element.id}` : `${element.tagName.toLowerCase()}${element.className && typeof element.className === 'string' ? '.' + element.className.trim().split(/\s+/).join('.') : ''}`;
  const issue = (code, selector, details, severity = 'major') => issues.push({code, selector, details, severity});
  const root = document.documentElement;
  if (root.scrollWidth > innerWidth + 2) {
    const suspects = [...document.querySelectorAll('body *')].filter(shown)
      .filter(element => { const r = rect(element); return r.right > innerWidth + 2 || r.x < -2; })
      .slice(0, 20).map(describe);
    issue('horizontal-overflow', 'html', {viewport: innerWidth, scrollWidth: root.scrollWidth, suspects});
  }

  for (const contract of contracts.controls || []) {
    const elements = [...document.querySelectorAll(contract.selector)];
    if (!elements.length && contract.required !== false) issue('missing-control', contract.selector, {});
    for (const element of elements) {
      const r = rect(element);
      if (!shown(element)) {
        if (contract.required !== false) issue('hidden-control', contract.selector, {rect: r});
        continue;
      }
      if (contract.inViewport && (r.x < -1 || r.y < -1 || r.right > innerWidth + 1 || r.bottom > innerHeight + 1)) {
        issue('control-outside-viewport', contract.selector, {rect: r, viewport: {width: innerWidth, height: innerHeight}});
      }
      const inViewport = r.right > 0 && r.bottom > 0 && r.x < innerWidth && r.y < innerHeight;
      if (inViewport) {
        const points = [[.5, .5], [.15, .15], [.85, .15], [.15, .85], [.85, .85]];
        const blocked = [];
        for (const [px, py] of points) {
          const x = r.x + r.width * px, y = r.y + r.height * py;
          // Browser hit testing rounds fractional points at the final pixel.
          // A point inside the layout viewport can therefore be outside the
          // hittable viewport. Reachability is tested again after scrolling.
          const hitWidth = Math.min(innerWidth, document.documentElement.clientWidth);
          const hitHeight = Math.min(innerHeight, document.documentElement.clientHeight);
          if (x < 1 || y < 1 || x > hitWidth - 1 || y > hitHeight - 1) continue;
          const top = document.elementFromPoint(x, y);
          if (!top || !(top === element || element.contains(top))) blocked.push({x, y, by: top ? describe(top) : null});
        }
        if (blocked.length && contract.allowOcclusion !== true) issue('occluded-control', contract.selector, {blocked});
      }
      for (let parent = element.parentElement; parent && parent !== document.body; parent = parent.parentElement) {
        const style = getComputedStyle(parent), bounds = rect(parent);
        const clipsX = /hidden|clip/.test(style.overflowX);
        const clipsY = /hidden|clip/.test(style.overflowY);
        if ((clipsX && (r.x < bounds.x - 1 || r.right > bounds.right + 1)) ||
            (clipsY && (r.y < bounds.y - 1 || r.bottom > bounds.bottom + 1))) {
          issue('clipped-control', contract.selector, {ancestor: describe(parent), rect: r, bounds});
          break;
        }
      }
      if (contract.minTargetSize && (r.width < contract.minTargetSize || r.height < contract.minTargetSize)) {
        issue('small-target', contract.selector, {rect: r, minimum: contract.minTargetSize});
      }
      records.push({selector: contract.selector, rect: r});
    }
  }

  for (const contract of contracts.styles || []) {
    const elements = [...document.querySelectorAll(contract.selector)];
    if (!elements.length) issue('missing-style-target', contract.selector, {});
    for (const element of elements) {
      const style = getComputedStyle(element);
      for (const [property, expected] of Object.entries(contract.properties || {})) {
        const actual = style.getPropertyValue(property).trim();
        const values = Array.isArray(expected) ? expected : [expected];
        if (!values.includes(actual)) issue('style-override', contract.selector, {property, expected, actual});
      }
    }
  }

  for (const contract of contracts.alignment || []) {
    if (contract.minWidth && innerWidth < contract.minWidth) continue;
    if (contract.maxWidth && innerWidth > contract.maxWidth) continue;
    const element = document.querySelector(contract.selector), reference = document.querySelector(contract.reference);
    if (!element || !reference) { issue('missing-alignment-target', contract.selector, {reference: contract.reference}); continue; }
    const a = rect(element), b = rect(reference);
    const differences = {
      'center-x': Math.abs(a.x + a.width / 2 - b.x - b.width / 2),
      'center-y': Math.abs(a.y + a.height / 2 - b.y - b.height / 2),
      left: Math.abs(a.x - b.x), right: Math.abs(a.right - b.right),
    };
    if (!(contract.mode in differences)) { issue('invalid-alignment-mode', contract.selector, {mode: contract.mode}); continue; }
    const tolerance = contract.tolerancePx ?? 2;
    if (differences[contract.mode] > tolerance) issue('alignment-drift', contract.selector, {mode: contract.mode, delta: differences[contract.mode], tolerance});
  }
  return {issues, records, viewport: {width: innerWidth, height: innerHeight}, scroll: {x: scrollX, y: scrollY}};
}

/** Install before navigation to observe the page's own work. */
function installTelemetry() {
  const store = {longTasks: [], longFrames: [], shifts: [], supported: {}};
  globalThis.__kinesisTelemetry = store;
  for (const [type, target] of [['longtask', 'longTasks'], ['long-animation-frame', 'longFrames'], ['layout-shift', 'shifts']]) {
    store.supported[type] = PerformanceObserver.supportedEntryTypes.includes(type);
    if (!store.supported[type]) continue;
    new PerformanceObserver(list => {
      for (const entry of list.getEntries()) {
        if (store[target].length >= 5000) continue;
        store[target].push({startTime: entry.startTime, duration: entry.duration, value: entry.value || 0, hadRecentInput: Boolean(entry.hadRecentInput)});
      }
    }).observe({type, buffered: true});
  }
}

async function sampleMotion({selectors, durationMs}) {
  const frames = [];
  const started = performance.now();
  const nodes = selectors.map(selector => ({selector, node: document.querySelector(selector)}));
  await new Promise(resolve => {
    const sample = now => {
      frames.push({time: now, subjects: nodes.map(({selector, node}) => {
        if (!node || !node.isConnected) return {selector, missing: true};
        const r = node.getBoundingClientRect(), style = getComputedStyle(node);
        return {selector, x: r.x, y: r.y, width: r.width, height: r.height, opacity: Number(style.opacity), transform: style.transform};
      })});
      if (now - started >= durationMs) resolve(); else requestAnimationFrame(sample);
    };
    requestAnimationFrame(sample);
  });
  const telemetry = globalThis.__kinesisTelemetry || {};
  return {frames, telemetry, durationMs: performance.now() - started};
}

module.exports = {inspectDOM, installTelemetry, sampleMotion};
