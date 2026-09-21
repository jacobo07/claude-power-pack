---
phase: 01-two-pane-exactness-drill
date: 2026-09-21
source: 01-VERIFICATION.md (gaps_found, 7/13)
closed: 4
refused: 1
still_open: 1
---

# Phase 1 — gap closure

Written beside `01-VERIFICATION.md`, not into it. That report describes the
audit that happened; editing its findings to match a later repair would
fabricate a verification. This is the dated record of what changed afterwards.

| Gap (as the verification stated it) | Outcome | Commit |
|---|---|---|
| G1 `V-TWOPANE-B-INSTRUMENT-CAN-SEE` never coded; 2 of 6 live gates exist | **CLOSED** | `b1f7a49` |
| G3 `vault/evidence/two-pane-exactness/<run-id>.json` never produced | **CLOSED** | `2dcda8f` |
| G4a `vault/lessons/two-pane-exactness-drill.md` absent | **CLOSED** | `68d1559` |
| G4b declare `two_pane_drill.py` in `reachability_registry.json` | **REFUSED, with measurement** | `68d1559` |
| G5 Tasks 4–6 have no commits | **partly** — 4 and 5 now do; 6 needs a human | — |
| G2 pane B was the ambient session; Task 6 never run | **OPEN** | — |

## G1 — the control that makes the claim mean anything

The plan calls this leg load-bearing and it was never written. Its absence was
not theoretical: blinding the instrument on a copy of the real `enterfix` run
(B's `t0` pushed 24 h forward) **still prints `PASS V-TWOPANE-B-UNTOUCHED`**, and
the old suite reported `TWOPANE_PASS=6/6`, exit 0 — a clean bill from an
instrument that could see nothing. It now exits 2 and names the pane it could not
see. A second drill, pointing B's transcript at A's file, reds `B-UNTOUCHED`,
so that absence assertion is not vacuous either.

The plan's needle, `nonce_B`, does not exist in this design — pane B is the
drill's own session and is never armed. The gate uses what was really typed in B
after `t0` instead: same predicate, same transcript, same window, same `since`.

**Retraction worth keeping.** I first read `panes.B.nonce` as B's own nonce and
was about to "correct" `B-UNTOUCHED`. `two_pane_drill.py:454` writes B's entry
with `info["nonce"]` where `info` is pane **A**'s record, so that key holds A's
nonce and the gate was already correct. Reading the key name instead of the
writer would have broken a working gate.

## G4b — why the registry entry was refused

`modules/liveness/reachability.py:269` enumerates `<repo>/modules` only, and only
packages carrying `__init__.py`. `tools/` is outside its observation domain, so
the drill can never be flagged there and a declaration would suppress nothing —
a record that looks like coverage and provides none. The reasoning is preserved
in `vault/lessons/two-pane-exactness-drill.md`.

Also measured: `reachability.py` exits **1** on this branch over ~20 pre-existing
orphans belonging to other work, so the phase's "reachability.py exits 0"
criterion was never meetable by this phase.

## G2 — what is still owed, and why I did not close it

The sealed run's pane B is the ambient invoking session (`37cfb187`), captured at
fire time from `CLAUDE_CODE_SESSION_ID`. That is a real live pane and a
legitimate negative control, but not the disposable second subject the plan
describes, and Task 6's human-verify checkpoint never ran.

Closing it needs a human to open a second Claude session in a terminal this
Cursor window owns, then `arm --pane B` / `fire --pane A` / `seal`. No amount of
work inside this pane substitutes for that, and manufacturing a pane B from a
fixture would defeat the phase's entire purpose.

## Re-derivation

```
python tools/two_pane_drill.py probe                   # 7/7
python tools/two_pane_drill.py seal --runid enterfix   # pointers, no verdicts
python tools/test_two_pane_exactness.py --runid enterfix
```
Current: `PROBE=7/7` exit 0 · `TWOPANE_PASS=7/7` exit 0.
