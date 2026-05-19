---
title: /resume v3 — Lazarus v3 Feature Spec
status: ready-for-implementation
authority: derived from real frame-by-frame vision analysis of operator capture
source_video: ~\Videos\2026-05-15 18-28-33.mp4 (24.1 MB, ~221 s)
frame_corpus: PowerPack_Sovereign_Datasets/_frames2/ (12 JPEG @ 640w, 8 global + 4 dense)
authored: 2026-05-15
seal: BL-0064 / Sovereign Miner v2 — Pillar 4
---

# /resume v3 (Lazarus v3) — Feature Spec

## Source of truth

Every observation in §1 cites a specific frame from the operator's screen
capture. No hypothesized pains, no inferred behavior. Frames live at
`~\Downloads\PowerPack_Sovereign_Datasets\_frames2\`. The
synthesized observations were captured verbatim into `vision_notes.txt`
in that same directory.

---

## §1 — Observed pain (frame evidence)

### Frame `g_01` (≈00:27) — Kernel spam

Terminal shows **Node.js v24.15.0** with stack traces:

> `Cannot find module '...\.claude\hooks\lazarus-janitor.js.DISABLED'`
> `Cannot find module '...\.claude\hooks\lazarus-heartbeat.js.DISABLED'`
> `code: 'MODULE_NOT_FOUND'`, `loader:1479`,
> `Stop hook error: Failed with non-blocking status code`

Status line: *"Cogitated for 5m 10s"*. This is the exact orphaned-hook
class the Pillar-1 disk purge fixed. Frame-grade proof that the pre-purge
state spammed fatal Node errors **every Stop event** — a degraded
foundation any "resume" UX is built on top of.

### Frame `g_04` (≈01:48) — Command surface

Claude Code **v2.1.142** with `/re` autocomplete listing
`/recap /review /resume /rewind /restart /resume-clean`. The on-screen
short description for `/resume` reads:

> *"Filtered session picker (text table) — shows only RESUMEABLE
> sessions (excludes ones currently LIVE in other Cursor terminals)."*

So the native picker **already** intends a live-exclusion filter. The
filter mechanism in place today (renaming `.jsonl` → `.jsonl.live`,
single-flag) works but is brittle, and the picker is the only UX
surface the operator sees — its quality bounds the whole experience.

### Frames `g_08` / `d_01` / `d_03` / `d_04` (03:00 → 03:41) — The picker

Header reads **"Resume session (3 of 40)"** then **"(4 of 40)"**.

What the operator is looking at, captured live:

- **40 sessions** for project *InfinityOps* in a single flat scrolling list
- **~half are `(untitled)`** and visually indistinguishable from each other
- Relative timestamps mixed (`"1 minutes ago"` … `"42 minutes ago"`)
- Branch tags exposed (`feat/ql-rental-compliance-reboot`,
  `db-migrate-worktree-cleanup`)
- File sizes vary 18.2 KB → 3.1 MB
- A subset shows PR refs (`jacobo07/InfinityOps#46/#29/#8`)
- Footer hotkeys: `Ctrl+A all projects | Ctrl+O current branch |
  Space preview | Type to search | Esc cancel`

Only **3–4 sessions visible per page** of a 40-entry list. No window /
pane grouping. LIVE sessions are not visually flagged in this list. Half
the rows untitled forces content-preview hunting to find the right one
per pane.

## §2 — Root pain synthesis (what the frames prove)

1. **Pre-purge kernel state was actively hostile** — every Stop event
   crashed two Node hook processes with `MODULE_NOT_FOUND`. The cure
   was a 3-file delete (Pillar 1), but the wider lesson is that the
   `/resume` UX sits downstream of hook-kernel hygiene; a fragile
   kernel makes restore-flows look broken even when they aren't.
2. **The picker has no topology model.** A 40-deep flat list cannot
   answer the operator's actual question ("which session goes in
   *this* pane?"). It treats sessions as a stream when they are a
   graph: project × window × pane × branch × age × liveness.
