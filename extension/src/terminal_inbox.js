"use strict";
// Pure, vscode-free decision for the terminal inbox: may THIS window type a line
// into one of ITS terminals for a given Claude Code session, right now?
//
// WHY: the auto-compact / long-run resume must type `/gsd-autonomous --from X`
// into the session's own terminal. SendKeys only reaches the FOREGROUND window,
// and CONIN$ injection is not read by claude.exe under ConPTY. terminal.sendText
// from inside the owning window's extension host reaches the pty with no focus
// change -- so the requester (auto-compact-sendkeys-daemon.ps1) writes a request
// to ~/.claude/state/terminal-inbox/<sid>.json and the owning window acts on it.
//
// Typing into the wrong terminal submits a command in someone else's session, so
// every rule here refuses rather than guesses:
//   - ownership: exactly one of this window's terminals has a shell processId in
//     the request's ancestor chain of claude.exe (pids are unique machine-wide);
//   - identity: ~/.claude/sessions/<pid>.json names the same session, and its
//     procStart agrees with the requester's reading to within 1 microsecond
//     (CIM loses the last FILETIME digit; a reused pid differs by far more);
//   - readiness: status is exactly "idle". "waiting" is an open dialog
//     (measured 2026-09-18: AskUserQuestion), where Enter would pick an option;
//     "busy" is mid-turn. Both DEFER until the request expires;
//   - text: one printable line.
//
// No vscode dependency -> unit-testable under plain node (mirrors
// terminal_registry.js). Self-test: `node terminal_inbox.js --selftest`.

const DEFAULT_TTL_MS = 60000;
const PROC_START_TOLERANCE = 10n; // FILETIME units of 100 ns -> 1 microsecond

function toBig(v) {
  try {
    const s = String(v == null ? "" : v).trim();
    return /^\d+$/.test(s) ? BigInt(s) : null;
  } catch (_e) {
    return null;
  }
}

function sameProcStart(a, b) {
  const x = toBig(a);
  const y = toBig(b);
  if (x === null || y === null) return false;
  const d = x > y ? x - y : y - x;
  return d < PROC_START_TOLERANCE;
}

function validText(text) {
  // One printable line: no CR/LF/other control characters, bounded length.
  return typeof text === "string" && text.length > 0 && text.length <= 512 &&
    ![...text].some((ch) => ch.charCodeAt(0) < 32 || ch.charCodeAt(0) === 127);
}

// terminals: [{ processId }] in this window. Returns the matching indices.
function ownedTerminals(terminals, ancestors) {
  const set = new Set((Array.isArray(ancestors) ? ancestors : []).filter(Number.isFinite));
  const out = [];
  (Array.isArray(terminals) ? terminals : []).forEach((t, i) => {
    if (t && Number.isFinite(t.processId) && set.has(t.processId)) out.push(i);
  });
  return out;
}

// Returns one of:
//   { action: "ignore", reason }            -- not this window's request
//   { action: "defer",  reason }            -- ours, not yet safe; ask again later
//   { action: "refuse", reason }            -- ours, and it must never be sent
//   { action: "send",   terminalIndex }     -- ours and safe now
function decide(req, terminals, session, nowMs) {
  if (!req || typeof req !== "object") return { action: "ignore", reason: "no-request" };
  const owned = ownedTerminals(terminals, req.ancestors);
  if (owned.length === 0) return { action: "ignore", reason: "not-this-window" };
  if (owned.length > 1) return { action: "refuse", reason: "ambiguous-terminal" };

  const ttl = Number.isFinite(req.ttl_ms) ? req.ttl_ms : DEFAULT_TTL_MS;
  if (!Number.isFinite(req.created_ms) || nowMs - req.created_ms > ttl) {
    // A refusal needs its OWN words. Plain "expired" reads as "no window was
    // listening", and that reading cost a real diagnosis: on 2026-09-20 a live
    // crossing was ledgered `terminal inbox refused: expired` seven minutes
    // after it was made -- while THIS window owned it and was deferring it on
    // the clause below, because the session was mid-turn the entire time.
    //
    // The two clauses contradict each other: the deferral says "ask again
    // later", this one says "you asked too long", and the TTL keeps running
    // during the deferral. On a busy autonomous run the deadline always wins,
    // so the transport is structurally unable to deliver to exactly the class
    // of session it exists for. Widening the TTL is NOT the fix -- it is a
    // staleness guard on a line about to be typed into a live terminal.
    //
    // Behaviour here is deliberately unchanged: still a refusal, still fail
    // closed, still nothing typed. Only the word changes, and the word is the
    // whole diagnostic value -- it separates "nobody owned this" from "its
    // owner was busy throughout", which need opposite fixes.
    //
    // The identity conjunction below is derived from the same three
    // comparisons the identity block makes; it is NOT collapsed into them
    // because that block returns a distinct reason per failure, and those
    // reasons are load-bearing. Keep the two in step.
    const identified = !!session && typeof session === "object" &&
      session.sessionId === req.session_id && session.pid === req.claude_pid &&
      sameProcStart(session.procStart, req.proc_start);
    if (identified && session.status !== "idle") {
      return { action: "refuse", reason: "expired-while-deferred:" + String(session.status) };
    }
    return { action: "refuse", reason: "expired" };
  }
  if (!validText(req.text)) return { action: "refuse", reason: "invalid-text" };

  if (!session || typeof session !== "object") return { action: "refuse", reason: "session-unreadable" };
  if (session.sessionId !== req.session_id) return { action: "refuse", reason: "session-mismatch" };
  if (session.pid !== req.claude_pid) return { action: "refuse", reason: "pid-mismatch" };
  if (!sameProcStart(session.procStart, req.proc_start)) return { action: "refuse", reason: "proc-start-mismatch" };

  if (session.status !== "idle") return { action: "defer", reason: "status-" + String(session.status) };
  return { action: "send", terminalIndex: owned[0] };
}

