# IC-009 — Universal Blocking-I/O Eradication & Critical-Path Liveness Closure

Branch: `feature/knowledge-acquisition` · HEAD at scan: `3de3bfa` · Scanned 2026-09-16

## 1. Reality Scan — handoff verdicts

| Prior claim | Verdict | Evidence |
|---|---|---|
| commit `bfb40a1` fixes session-file-guard stdin | **CONFIRMED** | `git show bfb40a1` — 99 insertions, bounded async + hard-exit backstop |
| commit `1b70c2a` adds the ratchet | **FALSIFIED (hash)** / CONFIRMED (content) | `cat-file -t 1b70c2a` → *not a valid object name*. Real commit is **`5ccbe78`**, `tools/test_hook_stdin_liveness.py`, 223 lines |
| ten remaining offenders | **CONFIRMED** | gate run: `STDIN_LIVENESS_PASS=5/5`, standing debt = the exact ten |
| detector false-negative on auto-test-gate | **CONFIRMED, already repaired** | strings no longer stripped; apostrophe trap is a positive control |
| agent-solo-guard is the only other blocking PreToolUse gate | **CONFIRMED** for `readFileSync(0)`; **REFINED** — see §3 |
| the 40-min stall is inherited-stdin blocking | **PARTIALLY PROVEN — and INSUFFICIENT.** See §2 |

## 2. The finding that changes the mission

Measured live during the scan, `Win32_Process` + `Win32_Thread`:

    pid=28128  session-file-guard.js   age=11.4 min  cpu=0 s  parent_alive=False  threads=1  handles=18
    pid=40036  kg-sync-hook.js         age=11.6 min  cpu=0 s  parent_alive=False
    pid=46996  gsd-read-injection-scanner.js age=6.9 min cpu=0 s parent_alive=False
    pid=49296/26336/50720  config.js   age=746/667/537 min  cpu=0 s  parent_alive=False

`session-file-guard.js` **is the hook bfb40a1 fixed**, running from the canonical live path,
byte-identical to the repo copy (sha `15F66D9C0D4A`). Its stdin budget is 2000 ms and its
hard-exit backstop is 5000 ms. It is parked at **11.4 minutes with zero CPU**, and
`state/session-guard-fail-open.log` records **no** hard-exit line — the last entry is
2026-09-15T14:38, a bounded-read timeout from yesterday.

`threads=1` is the discriminator. A live Node runtime carries a libuv threadpool; one thread
means the runtime has torn down. The process is not parked in the read — it is parked
**after deciding to exit**.

> **Bounding the READ does not bound the PROCESS.** The fix moved the block from the input
> boundary to the teardown boundary. Same symptom, same zero CPU, same held pipe, same dead
> screen — one layer further on.

This is the prompt's suspected meta-pattern confirmed on its own repair: *the control assumed
authority over a failure domain it does not own.* An in-process watchdog owns the event loop.
It does not own process death, which belongs to the OS and to inherited handles.

## 3. Canonical population — three classes, not one

36 harness-spawned scripts enumerated structurally from `settings.json`:

| Class | Count | Primitive | Detector sees it? |
|---|---|---|---|
| **A** | 10 | `fs.readFileSync(0)` — blocks the event loop | yes (frozen) |
| **B** | 2 | `hook-utils.readStdin()` — bounded but leaves the `data` listener attached, no `error` handler, no hard exit | **no** |
| **C** | 2 | own `stdin.on('data')` with **no timer at all** | **no** |
| **D** | 17 | own listener, timer present | partially — bound unverified |
| safe | 5 | no stdin read | n/a |

Class B is named as unfixed follow-up in bfb40a1's own message. `kg-sync-hook.js` (Class B) is
parked right now. `gsd-read-injection-scanner.js` (Class D, `exit=N`) is parked right now.
**The ten is a correct count of one primitive and an undercount of the class.**

Live/repo split-brain, measured: `agent-solo-guard.js` live (09-15) ≠ repo (09-04); 4 offenders
exist only in the repo, 2 only under `~/.claude/hooks`. `settings.json` is the authority and
names exactly one path per hook; the repo mirror is stale for several.

## 4. Mode arbitration — ULTRA-PLAN → EXECUTION

