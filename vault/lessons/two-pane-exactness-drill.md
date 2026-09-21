# The two-pane exactness drill — what it proves, at exactly its real size

**Subject:** `tools/two_pane_drill.py` + `tools/test_two_pane_exactness.py`
**Sealed evidence:** `vault/evidence/two-pane-exactness/<run-id>.json`
**Drill runs on this host:** `enterfix` (2026-09-20), `phase1-live{,2,3}` (2026-09-19)

This file exists because the claim is easy to overstate by one word. "The
continuation goes to the right pane" is what everyone wants it to say. What was
actually driven, once, live, on one host, is narrower — and the narrow version
is the useful one, because it is the one that stays true.

## PROVEN

With two Claude Code sessions in two terminals of **one** Cursor window:

1. **A received it.** A continuation armed for pane A reached A's transcript as a
   submitted `type:"user"` row after `t0`. Re-derived on every gate run by the
   product's own predicate, `gsd_long_run.user_issued_command_since`, never by a
   re-implementation — a copy of that matcher was wrong on its first day earlier
   in this milestone.
2. **B did not.** A's nonce never appears in B's transcript after the same `t0`.
3. **The instrument that reported B's absence can return the other answer.**
   *(Added 2026-09-21; the drill ran for a day without it.)* The same predicate,
   over the same transcript and the same window, finds something B really typed.
   Without this leg, clause 2 is satisfied identically by an instrument that
   cannot see pane B at all — and that was not hypothetical: blinding the
   instrument deliberately (B's `t0` pushed 24 h forward) still prints
   `PASS V-TWOPANE-B-UNTOUCHED`. The old gate reported `6/6`, exit 0, from an
   instrument seeing nothing.
4. **A refused request was ledgered with the owning window's own reason.** An
   owned request whose `claude_pid` has no session file was answered in 0.28 s
   with `session-unreadable`; an unowned one drew no ack in 15.04 s and nothing
   was typed. Leg A is the positive control that makes leg B's silence mean
   anything.

Every refusal returns before the `term.sendText` branch, which is reachable only
through `action: "send"`, so a request built to be refused cannot produce a
keystroke. Re-confirmed by direct read at `extension/src/extension.js:100-106`.

## NOT PROVEN — each with its reason

- **Pane B was not a dedicated subject.** In the `enterfix` run B is the
  *ambient invoking session* (`37cfb187`, the project's own long-running working
  pane), captured at fire time from `CLAUDE_CODE_SESSION_ID`. That is a real live
  pane and a legitimate negative control, but it is not the disposable second
  subject the plan describes, and the plan's Task 6 human-verify checkpoint —
  built precisely to catch this — was never run. **This is the phase's largest
  open item and it cannot be closed without a human opening a second pane.**
- **The `orca-exact` route.** This host has no Orca runtime. Every `V-CXT-*` gate
  drives a fake Orca subprocess. Deferred as GSDX-C08; claim nothing.
- **Two sessions in the same cwd.** The drill deliberately used one scratch cwd
  per pane. The `vault/terminal_slots.json` clobber is *avoided*, not exercised.
  Exercising it would add no coverage of `decide()`, which never reads cwd.
- **Two sessions in two different Cursor windows.** Only the one-window case ran,
  which is the case `ownedTerminals` exists to disambiguate. The cross-window
  `ignore` path (`terminal_inbox.js:71`) is inferred from source, not observed.
- **A headless extension-host harness.** None was found. The drill needs a human
  for both panes, and that stays true until someone builds one.
- **The autocompact entry point.** The drill fires flags directly into the
  daemon's own flag dir. Whether `context-watchdog.py::_route_for` /
  `_dispatch_continuation` chooses this route on a REAL autocompact was not
  exercised. Open.
- **The `V-CWIRE-*` gate bodies were never read.** This work assumed nothing from
  them. They remain unread rather than checked.
- **How `~/.claude/sessions/<pid>.json` comes to exist.** Determined by exclusion
  during planning: no writer exists in this repo or under `~/.claude/hooks`, and
  the file's own fields say `claude.exe` writes it. Its `status` transitions are
  outside this repo's control and were not enumerated — the drill waits for
  `idle` rather than causing it.
- **`TAIL_BYTES` in `_tail_rows`.** Measured that this run's rows fell inside the
  tail window; the constant itself is unread, so the assertion is about this run,
  not about every run.

## The registry declaration the plan asked for cannot be made

Task 5 asked for `tools/two_pane_drill.py` to be declared in
`vault/liveness/reachability_registry.json`. **Measured 2026-09-21: that would be
a no-op.** `modules/liveness/reachability.py:269` enumerates
`<repo>/modules` only, and only packages carrying `__init__.py`. `tools/` is
outside its observation domain, so the drill can never be flagged there and a
declaration would suppress nothing.

Writing one anyway would produce a record that *looks* like coverage and provides
none — the failure mode `documented-capability-must-be-executable.md` names. So
it was refused, and this paragraph exists instead.

Separately: `reachability.py` exits **1** on this branch today, on ~20 pre-existing
orphans (`knowledge_acquisition/*` among them) that belong to other work. Phase
1's done-criterion "reachability.py exits 0" was therefore unmeetable by phase 1
regardless, and nothing here claims to have fixed it.

## How to re-derive any of this

```
python tools/two_pane_drill.py probe                  # 7/7 preconditions
python tools/two_pane_drill.py seal --runid <runid>   # freeze pointers, no verdicts
python tools/test_two_pane_exactness.py --runid <runid>
```

Three exit codes, and the third is the point: `0` every gate passed, `1` a gate's
subject is wrong, `2` the evidence or an artifact it names could not be read, so
this run **judged nothing**. A verifier that could not judge its subject must
never present as a verdict about it.

The sealed evidence stores **pointers, never conclusions** — no `a_received`
flag, no verdict of any kind. The transcripts and the ledger persist on disk and
the gate re-reads them every invocation, so deleting or editing one turns the
gate red instead of leaving a green describing a world that no longer exists.
