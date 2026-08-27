---
title: Global project map — PP coverage across every repo on this host
date: 2026-08-27
status: MEASURED (not curated)
method: discovered by walking Cursor Projects to depth 3, stopping at every .git
        root; classified by last-commit age; cross-joined against the live
        graphify store and vault/ceps/events.jsonl
covers: [global_project_map, pp_onboarding, project_inventory, rtk_compliance,
         graphify_coverage, ceps_coverage, bootstrap_hook]
---

# Global project map

Every row here was **discovered**, never enrolled by hand. A registry filled in
from memory cannot fail you if it never enrolled you
(`PR-COVERAGE-BY-CONSTRUCTION-001`) — so the denominator is "every `.git` root
under `Cursor Projects`", not "every project someone remembered".

**67 repos found** — ACTIVE 16 · DORMANT 35 · ARCHIVED 12 · NO_COMMITS 4.
ACTIVE = a commit inside 30 days. Only ACTIVE repos are targets.

## 1. The three reported gaps, re-measured

The brief opened with three gaps stated as settled fact. Two do not survive
measurement. Correcting them is the point of this section — acting on the
literal brief would have installed a second RTK proxy on top of a working one
and "enabled" a CEPS capture path that was already capturing.

| # | Claim as briefed | Measured | Verdict |
|---|---|---|---|
| G1 | RTK proxy not installed; every Bash call prints the warning | Wired at `hook-dispatcher.js:190` → `modules/rtk-core/rtk-rewrite.js`, present in BOTH the live and canonical dispatcher (no split-brain). `tools/verify_rtk_fusion.py`: **80.3 % reduction, PASS** against a 77 % floor | **ALREADY CLOSED** |
| G2 | Graphify has 530 cross-repo coordinates, zero for CursorProjects | The store held **60 repos**; `530` was the *promoted global* layer, not the total. But `cursorprojects-73fbe6e64e` (KobiiSports Resort) genuinely held **0 nodes** | **REAL — now closed** |
| G3 | CEPS has 66 KB of events but zero from KobiiSports or CursorProjects | `project_id` = `sha256(cwd)[:12]`. Reversing the hashes resolves **3 events** to KobiiSports Resort's CursorProjects (2026-08-19/20) and 17 distinct project roots overall | **NOT A GAP** |

### G1 — the warning is a vendor self-check, not a PP defect

`rtk.exe` prints `/!\ No hook installed — run 'rtk init -g'` when it cannot find
**its own** init signature (`"command": "rtk hook claude"`) in `settings.json`.
PP deliberately does not use that signature: `rtk init -g` registers the bare
name `rtk`, and `~/.claude/bin` is **not** on the hook-execution PATH, so the
vendor wiring would fail on this host. PP ships a Node port that resolves the
binary by absolute path instead.

The proxy is demonstrably live — RTK compressed this very session's `grep`
output into its `N matches in M files` form, and emitted its own
`Failed to resolve 'rg' via PATH, falling back to direct exec` notice while
doing it. **Running `rtk init -g` would have been a regression**, replacing a
working absolute-path rewriter with a bare-name one that cannot resolve.

Filed in `governance/KNOWN_FALSE_POSITIVES.md`.

### G3 — CEPS is repo-agnostic by construction

CEPS keys on `sha256(os.getcwd())[:12]`, so it captures wherever the session
runs; there is no per-repo enablement to switch on. A `ceps=0` column below
means "no error was captured in the log's 11-day window", never "not wired".
The `.ksr_vault/` fork in KobiiSports is irrelevant to CEPS — nothing in the
capture path reads a repo vault.

## 2. The gap nobody reported — `deferred` was terminal

Chasing G2 to its root turned up the actual defect, one class above the
reported symptom.

`session_writeback.py` (the GK-08 Stop hook) caps a Stop-time index at
`MAX_MD_FILES = 4000` and emits `verdict: "deferred"` with the hint
*"refresh via `indexer --all`"*. **1335 of 2140** writeback attempts carry that
verdict — 62 %.

`--all` discovers from `terminal_slots.json` inside a **7-day recency window**,
and nothing scheduled `--all` at all. So the hint named a refresher that never
came back. `deferred` was a terminal state wearing the word "temporary", and the
sink stayed empty while every component passed its own tests
(`feedback_producer_fires_sink_empty`).

Two repos were sitting at zero:

