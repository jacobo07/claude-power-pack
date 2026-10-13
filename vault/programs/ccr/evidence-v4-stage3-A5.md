# CCR v4 stage 3 -- A5 evidence: long-horizon textual work class (Lobby R1)

All numbers are measured on the **Linux plane GEX44, host 2.1.296**. The canary used `~/.local/bin/claude` 2.1.296, and the mod's start receipt reports `compatible: true`. The `/usr/local/bin/claude` on PATH is 2.1.113 and was not used.

Sources:
- the Lobby Ralph-epoch transcripts in `ccr-s3-data/lobby-transcripts` (read only)
- `ccr-s3-data/a5-work/lobby-repo`, a copy of `lobby-repo` with `git init` and one snapshot commit, b6a18d6
- `ccr-s3-data/a5-work/canary-repo`, a `git clone` of that copy

Nothing was written into `lobby-repo` or `lobby-transcripts`.

    D=/home/kobii/missions/ccr-s3-data; W=$D/a5-work
    python3 tools/ccr_lobby_a5.py --transcripts $D/lobby-transcripts --repo $W/lobby-repo --work $W/transcript-copies --out vault/programs/ccr/stage3/a5/a5-offline.json
    python3 vault/programs/ccr/stage3/a5/canary.py --out vault/programs/ccr/stage3/a5/canary.json --round 1

## 1. Offline: E1 arm D (rotate every 40 calls), capsule measured at every rotation point, held-out only

**Corpus and split.** The split is A4's: 51 Lobby sessions with at least 5 calls, ordered by first ts. The earliest 70 % (36) are train and the latest 15 are held-out (2026-09-25 12:34 .. 09-26 00:07). E1's own split (`--cutoff 2026-10-01`) is not usable on this corpus because every session predates the cutoff.

**Capsules.** At each K40 rotation point (call 40, 80, 120, ...) of each held-out session:
- the transcript was copied up to that call, and
- the capsule was built with `ccr_continuation.build(--repo, obligation = first user line, --transcript = the copy)`.

That gives **22 capsules**, all with the predecessor note inlined:

| | min | p50 | p80 | max |
|---|---:|---:|---:|---:|
| tokens | 183 | **222.5** | 256 | 342 |

E1 assumed 8,000 tokens per capsule, which is 36 times the measured p50.

**Cost models**, all on the same recorded call sequence (weights: read 0.1, write 1.25, input 1, output 5):
- **E1-D-8k** is E1's `simulate` exactly. A rotation pays one write of floor + capsule plus that call's input and output, and the context resets to floor + capsule. The capsule is 8,000.
- **E1-D-measured** is the same model, with the capsule measured at each rotation point.
- **A4-D-measured** is A4's rotation cost, with the measured capsule at each point. It adds the capsule write, the measured rehydration (3 calls), the first-call overhead and the re-established context R. Rehydration, overhead and R are fit on train (floor 206,186, R 10,388, rehydration 85,853, first-call 1,905).

| arm | held weighted cost | held processed | rotations | **saving (aggregate)** | median session saving (all 15) | median (the 11 rotating sessions) |
|---|---:|---:|---:|---:|---:|---:|
| A (as recorded) | 48,132,600 | 367,847,860 | 0 | 0 | 0 | 0 |
| E1-D-8k | 45,009,685 | 285,437,582 | 22 | +6.49 % | +3.62 % | +4.74 % |
| **E1-D-measured** | 44,305,394 | 280,360,386 | 22 | **+7.95 %** | **+5.20 %** | +6.25 % |
| A4-D-measured | 47,394,474 | 287,154,138 | 22 | +1.53 % | 0.00 % | -1.09 % |

Reading:
- Replacing the 8k assumption with measured capsules adds **+1.46 points** under E1's model.
- **What makes rotating every 40 calls expensive is not the capsule.** It is the cost of re-establishing the working set after the rotation, which A4 measured at 85.9k weighted per rotation. Including it takes K40 from +7.95 % to **+1.53 %**. That matches A4's K40 +1.54 % with a single p50 capsule, so per-point measurement changes almost nothing there.
- **Not every session gains.** Only aa2d2ac7 is above 10 % (16.8 % / 10.7 %). Under A4's model, 6 of the 11 rotating sessions lose.
- **0685baf6 shows -3.19 % with 0 rotations.** This is E1's clamp: a recorded compaction below the floor is held at the floor. It applies identically to every rotating arm.
- **None of this clears E1's 15 % bar.** E1's +21.1 % came from the laptop's live Lobby project directory, a different corpus. On this corpus, E1's own model with E1's own 8k capsule gives +6.49 %.

Per-session rows, with each capsule's tokens and whether its note was inlined: `stage3/a5/a5-offline.json`.

## 2. Canary: CARRY vs ROT on one bounded textual continuation (haiku, subscription `claude -p`)

