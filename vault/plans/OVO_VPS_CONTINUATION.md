# OVO Forensic Upgrade — VPS Continuation Handoff

**For:** kobig · **Created:** 2026-04-25 · **Continues:** `vault/plans/OVO_FORENSIC_UPGRADE.md`

## Status snapshot

✅ MC-OVO-100..104 + 108 + 110 — shipped (commits `bc9a5f4`, `2e5bef0`, `944b6ff`, `5d216e2`, `ea44fdb`, `7c83a45`, `bff44e2`).
✅ MC-OVO-106 (Adversarial Replay Harness) — shipped 2026-04-26.
✅ **MC-OVO-107 partial — shipped 2026-04-26 (JS via esprima).** `tools/cascade_populate_js.py` + schema + 14 unit tests. Power-pack's own graph populated (4 nodes, 13 edges, 10 honest STALEMATES — esprima 4.x doesn't support ES2020 `??`/`?.`, the modern files stalemate truthfully). Deferred: TypeScript walker (needs separate parser strategy — `tsc --listFilesOnly` subprocess vs alternative pure-Python TS parser), Python populator, full ES2020+ JS coverage (would require swapping esprima for `pyjsparser`/Node-subprocess/tree-sitter).
❌ MC-OVO-109 (OmniCapture → RLP Wire) — needs OmniCapture query API surface; blocked until docs read or owner-supplied.

## Why this handoff exists

Owner asked for VPS-side execution to free Windows RAM. The current Claude session is a process on the Windows host — it cannot transfer itself. The clean path: the Owner relaunches `claude` on the VPS, this doc is the prompt-bridge.

## VPS bring-up (one-time, ~2 min)

```bash
ssh -i ~/.ssh/kobicraft_vps kobicraft@204.168.166.63
cd ~ && git clone https://github.com/jacobo07/claude-power-pack.git
cd claude-power-pack && python -m unittest tests.test_forensic_probes
```

Expected: 25/25 PASS — proves cross-platform parity (Windows Python 3.13 + Linux Python 3.12 both green). This is the same Path A pattern used in MC-OVO-34-V (mistake-frequency cross-platform parity).

## Continue with `claude` on the VPS

```bash
cd ~/claude-power-pack
claude   # fresh CLI session
```

Then paste this single prompt to continue:

```
Continue OVO forensic upgrade. Read vault/plans/OVO_FORENSIC_UPGRADE.md and
vault/plans/OVO_VPS_CONTINUATION.md for context. Then ship in this order:

1. MC-OVO-108 verification: `python -m unittest tests.test_forensic_probes`
   should be 25/25. Confirm before any new work.

2. MC-OVO-107 (TS/JS cascade populator): build tools/cascade_populate_ts.py
   that walks the .js/.ts files in a target project, extracts require()/import
   call graph, and emits ovo-cascade-graph-v2 nodes with blast_radius.
   Use Python's regex first (fast iteration, no npm deps). If accuracy >85%
   on the power-pack's own lib/ + tools/, ship. If not, escalate to acorn
   (npm) — declare the dep in the populator's docstring.

3. MC-OVO-106 (Adversarial Replay Harness — partial): build the schema for
   vault/audits/replay_log/ + tools/replay_run.py that takes a log entry,
   sends its input through the post-delta sandbox, diffs the output. Real
   sandbox runtime is per-project; ship a "REPLAY_NOT_CONFIGURED" path that
   matches the existing probe pattern. Stop before adversarial mutations
   (next session's work).

4. MC-OVO-109 (OmniCapture → RLP wire): only if OmniCapture's query API is
   documented in this repo. If not, defer — write an ASK to vault/plans/
   listing the exact fields needed.

After each MC: atomic commit, run forensic_probes against the cumulative
delta, OVO Council, push when green. Use --tier FORENSIC since these are
forensic-domain changes — the [FORENSIC_PROBES] band is now mandatory at
that tier (MC-OVO-110).
```

## Critical context for the VPS-side Claude

- **SSH key:** `~/.ssh/kobicraft_vps` is correct for this project. **Do NOT use GEX44** — that's reserved for KobiiCraft / KobiiSports Resort / video-pipeline work per `~/.claude/CLAUDE.md`.
- **Push gate active:** `.powerpack` sentinel present. The OVO push hook (`modules/zero-crash/hooks/ovo-push-gate.js`) blocks `git push` if the last verdict in `vault/audits/verdicts.jsonl` is older than 10 min.
- **FORENSIC tier enforcement (new this session):** when running the OVO Council at FORENSIC tier, the council-text MUST contain `[FORENSIC_PROBES: ...]` band — otherwise `oracle_delta.py --record-verdict` returns exit 4 (Mistake #53). This is the gate you yourself just shipped. Eat the dog food.
- **Anti-thrash hook live:** `~/.claude/hooks/anti-thrash.js` blocks 3+ consecutive Edits on the same file without a Read between them. Plan your edits in fewer, larger passes.

## What the Owner runs to verify VPS-side work landed

```bash
ssh -i ~/.ssh/kobicraft_vps kobicraft@204.168.166.63 \
  "cd ~/claude-power-pack && git pull && python -m unittest tests.test_forensic_probes 2>&1 | tail -3"
```

A clean `25/25` (or `28/28`, `30/30` after MC-OVO-107/106) means the VPS-side session shipped honestly.

## Anti-scaffold reminder for the VPS-side session

The prior session (this one) shipped foundations + caveat-fixes only. MC-OVO-106 / 107 / 109 are full-session subsystems. The Reality Contract still applies:

- Don't ship a `cascade_populate_ts.py` that returns empty nodes for every input.
- Don't ship a `replay_run.py` that fakes a "diff=0" result without an actual sandbox.
- Don't claim OmniCapture wired without an actual env-var hand-off + a probe sample landing in `_audit_cache/runtime_probe.jsonl`.

If a subsystem can't be honestly delivered in one session, deliver the schema + the NOT_CONFIGURED hook + the explicit blocker note. The forensic_probes pattern (3-state contract, NOT_CONFIGURED never falsifies PASS) is the canonical template.