3. **Redundancy is invisible.** The `.jsonl.live` rename hides
   currently-attached sessions, but there is no view of *what's
   already loaded where*, so a freshly-opened pane has no way to
   tell whether the session it wants is already up in another window.
4. **Half the corpus is untitled.** That forces space-preview
   hunting per session, every time, which scales as O(n·preview).

## §3 — Lazarus v3 architecture (C1 – C5)

The five-component design carried from `vision_notes.txt` (originally
written into `RESUME-UPGRADE-SPEC.TXT` §C). Each is bounded, file-local,
and lives entirely in user-space; native modal preserved.

### C1 — Topology snapshot per Stop

On every Stop event the Stop-chain writes a single JSON object to
`~/.claude/state/lazarus_v3/topology.json` with the shape:

```jsonc
{
  "schema": "lazarus_v3/topology/1",
  "generated_at": "<ISO-8601>",
  "panes": [
    {
      "uuid": "<session-uuid>",
      "window_id": "<terminal-window>",
      "pane_id": "<pane>",
      "cwd": "<absolute>",
      "branch": "<git-branch-or-null>",
      "title_hint": "<first-user-prompt-truncated-256>",
      "last_seen": "<ISO-8601>",
      "scroll_offset": "<int-or-null>",
      "size_bytes": <int>
    }
  ]
}
```

`window_id` / `pane_id` come from `wt.exe` / Cursor terminal env
(`WT_SESSION`, `CLAUDE_TERMINAL_ID`). When those env vars are unset on
the platform, fall back to a stable hash of `(pid_of_parent_terminal,
cwd)`.

### C2 — Redundancy filter

A session is considered **attached** when *both* hold:

1. The on-disk file is `<uuid>.jsonl.live` (not `<uuid>.jsonl`).
2. C1 topology lists a pane whose `uuid` matches **and**
   `last_seen` is within the last 60 seconds.

The picker hides any session for which both conditions are true. A
single condition alone is suspect (e.g., a crashed pane leaves
`.jsonl.live` orphaned for >60 s — that session should reappear in the
picker, not be permanently hidden).

### C3 — Multi-pane rehydrate (one command)

`/resume --topology` reads `topology.json`, presents the picker grouped
by `(project, window_id)` instead of a flat list, and on selection
opens each chosen UUID in its own pane via the terminal multiplexer's
spawn API. mkdir-mutex on `<state>/<uuid>.lock` serializes per-UUID so
two concurrent panes cannot pick the same session.

### C4 — Heartbeat owns liveness

A 30-second heartbeat (PostToolUse + Stop) refreshes
`<state>/<uuid>.heartbeat` (mtime). A session is **stale** when both:

- `now - mtime(heartbeat) > 30 s`, **and**
- C1 topology does not show that uuid in any pane within 30 s.

Two independent positive signals before reclaim (per ACV stale-marker
lesson: a single signal is a known foot-gun for destructive ops).

### C5 — Hook surface

| Hook | Event | Action |
|---|---|---|
| `lazarus-v3-snapshot.js` | Stop | Write/update topology + heartbeat |
| `lazarus-v3-rename.js` | SessionStart | Rename `<uuid>.jsonl` → `.live`; release stale `.lock` files |
| `lazarus-v3-cleanup.js` | Stop (deferred) | Reclaim stale `<uuid>.jsonl.live` → `.jsonl` after C4 conditions |

Native picker is left untouched. v3 is **additive**: `/resume` keeps
working unchanged; `/resume --topology` is the new surface.

---

## §4 — Implementation surface

### State directory layout

```
~/.claude/state/lazarus_v3/
  topology.json                   # singleton, rewritten per Stop
  <uuid>.heartbeat                # touch-only, mtime is the signal
  <uuid>.lock                     # mkdir-mutex, owner is pid
  metrics.jsonl                   # append-only: stale-reclaim events
```