| repo | nodes before | deferred since | nodes after |
|---|---|---|---|
| KobiiSports Resort `CursorProjects` | 0 | never once indexed | **17,415** (+58 promoted) |
| `Cursor Projects/AKOS` | 0 | 2026-07-12 (46 days) | **8,918** |

AKOS was **not** in the brief. It surfaced only because the debt set is
discovered from the log rather than from the list of repos someone suspected.

Fixed in `442f3bf`: `indexer --deferred` names the debt set and exits 1 when
non-empty; `--deferred --repair` full-indexes it (uncapped, minutes per repo —
never from a hook); the hint now points at a refresher that reads that same log,
so every future skip is recoverable by construction. Gate:
`tools/test_graphify_deferred.py`, 7/7.

## 3. ACTIVE repos — coverage as measured

`graph` = nodes in the live graphify store · `ceps` = events in the 11-day
window · `markers` = onboarding markers present on disk.

| age | repo | graph | ceps | markers |
|---|---|---:|---:|---|
| 0d | claude-power-pack | 1,372 | 5 | `.powerpack` `.pp-onboarded` `CLAUDE.md` `.claude` |
| 0d | Computer Personal Ops | 58 | 2 | `.claude` |
| 0d | CostaLuz Lawyers | 363 | 0 | `.claude` |
| 0d | GEO-audit | 8,312 | 15 | `CLAUDE.md` `.claude` |
| 0d | Jacobo | 69 | 4 | `.pp-onboarded` `CLAUDE.md` `.claude` |
| 0d | KobiiCraft Core Files | 1,845 | 30 | `.powerpack` `CLAUDE.md` `.claude` |
| 1d | FIFA 11 Mod | **32** | 0 | `CLAUDE.md` `.claude` |
| 1d | KobiiHub | **9** | 0 | — |
| 2d | Orca X | 75 | 8 | `.pp-onboarded` `CLAUDE.md` |
| 2d | KobiiSports Resort/CursorProjects | **17,415** | 3 | `CLAUDE.md` `.claude` |
| 12d | CavEX | **238** | 0 | — |
| 12d | kobicraft-web | **50** | 0 | — |
| 14d | kobicraft-auth | **6** | 0 | — |
| 16d | TUA-X | 29,536 (stale) | 0 | `.pp-onboarded` `CLAUDE.md` `.claude` |
| 16d | TUA-X-bdci | **2,368** | 0 | `CLAUDE.md` `.claude` |
| 23d | InfinityOps-gscfix | **524** | 0 | `CLAUDE.md` `.claude` |

Seven ACTIVE repos held **no** graph coordinates at all — a *different* class
from the deferred ones: not skipped for size, simply never visited by a session
that reached Stop. All seven were indexed on 2026-08-27 (bold above), 7/7, in
119 s total; the two that cost real time were TUA-X-bdci (2,189 md → 2,368
nodes, 73 s) and InfinityOps-gscfix (1,522 md → 524 nodes, 35 s). CavEX
promoted 69 nodes to the cross-repo layer and kobicraft-web 25, so the cheapest
repos here were not the least valuable ones.

**Verified after the pass: of 16 ACTIVE repos, zero are absent from the store
and zero sit at zero nodes.** Store 60 → 71 repos; promoted global nodes
530 → 803.

The `ceps=0` column is unchanged and is not a gap — see §1. TUA-X is the one
remaining entry with *stale* rather than absent coordinates; a live pane there
re-defers it at every Stop, so it returns to the debt set until an out-of-band
index lands. Staleness coming back is the gate working, not leaking.

## 4. Onboarding — the mechanism exists and reaches nothing

Phase 5 of the brief asks for a universal bootstrap hook. **Four already
exist.** None is reachable:

| hook | in `settings.json` | in either dispatcher | in the liveness registry |
|---|---|---|---|
| `zero-command-bootstrap.js` | absent | absent | undeclared |
| `first-time-project.js` | absent | absent | undeclared |
| `token-optimizer-bootstrap.js` | absent | absent | undeclared |
| `auto-vault-bootstrap.js` | absent | absent | undeclared |

`token-optimizer-bootstrap.js` is the one the global `CLAUDE.md` § *First-Time
Project Setup* instructs the agent to run by hand — the doctrine documents a
manual workaround for a hook that was meant to be automatic.

