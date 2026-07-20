#!/usr/bin/env node
// Stop hook: OutputContracts advisory. Emits a soft warning when the
// Stop event transcript contains low-quality output markers. NEVER
// blocks (Stop must always succeed). BOM-strip defensive.
'use strict';

const fs = require('fs');

// Returns the concatenated text blocks of the most recent assistant turn.
// Fail-open: any read/parse problem yields '' (hook stays silent) rather
// than throwing inside a Stop hook, which must always succeed.
function readLastAssistantText(transcriptPath) {
  if (!transcriptPath || typeof transcriptPath !== 'string') return '';
  let raw;
  try {
    const { size } = fs.statSync(transcriptPath);
    // Bounded tail read -- transcripts grow unbounded over a session.
    const TAIL = 512 * 1024;
    const start = size > TAIL ? size - TAIL : 0;
    const fd = fs.openSync(transcriptPath, 'r');
    try {
      const buf = Buffer.alloc(size - start);
      fs.readSync(fd, buf, 0, buf.length, start);
      raw = buf.toString('utf8');
    } finally {
      fs.closeSync(fd);
    }
  } catch {
    return '';
  }

  // A first line truncated by the tail offset simply fails JSON.parse
  // below and is skipped, so it needs no special handling.
  const lines = raw.split('\n');
  const out = [];
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim();
    if (!line) continue;
    let rec;
    try { rec = JSON.parse(line); } catch { continue; }
    // Walking back, stop at the user message that opened this turn.
    if (rec.type === 'user') break;
    if (rec.type !== 'assistant') continue;
    const content = rec.message && rec.message.content;
    if (!Array.isArray(content)) continue;
    for (const block of content) {
      if (block && block.type === 'text' && typeof block.text === 'string') {
        out.push(block.text);
      }
    }
  }
  return out.join('\n');
}

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

  // The Stop payload carries transcript_path (a path), never the turn's
  // prose -- scanning the payload itself matches nothing the harness ever
  // sends. Read the transcript and scan the last assistant turn's text.
  const transcript = readLastAssistantText(req.transcript_path).toLowerCase();
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
