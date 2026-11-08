'use strict';
/**
 * recovery_fastpath.js -- decides whether the SessionStart recovery gate
 * (tools/recovery_epoch_gate.py) needs to run at all, or whether its answer is already
 * on disk. Plan pillar-k-resident-prefix C3, audit gap 6.
 *
 * WHY. Measured over 7 days: hub time up to the recovery line p50 967 / p90 1,550 ms vs
 * p50 125 ms after it -- the python spawn is most of the hub's critical path, and it ran
 * on every session start to reprint the same verdict. A hash of the gate's input FILES
 * cannot key a cache (power_beacon.json is rewritten on every SessionStart), so this
 * mirrors the gate's own decisions instead, on the same facts:
 *
 *   (a) epoch.detect_interruption opens an epoch only when the beacon is not graceful AND
 *       the machine booted after the beacon's ts. Whenever that could be true -> RUN.
 *       (The gate is never passed --live-terminals by the hub, so boot is the only signal.)
 *   (b) while an epoch is OPEN, banner() re-judges it from the pinned reference (fixed for
 *       the epoch) and the bytes of pane_map.json. When those bytes hash to the
 *       judged_input_sha the gate stored at its last judgement, the verdict cannot have
 *       changed -> SKIP and print the reminder_line the gate itself stored (one formatter).
 *   Otherwise the gate would print nothing and write nothing -> SKIP, silent.
 *
 * Every doubt resolves to RUN: an unreadable file, an unparseable timestamp, a missing
 * hash. Running the gate costs time; skipping it wrongly would hide an interruption.
 * Loading this module does nothing (no timers, no stdin, no spawns, no writes).
 * Kill switch: CPP_RECOVERY_FASTPATH=off -> always run the gate.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

// os.uptime() and GetTickCount64 agree to well under a second; the margin absorbs that
// and clock jitter, always in the direction of running the gate.
const BOOT_MARGIN_MS = 120 * 1000;

function readJson(fp) {
  let raw;
  try {
    raw = fs.readFileSync(fp, 'utf8');
  } catch (err) {
    return (err && err.code === 'ENOENT') ? { ok: true, value: null } : { ok: false };
  }
  try {
    return { ok: true, value: JSON.parse(raw.replace(/^﻿/, '')) };
  } catch (_) {
    return { ok: false };
  }
}

// Python's parse_iso treats a naive timestamp as UTC; Date.parse would read it as local.
function parseIsoUtc(s) {
  if (typeof s !== 'string' || !s) return NaN;
  const hasZone = /(Z|[+-]\d\d:?\d\d)$/i.test(s.trim());
  return Date.parse(hasZone ? s : s + 'Z');
}

function recoveryFastPath(stateDir, opts) {
  const o = opts || {};
  const sw = String(process.env.CPP_RECOVERY_FASTPATH || '').trim().toLowerCase();
  if (sw === 'off' || sw === '0' || sw === 'false') return { run: true, why: 'kill switch' };
  const now = (typeof o.nowMs === 'number') ? o.nowMs : Date.now();
  const uptimeMs = (typeof o.uptimeMs === 'number') ? o.uptimeMs : os.uptime() * 1000;

  const b = readJson(path.join(stateDir, 'power_beacon.json'));
  if (!b.ok) return { run: true, why: 'beacon unreadable' };
  const beacon = b.value;
  if (beacon && beacon.kind !== 'graceful') {
    const bts = parseIsoUtc(beacon.ts);
    if (Number.isNaN(bts)) return { run: true, why: 'beacon ts unparseable' };
    if (now - uptimeMs > bts - BOOT_MARGIN_MS) {
      return { run: true, why: 'booted after a non-graceful beacon (possible interruption)' };
    }
  }

  const e = readJson(path.join(stateDir, 'recovery_epoch.json'));
  if (!e.ok) return { run: true, why: 'epoch unreadable' };
  const ep = e.value;
  if (!ep || ep.status !== 'open') return { run: false, line: null, why: 'no open epoch' };
  if (!ep.judged_input_sha || typeof ep.reminder_line !== 'string' || !ep.reminder_line || !ep.announced_at) {
    return { run: true, why: 'open epoch not yet judged with an input hash' };
  }
  let bytes;
  try {
    bytes = fs.readFileSync(path.join(stateDir, 'pane_map.json'));
  } catch (_) {
    return { run: true, why: 'pane_map unreadable' };
  }
  const sha = crypto.createHash('sha256').update(bytes).digest('hex');
  if (sha !== ep.judged_input_sha) return { run: true, why: 'pane_map changed since the last judgement' };
  return { run: false, line: ep.reminder_line, why: 'open epoch, pane_map unchanged since judged' };
}

module.exports = { recoveryFastPath, parseIsoUtc, BOOT_MARGIN_MS };
