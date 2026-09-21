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

// The argument tail of a staged `/compact`, or "" for everything else.
//
// WHY THIS LIVES HERE AND NOT IN extension.js: it was born inline in the
// delivery block (f771f55), and extension.js requires vscode, so no gate could
// reach it -- the rule rested on one Owner observation of one pane. This module
// is already vscode-free, already exported, already driven by
// tools/test_terminal_inbox.py, so moving the predicate is the whole mechanism.
// extension.js CALLS this; it must never carry a second copy, because two
// copies of one rule drift and only one of them is tested.
//
// Scoped to /compact deliberately. The second Enter (2026-09-20) was free -- a
// no-op when the line had already submitted. This tail is NOT: if the command
// line submitted by itself, the tail lands in the fresh post-compaction prompt
// as a stray user message (measured 2026-09-21, 18:24 crossing). A wasted turn,
// visible, not destructive -- and a cost only /compact is known to need, so
// /gsd-autonomous and /cpp-gsd-long must take the empty branch untouched.
const COMPACT_WITH_ARGS = /^\/compact\s+/;

function argumentTail(text) {
  if (typeof text !== "string") return "";
  // Anchored: a /compact appearing anywhere but the start is prose, not a
  // command, and `\s+` is what separates `/compact x` from `/compaction x`.
  if (!COMPACT_WITH_ARGS.test(text)) return "";
  return text.replace(COMPACT_WITH_ARGS, "").trim();
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

// A request its owner is actively holding is not a stale request. DEFAULT_TTL_MS
// guards staleness of a line NOBODY has taken up; this bounds how long the owner
// may hold one while the session is mid-turn. Two different facts, so two clocks
// -- one clock serving both is what made a busy autonomous run structurally
// undeliverable (2026-09-20: owned, deferred 7 minutes, then "expired"). Twenty
// minutes covers the long turns measured on this host (a 26-minute subagent ran
// the day this was written) without letting a hung session wait forever. The
// requester may override per request with `max_defer_ms`.
const DEFAULT_MAX_DEFER_MS = 1200000;

// Returns one of:
//   { action: "ignore", reason }            -- not this window's request
//   { action: "defer",  reason }            -- ours, not yet safe; ask again later
//   { action: "refuse", reason }            -- ours, and it must never be sent
//   { action: "send",   terminalIndex }     -- ours and safe now
//
// `deferredSinceMs` is when THIS window first deferred this identified request.
// Omitted/undefined reproduces the pre-2026-09-21 behaviour exactly, so every
// existing caller is byte-unchanged until it opts in.
function decide(req, terminals, session, nowMs, deferredSinceMs) {
  if (!req || typeof req !== "object") return { action: "ignore", reason: "no-request" };
  const owned = ownedTerminals(terminals, req.ancestors);
  if (owned.length === 0) return { action: "ignore", reason: "not-this-window" };
  if (owned.length > 1) return { action: "refuse", reason: "ambiguous-terminal" };

  // Hoisted: both the staleness branch and the deferral bound need it, and
  // deriving it twice is how two copies of one rule drift apart. It is NOT
  // collapsed into the identity block below, because that block returns a
  // distinct reason per failure and those reasons are load-bearing.
  const identified = !!session && typeof session === "object" &&
    session.sessionId === req.session_id && session.pid === req.claude_pid &&
    sameProcStart(session.procStart, req.proc_start);

  const ttl = Number.isFinite(req.ttl_ms) ? req.ttl_ms : DEFAULT_TTL_MS;
  const maxDefer = Number.isFinite(req.max_defer_ms) ? req.max_defer_ms : DEFAULT_MAX_DEFER_MS;
  // Time this window has been holding the request is excluded from its age: the
  // TTL measures how long a line went UNCLAIMED, not how long its rightful owner
  // was busy. Bounded separately below so "paused" can never mean "forever".
  const deferredFor = (Number.isFinite(deferredSinceMs) && deferredSinceMs > 0 &&
    nowMs > deferredSinceMs) ? nowMs - deferredSinceMs : 0;

  if (!Number.isFinite(req.created_ms)) return { action: "refuse", reason: "expired" };
  if (deferredFor > maxDefer) {
    // The bound, and it is the dominant fact when it fires: this window held the
    // request as long as it is allowed to. Distinct from every other refusal,
    // because the fix is "the session never went idle", not "delivery broke".
    return { action: "refuse",
             reason: "deferred-too-long:" + String(identified ? session.status : "unidentified") };
  }
  if (nowMs - req.created_ms - deferredFor > ttl) {
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

module.exports = { decide, ownedTerminals, sameProcStart, validText, argumentTail,
  DEFAULT_TTL_MS, DEFAULT_MAX_DEFER_MS };

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

  // --- the deferral clock (2026-09-21) ---------------------------------------
  // The 2026-09-20 crossing in its exact shape, now delivered instead of lost:
  // created 10 minutes ago against a 60 s TTL, held by this window for almost
  // all of it because the session was mid-turn, and idle at the moment we ask.
  // Under the old single clock this refused as "expired" and the run stopped.
  const oldReq = { ...req, created_ms: now - 600000 };
  check("V-INBOX-DEFERRAL-PAUSES-THE-CLOCK", () =>
    assert.deepStrictEqual(decide(oldReq, terms, sess, now, now - 599000),
      { action: "send", terminalIndex: 1 }));
  // The bound: "paused" must never mean "forever".
  check("V-INBOX-DEFERRAL-IS-BOUNDED", () =>
    assert.strictEqual(
      decide(oldReq, terms, { ...sess, status: "busy" }, now, now - 1200001).reason,
      "deferred-too-long:busy"));
  check("V-INBOX-DEFERRAL-BOUND-IS-OVERRIDABLE", () =>
    assert.strictEqual(
      decide({ ...oldReq, max_defer_ms: 1000 }, terms, { ...sess, status: "busy" }, now,
        now - 5000).reason, "deferred-too-long:busy"));
  // Green control, and the one that matters most: WITHOUT a deferral stamp the
  // old behaviour is byte-identical, so no existing caller changed meaning.
  check("V-INBOX-NO-DEFERRAL-STAMP-IS-UNCHANGED", () =>
    assert.strictEqual(decide(oldReq, terms, sess, now).reason, "expired"));
  // A stamp from the future, or a nonsense one, must not extend anything.
  check("V-INBOX-BOGUS-DEFERRAL-STAMP-IGNORED", () =>
    assert.ok([now + 60000, -1, 0, NaN, null, undefined, "x"].every((v) =>
      decide(oldReq, terms, sess, now, v).reason === "expired")));
  // The pause moves the deadline; it does not remove it. Deferred the whole
  // time but still older than TTL + deferral -> refused, not sent.
  check("V-INBOX-PAUSE-STILL-EXPIRES", () =>
    assert.strictEqual(
      decide({ ...req, created_ms: now - 600000 }, terms, sess, now, now - 100000).action,
      "refuse"));

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

  // --- the argument tail (2026-09-21) ----------------------------------------
  // SYNTHETIC subjects only. This session's real /compact line is deliberately
  // absent: a drill built from the artifact it guards stops testing anything the
  // moment that artifact changes, and the line changes every crossing.
  //
  // Both poles are driven on every run. A predicate that had quietly started
  // returning "" for everything, or dropped its anchor and tailed every command,
  // fails a NAMED case rather than shrinking a count nobody reads.
  check("V-INBOX-ARGTAIL-EXTRACTS", () =>
    assert.strictEqual(argumentTail("/compact focus on v1 phases"), "focus on v1 phases"));
  check("V-INBOX-ARGTAIL-TRIMS", () =>
    assert.strictEqual(argumentTail("/compact   spaced  "), "spaced"));
  // The negative pole, and the one that protects the other commands: an
  // unconditional tail would append a stray line to every autonomous resume.
  check("V-INBOX-ARGTAIL-OTHER-COMMANDS-EMPTY", () =>
    assert.ok(["/gsd-autonomous --from 3", "/cpp-gsd-long", "/absw2-continue"].every((t) =>
      argumentTail(t) === "")));
  // Bare /compact has no separating whitespace, so there is no argument to
  // submit and a second submission would be an empty stray line.
  check("V-INBOX-ARGTAIL-BARE-COMPACT-EMPTY", () =>
    assert.strictEqual(argumentTail("/compact"), ""));
  // `\s+` is the whole difference between a command and a longer word.
  check("V-INBOX-ARGTAIL-PREFIX-IS-NOT-A-MATCH", () =>
    assert.ok(["/compaction now", "/compacted", "/compact-now x"].every((t) =>
      argumentTail(t) === "")));
  // Anchored at the start: a /compact inside prose is not a staged command.
  check("V-INBOX-ARGTAIL-ANCHORED-AT-START", () =>
    assert.ok(["please /compact x", " /compact x", "x /compact y"].every((t) =>
      argumentTail(t) === "")));
  check("V-INBOX-ARGTAIL-NON-STRING-EMPTY", () =>
    assert.ok([null, undefined, 42, {}, [], "", true].every((v) => argumentTail(v) === "")));

  if (process.exitCode === 1) {
    console.log("TERMINAL_INBOX_SELFTEST=FAIL");
  } else {
    console.log("TERMINAL_INBOX_SELFTEST=PASS ok=" + ok);
  }
}