**Transcript point.** Ralph epoch `m-1d270cd85220-e5` (session cb70bd86, held-out), cut at **call 40**, which is K40's first rotation point. The recorded context there is 320,382.

**Task (fixed).** Continue the epoch with one bounded step and edit nothing. Report M9's outline span at row v 55.8 and the maximum span. The reply must end with `ANSWER: <a> <b>`.
- Deterministic check: `^ANSWER:\s*18\.9\s+25\.5\s*$`.
- Truth comes from `vault/kme/intake/luckyarena-lobby/MEASUREMENTS.md:318-320`, and the carried transcript also holds both values.

**Settings shared by both arms:** `--model haiku --max-turns 6 --strict-mcp-config --allowedTools Read,Grep,Glob --disallowedTools Edit,Write,Bash,NotebookEdit,Agent`. The working directory is `canary-repo`, and `ANTHROPIC_API_KEY` was removed from the environment.

**The two arms:**
- **CARRY:** a copy of the cut transcript was placed at `~/.claude/projects/-home-kobii-missions-ccr-s3-data-a5-work-canary-repo/<new uuid>.jsonl`. In the copy, the sessionId was rewritten and the stale `last-prompt` line was dropped. The run was `--resume <copy-id> --fork-session`.
- **ROT:** a fresh session with `--plugin-dir mods/cpp-cognitive-runtime` and `CCR_WORK_UNIT={"class":"read-only-reviewer","id":"WU-A5-canary"}`. The mod receipt shows the unit was accepted, with modes unit=enforce. The prompt was the M1 capsule (437 chars, 256 tokens) followed by the task.

**Admission.** MemAvailable was 58,405,848 kB before the round, against the 4 GB required.

| run | arm | calls (model) | input | cache read | cache write | output | **processed** | **weighted** | answer check | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | CARRY | 4 haiku + 1 synthetic (0 usage) | 8 | 1,066,975 | 358,040 | 1,134 | **1,426,157** | **559,925.5** | `ANSWER: 18.9 25.5` | PASS |
| 1 | ROT | 2 haiku | 4 | 14,450 | 27,537 | 549 | **42,540** | **38,615.2** | `ANSWER: 18.9 25.5` | PASS |
| 2-3 | both | -- | | | | | | | | **NOT RUN: budget** (see below) |

- **ROT's weighted saving vs CARRY is 93.1 %** (processed: 97.0 %). Parity: CARRY 1/1 and ROT 1/1 pass. With n = 1, the "median" is that single run.
- **CARRY did not answer from its carried context.** It re-searched (Glob, Grep, Grep, Read) at about 355k context per call. ROT read the file in 1 tool call at about 13-14k context. Without the original epoch's prompt, the fresh unit's floor is 12,361.
- **CARRY's run 1 paid a cold cache write of 354,482** (1h ephemeral), which is 443k of its 560k weighted. Warm runs 2-3 would have read that prefix instead. A rough count from the run 1 call shape, not a measurement: about 150k weighted per warm run. That would still be a ROT saving of about 75 %.
- **This canary prices the capsule continuation of one bounded step. It does not price a full epoch rotation.** ROT here does not re-create the Ralph epoch's ~194k floor, which a real rotation would pay. The economic estimate of rotating is the offline table, not this canary.

**Runs 2-3 not executed (budget).** One CARRY run costs 1,426,157 processed. After round 1 this unit had used about 3.0M, the 3,000,000 budget: this session's 1,555,331 at 24 calls plus the canary's 1,468,697. Two more rounds add about 2.94M and would cross the 4,500,000 hard stop before a receipt could be written. To run them later:

    cd /home/kobii/missions/ccr-s3 && python3 vault/programs/ccr/stage3/a5/canary.py --out vault/programs/ccr/stage3/a5/canary.json --round 2   # then --round 3

The script appends, and it refuses to continue if a run hits the 1,500,000 runaway limit.

## 3. Verdict

- **Offline (economics, 15 held-out Lobby sessions):** K40 with measured capsules saves **+7.95 % weighted** (aggregate; median session +5.20 %) under E1's model. Under A4's measured rehydration model it saves **+1.53 %** (median 0.0 %). This is positive, so not NO_WORK, but below the 15 % bar. Capsule size was never the cost driver (p50 222.5 tokens). Re-establishing the working set after each rotation is, at 85.9k per rotation. A4's break-even rule (+5.47 % on the same held-out, A4) beats fixed K40 under the full model.
- **Canary (task parity, n = 1 per arm):** ROT keeps answer parity (1/1 vs 1/1) at **93.1 % lower weighted cost** (38,615 vs 559,926) on one bounded textual continuation from a 320k-context Lobby point. The run count is limited by budget to 1 of the 3 planned per arm.
