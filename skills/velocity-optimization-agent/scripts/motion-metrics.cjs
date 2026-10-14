'use strict';

function percentile(values, fraction) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(sorted.length * fraction) - 1)];
}

function analyzeMotion(sample, contracts = [], budgets = {}) {
  const issues = [];
  const frames = sample.frames || [];
  const intervals = frames.slice(1).map((frame, i) => frame.time - frames[i].time);
  const statistics = {sampleFrames: frames.length, frameP50Ms: percentile(intervals, .5),
    frameP95Ms: percentile(intervals, .95), maxFrameMs: intervals.length ? Math.max(...intervals) : null,
    delayedFrames: intervals.filter(ms => ms > (budgets.delayedFrameMs ?? 34)).length};
  const add = (code, selector, details) => issues.push({code, selector, details, severity: 'major'});
  if (frames.length < 3) add('insufficient-motion-samples', null, {frames: frames.length});
  if (budgets.maxFrameMs != null && statistics.maxFrameMs > budgets.maxFrameMs) add('frame-stall', null, statistics);
  if (budgets.p95FrameMs != null && statistics.frameP95Ms > budgets.p95FrameMs) add('frame-budget', null, statistics);
  for (const contract of contracts) {
    const samples = frames.map(frame => frame.subjects.find(subject => subject.selector === contract.selector));
    if (samples.some(subject => !subject || subject.missing)) { add('missing-motion-subject', contract.selector, {}); continue; }
    if (!samples.length) continue;
    const first = samples[0], last = samples.at(-1);
    let maxStep = 0, reversals = 0;
    const axis = contract.axis || 'x';
    for (let i = 1; i < samples.length; i++) {
      const dx = samples[i].x - samples[i - 1].x, dy = samples[i].y - samples[i - 1].y;
      maxStep = Math.max(maxStep, Math.hypot(dx, dy));
      const delta = samples[i][axis] - samples[i - 1][axis];
      if ((contract.direction === 'increasing' && delta < -(contract.directionTolerancePx ?? .5)) ||
          (contract.direction === 'decreasing' && delta > (contract.directionTolerancePx ?? .5))) reversals++;
    }
    if (contract.maxStepPx != null && maxStep > contract.maxStepPx) add('motion-discontinuity', contract.selector, {maxStepPx: maxStep, limit: contract.maxStepPx});
    if (reversals) add('unexpected-motion-reversal', contract.selector, {reversals, direction: contract.direction});
    const distance = Math.max(...samples.map(subject => Math.abs(subject[axis] - first[axis])));
    if (contract.minTravelPx != null && distance < contract.minTravelPx) add('missing-expected-motion', contract.selector, {distance, minimum: contract.minTravelPx});
    if (contract.maxTravelPx != null && distance > contract.maxTravelPx) add('motion-travel-exceeded', contract.selector, {distance, maximum: contract.maxTravelPx});
    if (contract.finalPosition != null && Math.abs(last[axis] - contract.finalPosition) > (contract.endpointTolerancePx ?? 2)) add('motion-endpoint-mismatch', contract.selector, {actual: last[axis], expected: contract.finalPosition});
    if (contract.finalOpacity != null && Math.abs(last.opacity - contract.finalOpacity) > (contract.opacityTolerance ?? .02)) add('motion-opacity-endpoint', contract.selector, {actual: last.opacity, expected: contract.finalOpacity});
    if (contract.restTolerancePx != null) {
      const tail = samples.slice(-Math.max(3, Math.floor(samples.length * .15)));
      const spread = Math.max(...tail.map(s => s[axis])) - Math.min(...tail.map(s => s[axis]));
      if (spread > contract.restTolerancePx) add('motion-not-settled', contract.selector, {spread, tolerance: contract.restTolerancePx});
    }
  }
  const telemetry = sample.telemetry || {};
  const cls = (telemetry.shifts || []).filter(entry => !entry.hadRecentInput).reduce((sum, entry) => sum + entry.value, 0);
  statistics.observedLayoutShiftSum = cls; // Not the official maximum session-window CLS metric.
  if (budgets.maxLayoutShiftSum != null && cls > budgets.maxLayoutShiftSum) add('unexpected-layout-shift', null, {sum: cls, maximum: budgets.maxLayoutShiftSum});
  if (budgets.maxLongTaskMs != null && telemetry.supported?.longtask) {
    const maximum = Math.max(0, ...(telemetry.longTasks || []).map(entry => entry.duration));
    if (maximum > budgets.maxLongTaskMs) add('long-task-budget', null, {maximum, limit: budgets.maxLongTaskMs});
  }
  return {statistics, issues, supportedObservers: telemetry.supported || {}};
}

module.exports = {percentile, analyzeMotion};