This is the Liveness Standard's own thesis, recurring inside the Liveness
Standard: shipping a module is not wiring it. It stayed silent because
`modules/liveness/reachability.py` scores **380 subjects, all under `modules/`**.
A file in `hooks/` is treated as a *seed* of reachability, never a *subject* of
it — so an unwired hook is not scored ORPHAN, it is **absent from the
denominator**, and absence reads as health. That is
`PR-COVERAGE-BY-CONSTRUCTION-001` firing against the very gate written to
enforce it.

Registration is not missing either: `tools/settings_merger.py
register-zero-command` exists and has never been run.

### Why this was not wired blind — an Owner decision, stated

`zero-command-bootstrap.js` writes `.specify/memory/constitution.md` into
**every** repo with a `.git` and a recognised manifest, then stamps
`.pp-onboarded`. Across this host that is a silent Spec Kit install into dozens
of repos — which directly contradicts the brief's own Phase 4 principle
("activate only capabilities with clear positive ROI for that project type";
the KobiiSports fork is cited as proof that by-type design is correct).

There is a second, harder conflict. Phase 4 asks that the onboarding marker
record the activated capabilities. `.pp-onboarded` is *already* that hook's
idempotency latch: writing our own payload there makes
`zero-command-bootstrap.js` a permanent no-op in every repo we touch. **Phase 4
as literally specified disables Phase 5.** The two need different markers.

Both are Owner calls, and both are cheap once decided:

- **(a) Wire it as-is** — `settings_merger.py register-zero-command`, then
  `/restart`. Spec Kit lands everywhere. Fastest; contradicts by-type onboarding.
- **(b) Wire it gated by type** — add a manifest/type predicate before the stub,
  so only repos where Spec Kit pays land it. Keeps `.pp-onboarded` as its latch;
  Phase 4's capability record moves to a distinct `.pp-capabilities` marker.
- **(c) Declare and leave** — **not currently available.** Checked rather than
  assumed: every one of the registry's 131 keys is a path under `modules/`
  (`auto-testing/detectors`, …) and **zero** name a file in `hooks/`, because
  `reachability.py` never scores one. An entry for a bootstrap hook would be a
  key no gate reads — a status nothing can transition, which reads as tracked
  while enforcing nothing, and is worse than the silence it replaces. This
  option only opens *after* the denominator fix below.

**(b) is the recommendation** — it is the only option that satisfies both phases
of the brief instead of trading one against the other.

Independent of that choice, `reachability.py` should take `hooks/*.js` as
subjects and not only seeds; otherwise the next unwired hook is invisible the
same way, and option (c) stays shut. Tracked, not done here — changing a gate's
denominator is its own scoped change with its own evidence, and it is the
prerequisite for (c) rather than an optional companion to it.

## 5. Standing debt, by name

Never a count and never a ratio — a threshold falls by deleting a subject, a
ratio by growing its denominator. Only names move the number for the right
reason.

1. ~~`FIFA 11 Mod`, `KobiiHub`, `CavEX`, `kobicraft-web`, `kobicraft-auth`,
   `TUA-X-bdci`, `InfinityOps-gscfix` — ACTIVE, zero graph coordinates.~~
   **CLOSED 2026-08-27**, 7/7 indexed; verified by re-deriving the ACTIVE set
   and re-querying the store, not by trusting the indexer's own return values.
   Replaced by: **`Cursor Projects/TUA-X` — stale, not absent** (29,536 nodes
   from 2026-07-03). Two backgrounded repair attempts were killed by the
   harness before completing; per the two-consecutive-failures law the third
   attempt used a different layer (a detached `Start-Process`, PID confirmed
   alive) rather than a third retry of the same shape. Its outcome is
   unverified at the time of writing — `python modules/graphify/indexer.py
   --deferred` is the authority, and it will keep naming TUA-X until an index
   actually lands. The gate self-reports; this line does not have to.
2. `zero-command-bootstrap.js`, `first-time-project.js`,
   `token-optimizer-bootstrap.js`, `auto-vault-bootstrap.js` — exist,
   unreachable, undeclared. Blocked on the §4 decision.
3. `modules/liveness/reachability.py` — scores `modules/` only; `hooks/` is a
   seed set, never a subject set.
4. `~/.claude/state/graphify/` holds **437** `.gf_*` per-session marker files
   with no reaper. Not load-bearing; noted so it is not rediscovered as a
   mystery.