### Interop with existing hooks

- Pillar-1 kernel scan probed 30 referenced hooks clean; the 3 new
  Lazarus-v3 hooks slot in alongside `lazarus-snapshot.js` (already
  active in `settings.json` Stop chain) and `resume-hide-live.js`
  (already active in SessionStart chain) without removing either.
- `resume-hide-live.js` currently does the `.jsonl` → `.jsonl.live`
  rename. C5's `lazarus-v3-rename.js` does **not** duplicate this; it
  *consumes* the rename and adds lock-release. Single source of truth
  for renaming remains the existing hook.
- The native modal continues filtering by `.endsWith(".jsonl")` (per
  `project_native_resume_hide_live` memory, BL-0013) — that contract
  is unchanged.

### Configuration

`~/.claude/lazarus_v3.json` (optional, all keys default-safe):

```jsonc
{
  "stale_threshold_seconds": 30,
  "heartbeat_interval_seconds": 30,
  "group_by": ["project", "window_id"],
  "max_panes_per_group": 8
}
```

### Backwards compatibility

- A fresh install with no `topology.json` falls through to the existing
  `/resume` behavior (flat picker). No regression on first use.
- A user who never invokes `/resume --topology` never pays the cost.

---

## §5 — Verification plan

| Gate | Method | Pass criterion |
|---|---|---|
| G1 — Topology written | Trigger Stop, read `topology.json` | File present, schema-valid, pane count > 0 |
| G2 — Live-pane hidden | Open pane A, in pane B run `/resume --topology` | A's uuid does not appear in the picker while heartbeat is fresh |
| G3 — Crash recovery | Kill pane A's process, wait 35 s, run picker again | A's session reappears (stale > 30 s + topology absent) |
| G4 — Lock mutex | Two panes race `/resume --topology` selecting same uuid | Only one acquires; the other gets a clear "already attached" message |
| G5 — Native unchanged | Run native `/resume` | Identical output to v2 baseline (same filtered list) |

All gates require observable output (log line, file mtime, or stderr
message); none are satisfied by "no error" alone.

---

## §6 — Out of scope (named so it's not silently expected)

- Cross-machine resume (state dir is `~/.claude` only).
- Renaming or reorganizing the native picker itself — v3 ships a new
  flag (`--topology`), it does not edit `commands/resume.md`.
- Persistent xterm.js scrollback restoration. Per
  `reference_cursor_state_vscdb` memory: scroll position and input
  buffer **do not** live in `state.vscdb`; they live in xterm.js
  renderer state and require a Cursor-extension surface that we do
  not own.

---

## §7 — Frame index (audit trail)

| Frame | Time | Caption |
|---|---|---|
| `g_01.jpg` | ~00:27 | Pre-purge MODULE_NOT_FOUND stack on Stop |
| `g_02.jpg` | ~00:54 | (context — terminal scroll mid-session) |
| `g_03.jpg` | ~01:21 | (context — operator typing) |
| `g_04.jpg` | ~01:48 | `/re*` autocomplete + `/resume` description |
| `g_05.jpg` | ~02:15 | (context) |
| `g_06.jpg` | ~02:42 | (context) |
| `g_07.jpg` | ~03:09 | (context) |
| `g_08.jpg` | ~03:36 | Picker header *"Resume session (3 of 40)"* |
| `d_01.jpg` | 03:00 | Picker dense — flat list of untitled entries |
| `d_02.jpg` | 03:10 | Picker dense — branch/size mix visible |
| `d_03.jpg` | 03:20 | Picker dense — PR refs visible |
| `d_04.jpg` | 03:30 | Picker dense — *"(4 of 40)"* + footer hotkeys |

Frames `g_*` were sampled `fps=1/27` over the full 221 s clip;
frames `d_*` were sampled `fps=1/10` from the 3:00 dense-pain window.
Both extractions are deterministic given the input video.
