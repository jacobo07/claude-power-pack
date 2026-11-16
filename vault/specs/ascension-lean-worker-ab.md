---
spec: ascension-lean-worker-ab
status: DRAFT (Owner "y" 2026-11-16, pane 4de9b293: spec + A/B on one lane)
tier: T2 (new worker launch route for the Ascension autopilot; user-visible behaviour of workers changes)
covers: [ascension-autopilot, gsd_mission slim-t2, route_admission, worker prefix]
---

# Ascension lean worker: A/B of the slim-t2 launch on one lane

## 1. Problem (measured, GEX44, 2026-11-16 ~11:30Z)

Worker transcripts of the last 14 h (`~/.claude/projects/-home-kobii-missions-*`, 100 sessions, 3,920 model
calls, 531M processed tokens; script `usage.sh`/`usage3.sh` in the pane scratchpad):

- mean processed tokens per model call **135.8k**; first call of a session **54.8k / 75.2k / 109.3k** (min/median/max);
  96% of everything processed is cache reads. Model mix by tokens: Sonnet 5.5 74%, Opus 5.5 26%.
- what the first call carries (bytes of the attachments in one MKW worker session): skill listing 74.7 KB
  (194 skills on the host), agent listing 56.8 KB (95 agents), instructions 54.9 KB (TENNIS/KSR product
  CLAUDE.md 40 KB), SessionStart hook context 40.7 KB, prompt snapshot 18.1 KB.
- what workers use: tools Bash 1,592 / Agent 82 / Write 77 / Read 71 / Skill 28; skills only `gsd-*`
  (autonomous 14, execute-phase 5, plan-phase 5, discuss-phase 3, code-review 1); agents only `gsd-*`.
  `wii-power-pack`, `wii-disc-reconstruction`, `mobile-game-wii-port`, `instrument-before-claim`: present, 0 calls.

Prefix probe, `claude -p --model=sonnet "Reply with the single word OK."` in `/home/kobii/missions/mkw-decomp`
(`probe.sh`, one call each):

| launch shape | first-call prefix |
|---|---|
| default `-p` | 36,917 |
| `--setting-sources=project,local` (no user hooks/plugins) | 26,480 |
| + `--disable-slash-commands` | 26,480 |
| + `--tools=Read,Grep,Glob,Bash,Edit,Write` (no Agent) | 19,888 |
| slim-t2 shape (`--setting-sources=local`, kernel system prompt, `--exclude-dynamic-system-prompt-sections`) | **6,296** |

Not measured: the share of the 531M spent inside GSD subagents (the transcript split did not resolve; do not cite one).

## 2. What already exists (do not rebuild)

- `gsd_mission` slim launch: `slim_profile` / `slim_argv` / `_launch_slim` (print mode, our own `--session-id`,
  budget breaker through `--settings=vault/config/slim-critical-settings.json` for slim-t2).
- `route_admission.admit` with measured profile floors (`vault/config/route-floors.json`); `gsd_mission envelope
  --wu-packet` + `admit --route` record `worker_profile` on the mission; launch reads that one field.
- Slim finish handling: `slim_finished` -> COMPLETED, or HALTED when the breaker tripped, the worker reported
  is_error, or (halt_continue on) the work unit's receipt is absent / not closed; `halt_continue` then applies.

## 3. Design (A/B arm only; the other lanes keep the `--bg` + GSD launch)

The A/B lane arms exactly as today (`arm --no-launch`, hold, authority), then, before release:
1. Packet: the generation's PHASES packet + `command_text` with the `/gsd-autonomous` sentence replaced by
   "execute the phases yourself in order, committing as you go" (slim has no slash commands and no Agent tool).
2. `gsd_mission envelope --mission M --wu-packet <packet> --model <the lane's control model>` (same model as the
   control generations, so the A/B measures the launch shape, not the model).
3. Route `{"envelope": {target, warn, stop, calls}, "workers": [{"name": "w", "profile": "slim-t2", "calls": N,
   "packet": <packet tokens>}]}`; `gsd_mission admit`. Not ADMISSIBLE/WATCHED -> the lane arms the normal way
   (logged `lean_fallback`), never parks on it.
4. Judgment: a slim mission that ends COMPLETED/HALTED **with** a checkpoint hold or a committed checkpoint file
   named in the packet goes to the judge exactly like a hold (new branch in `lane_tick`; today a terminal state
   is read before the hold and would park it). The work-unit receipt the slim path requires is written by the
   worker as the packet's last step (format: `tools/receipt_json` / `_receipt_path`, to be read before coding).

## 4. A/B protocol and decision rule (frozen before the first arm)

- Arm: one lane, the next 3 generations slim-t2. Control: the same lane's last 3 `--bg` generations + the other
  lanes over the same window.
- Primary metric: processed tokens per model call (from the transcripts, same script as section 1).
  Secondary: generations per 10M, judge verdict class (CERT/CAPABILITY/INFORMATION/NONE), policy refusals.
- Decision rule: ADOPT for more lanes if mean tokens/call drops >= 30% AND no judged generation of the arm is
  worse than INFORMATION for a reason the judge attributes to the launch shape (missing gates, uncommitted
  evidence, skipped freeze). REJECT if tokens/call drops < 15% or 2 of 3 generations end without a judgeable
  checkpoint. In between: Owner look.
- Positive control for the metric: the section-1 script re-run on the control window must reproduce 135.8k
  +/- 10% before the arm's number is read.

## 5. Risks to resolve before coding (read, do not assume)

- R1 A long `-p` run: no Ralph continuation, no autocompact guarantee in print mode; a 7-10M generation is
  ~100+ calls. Check `--autocompact`/print-mode behaviour on the host build before the first arm.
- R2 Receipt contract of the slim path (`_receipt_present`): exact file and closing Status.
- R3 Without GSD the plan/verify discipline rests on the packet and the autopilot's own policy + judge. The judge
  already re-runs gates and checks freeze order; accepted as the experiment's question, not a defect.
- R4 Lane choice: the A/B lane should not be the one carrying the best open result (MKW, 35/40 held-out at 100).

## 6. Acceptance

V-AP-LEAN-* tests in `test_autopilot.py` (packet rewrite drops `/gsd-autonomous`; admit refusal falls back to the
normal arm; terminal slim mission with a checkpoint is judged, without one parks as today), mutants for each,
gate 100% with no survivors, deployed on GEX44 behind `lanes.json` `"worker": "slim-t2"` on ONE lane.

## 7. Rollback

Remove `"worker"` from the lane in `lanes.json` (next arm is `--bg` again). Code path inert without it.