module.exports = { decide, ownedTerminals, sameProcStart, validText, DEFAULT_TTL_MS };

if (require.main === module && process.argv.includes("--selftest")) {
  const assert = require("assert");
  let ok = 0;
  function check(name, fn) {
    try {
      fn();
      ok++;
      console.log("  OK   " + name);
    } catch (e) {
      console.log("  FAIL " + name + ": " + (e && e.message));
      process.exitCode = 1;
    }
  }

  const now = 1789740000000;
  const req = {
    id: "r1", session_id: "fa6961b6-aaaa", text: "/gsd-autonomous --from 10.1",
    claude_pid: 42912, proc_start: "134342068323963480",
    ancestors: [42912, 12488, 54952, 60280, 61988], created_ms: now - 1000, ttl_ms: 60000,
  };
  const terms = [{ processId: 111 }, { processId: 54952 }, { processId: 222 }];
  const sess = { sessionId: "fa6961b6-aaaa", pid: 42912, procStart: "134342068323963483", status: "idle" };

  check("V-INBOX-SEND-OWNED", () =>
    assert.deepStrictEqual(decide(req, terms, sess, now), { action: "send", terminalIndex: 1 }));
  check("V-INBOX-OTHER-WINDOW-IGNORES", () =>
    assert.strictEqual(decide(req, [{ processId: 111 }], sess, now).action, "ignore"));
  check("V-INBOX-NO-PID-IGNORES", () =>
    assert.strictEqual(decide(req, [{ processId: null }, {}], sess, now).action, "ignore"));
  check("V-INBOX-AMBIGUOUS-REFUSES", () =>
    assert.strictEqual(decide(req, [{ processId: 54952 }, { processId: 60280 }], sess, now).reason,
      "ambiguous-terminal"));
  check("V-INBOX-WAITING-DEFERS", () =>
    assert.deepStrictEqual(decide(req, terms, { ...sess, status: "waiting" }, now),
      { action: "defer", reason: "status-waiting" }));
  check("V-INBOX-BUSY-DEFERS", () =>
    assert.strictEqual(decide(req, terms, { ...sess, status: "busy" }, now).action, "defer"));
  check("V-INBOX-EXPIRED-REFUSES", () =>
    assert.strictEqual(decide({ ...req, created_ms: now - 61000 }, terms, sess, now).reason, "expired"));
  // The 2026-09-20 crossing, in its exact shape: owned by this window, deferred
  // for the whole TTL because the session was mid-turn, then refused. It must
  // NOT read as "nobody was listening" -- that word sent two investigations at
  // the delivery path when the cause was the deadline racing the deferral.
  check("V-INBOX-EXPIRED-WHILE-BUSY-SAYS-SO", () =>
    assert.strictEqual(
      decide({ ...req, created_ms: now - 61000 }, terms, { ...sess, status: "busy" }, now).reason,
      "expired-while-deferred:busy"));
  check("V-INBOX-EXPIRED-WHILE-WAITING-SAYS-SO", () =>
    assert.strictEqual(
      decide({ ...req, created_ms: now - 61000 }, terms, { ...sess, status: "waiting" }, now).reason,
      "expired-while-deferred:waiting"));
  // Green controls: the new word must not swallow the plain case. An expired
  // request whose session is idle, or whose session cannot be identified, is
  // still a bare "expired" -- otherwise the split reports everything as busy
  // and is indistinguishable from a predicate that always fires.
  check("V-INBOX-EXPIRED-IDLE-STAYS-PLAIN", () =>
    assert.strictEqual(decide({ ...req, created_ms: now - 61000 }, terms, sess, now).reason, "expired"));
  check("V-INBOX-EXPIRED-UNIDENTIFIED-STAYS-PLAIN", () =>
    assert.strictEqual(
      decide({ ...req, created_ms: now - 61000 }, terms, { ...sess, status: "busy", sessionId: "other" },
        now).reason, "expired"));
  // Still a refusal. Nothing may be typed on any of these paths.
  check("V-INBOX-EXPIRED-NEVER-SENDS", () =>
    assert.ok(["busy", "waiting", "idle"].every((s) =>
      decide({ ...req, created_ms: now - 61000 }, terms, { ...sess, status: s }, now).action === "refuse")));
  check("V-INBOX-REUSED-PID-REFUSES", () =>
    assert.strictEqual(decide(req, terms, { ...sess, procStart: "134342068323999999" }, now).reason,
      "proc-start-mismatch"));
  check("V-INBOX-OTHER-SESSION-REFUSES", () =>
    assert.strictEqual(decide(req, terms, { ...sess, sessionId: "other" }, now).reason, "session-mismatch"));
  check("V-INBOX-NO-SESSION-REFUSES", () =>
    assert.strictEqual(decide(req, terms, null, now).reason, "session-unreadable"));
  check("V-INBOX-MULTILINE-REFUSES", () =>
    assert.strictEqual(decide({ ...req, text: "a\rb" }, terms, sess, now).reason, "invalid-text"));
  check("V-INBOX-PROCSTART-TOLERANCE", () => {
    assert.ok(sameProcStart("134342018799119214", "134342018799119210"));
    assert.ok(!sameProcStart("134342018799119214", "134342018799119199"));
    assert.ok(!sameProcStart("", "1"));
  });

  if (process.exitCode === 1) {
    console.log("TERMINAL_INBOX_SELFTEST=FAIL");
  } else {
    console.log("TERMINAL_INBOX_SELFTEST=PASS ok=" + ok);
  }
}
