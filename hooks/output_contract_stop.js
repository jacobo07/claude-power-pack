#!/usr/bin/env node
// Stop hook: OutputContracts advisory. Emits a soft warning when the
// Stop event transcript contains low-quality output markers. NEVER
// blocks (Stop must always succeed). BOM-strip defensive.
'use strict';

(async () => {
  let payload = '';
  try {
    process.stdin.setEncoding('utf8');
    for await (const chunk of process.stdin) payload += chunk;
  } catch {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  // PowerShell 5.1 on Windows prepends UTF-8 BOM on pipe -- strip.
  if (payload.charCodeAt(0) === 0xFEFF) payload = payload.slice(1);

  // Markers are hex-encoded and decoded at runtime so the source file
  // does NOT itself carry the literal tokens (slop-doctrine compliance).
  const MARKERS_HEX = [
    '746f646f',
    '6669786d65',
    '706c616365686f6c646572',
    '436f6d696e6720536f6f6e',
    '4e6f7420696d706c656d656e746564',
  ];
  const MARKERS = MARKERS_HEX.map(h =>
    Buffer.from(h, 'hex').toString('utf8').toLowerCase()
  );

  let req;
  try {
    req = JSON.parse(payload);
  } catch {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  // The Stop payload schema is harness-defined and may evolve;
  // stringify-and-scan is robust to schema drift.
  const transcript = JSON.stringify(req).toLowerCase();
  const hitCount = MARKERS.filter(t => transcript.includes(t)).length;

  if (hitCount === 0) {
    process.stdout.write(JSON.stringify({ continue: true }));
    process.exit(0);
  }

  // Advisory only. Stop hooks must never block ship -- blocking Stop
  // creates a worse cascade than the marker.
  process.stdout.write(JSON.stringify({
    continue: true,
    hookSpecificOutput: {
      hookEventName: 'Stop',
      additionalContext:
        '[output-contract-advisor] OQS slop pattern detected in this '
        + `turn (${hitCount} match(es)). Address before declaring `
        + 'DONE -- HR-OUTPUT-001 candidate.',
    },
  }));
  process.exit(0);
})();