Downgrading. Ten hooks is multiplicity, not architectural uncertainty: `session-file-guard.js`
is a proven template and each migration is mechanical-with-semantic-review. The one genuine
unknown (§2) is settled by **measurement, not deliberation**, so it belongs in execution as the
first experiment rather than in another planning round.

## 5. Precondition — host

**369 MB free of 32 061 MB (98.8 % used).** Under this, every timing number is noise and my own
tool calls are part of the load. Reap the proven-abandoned parked processes and re-measure
headroom *before* any latency claim. Any timing taken under starvation is reported **UNMEASURED**,
never as a result.

## 6. Execution plan

**Stage 0 — the exit-boundary experiment (gates everything else).**
Reproduce a hook that has passed its bounded read and called `process.exit(0)` while holding an
inherited stdout pipe with no reader. Determine which of these is true: exit blocked on a
synchronous flush · exit blocked on a held handle · the timer never armed. Outcome decides
whether Stage 2's template needs an exit-boundary clause. Both outcomes are publishable; the
failure mode is assuming the answer.

**Stage 1 — template hardening.** Whatever Stage 0 proves, fold into a single shared bounded-input
contract: bounded read · detached listener · `error` handler · hard-exit backstop that cannot
itself block · explicit distinction between *no input*, *timed out*, and *input said nothing*.
Fix `hook-utils.readStdin` here (closes Class B at the source for both consumers).

**Stage 2 — migrate Class A, ordered by blast radius, not alphabetically.**
1. `agent-solo-guard.js` — PreToolUse, stalls a user turn directly
2. `session_start_hub.js` — measured 7374 ms, no declared budget, delays session open
3. `lazarus-stub-recover.js`, `restart-target-consumer.js` — lifecycle stalls
4. `auto-test-gate.js`, `lazarus-livesnap.js` — PostToolUse / observed orphaned
5. `bug-hunter-*`, `osa_deploy_detector.js`, `subagent-bash-avoidance-advisor.js` — advisory

Per hook, a semantic diff is required before the commit: input parsing · default · error path ·
exit status · stdout · **stderr** (the mute-gate channel) · security verdict · empty input ·
malformed input · premature EOF · parent death. No behaviour change rides along unannounced.
Fixing one means **deleting its line from `KNOWN_OFFENDERS`** — the stale-entry clause makes that
mandatory, and the gate is expected to go red between the fix and the deletion. That redness is
the ratchet working.

**Stage 3 — Class B/C/D.** B closes with Stage 1. C (`cdio_visual_advisory.js`,
`mistake-ingest.js`) gets the template. D is audited for whether the timer actually bounds the
read and whether the process can exit; only the unbounded ones are migrated.

**Stage 4 — detector aperture.** The gate currently answers "does this file call
`readFileSync(0)`". It must answer "can this file park on stdin". Add the Class B/C predicates
with the same posture already chosen (accuse rather than silently certify), keep
parser-failure → non-green, keep the bidirectional inventory, and ratchet the floor toward zero
as entries are deleted. Drive the red branch of each new predicate.

**Stage 5 — promotion + production reality.** For every migrated hook, the target is the path
`settings.json` names. Snapshot the live copy, validate the candidate, promote, verify installed
identity by hash, canary, keep rollback until the canary passes. Reconcile the stale repo mirror
separately and say which direction won.

**Stage 6 — orphan re-measurement.** Re-run the census after migration and attribute what
remains. `config.js` at 12 hours is a different genesis and will not be claimed as ours.

**Stage 7 — knowledge.** UKDL Hard Rule candidates, deduplicated against the existing corpus,
centred on: *bounding an input does not bound a process*; *a timeout is a detection event unless
it owns the resource*; *parser failure is never a PASS*. Vault incidents for the stall, the
detector false negative, the `1b70c2a` hash, and whatever Stage 0 finds. Baseline elevation is a
gate, not prose.

## 7. Non-goals

No new liveness framework. No repo-wide async rewrite. No ban on synchronous local I/O that
cannot block. No CLAUDE.md growth — vault pointers only. No rewriting of another pane's commits.

## 8. Done-gates

Inventory · representative migration · PreToolUse family · full Class A · detector · pipe/process ·
orphan prevention · host runtime · security · baseline. Each states its Production Reality tier
separately: SOURCE / TEST / INSTALLED / RUNTIME / PRODUCTION-PATH / UNKNOWN. Unknown stays unknown.
