# CCR / rollover capsule defects -- scoping (read-only investigation, 2026-11-02)

Evidence: run K4 (state dir gpf-rollover-gpm026gm, capsule 3b06bfd9) vs run S6 (gpf-rollover-bbqwcgt5, capsule f9e6e9e1).
Not verified: I could not locate the CCR receipt files (grep of C:\Users\User\.claude\ccr for `"basis":"unreadable"` found nothing), so the
receipt value is taken from the task brief; the root cause below is derived from code + state-dir contents.

## Defect 1 -- lossy obligation

Observed
- Capsule `obligations` = one paraphrased string, `obligations_source: "explicit"` (gpf-rollover-gpm026gm/capsules/3b06bfd9-....json:31-34).
- Goal file (gpf-cr29-probe/RESUMPTION_FILE.md:5-6) has `## Next` / `1. Create done.txt ... exactly RESUMED-K4-6186fd`. That item matches ITEM_RE under NEXT_HEAD_RE, so `obligations_from(goal)` would have returned it verbatim.
- Ledger: 3x `resume_failed wrong=["next"]` (18:29:38, :46, 18:30:02), then `resume_certified` 18:30:22.

Root cause: CONFIRMED (code + data)
1. The real /kclear path is `tools/session_checkpoint.py seal_capsule` (lines 324-328). It maps the model-authored JSON `pending` array
   (commands/kclear.md:44 "`pending` becomes the capsule's open obligations, first = next") to `next_items` and passes them to
   `rollover.compile_capsule`.
2. `compile_capsule` (tools/rollover.py:359-363) gives `next_items` absolute precedence (`source="explicit"`); the goal file is read only when
   `next_items` is empty. The model summarised the goal file's Next item into `pending`, dropping the token and adding "Owner go-ahead".
   The goal basis was `explicit` and the file was readable, but that is not consulted.
3. `obligations_now` (rollover.py:956-958) re-reads the goal file only when source == "goal file". Source "explicit" -> the stale paraphrase is kept.
4. `exam` (rollover.py:981) asks "next open obligation, from the goal file?" but answers from the capsule's paraphrase; `_matches`
   (rollover.py:1000-1009) requires `want in got` or a substring of >= max(12, len(want)//3). A successor that quoted the real goal-file
   item neither contains the paraphrase nor is contained in it, so it failed. It certified only after echoing the paraphrase.
   The question text and the answer key disagree: that is the defect.

Minimal fix (preferred): goal file wins when readable.
- `compile_capsule`: after `gp = goal_pointer(...)`, if `gp["state"] == "OK"` compute `g_items = obligations_from(gp["path"])`; if non-empty use
  them with `source="goal file"` (so `obligations_now` keeps re-reading live). Fall back to `next_items` (explicit) only when the goal file
  yields none, then own handoff. Keep `next_items` verbatim in a new key `obligations_stated` for audit (optional).
- Alternative if explicit must stay authoritative for non-goal-file callers: only prefer goal file when `gp["basis"]=="explicit"` or "written by this session".
- Optional hardening in `_matches`/`exam`: none needed once the key comes from the goal file; do not loosen the substring rule (D4 guard).
- Optional doc fix: commands/kclear.md:44 -- say `pending` is a fallback and that the goal file's own Next items are used when present.

Files: tools/rollover.py (compile_capsule only), commands/kclear.md (wording). session_checkpoint.py needs no change.
Tests (existing): tools/test_rollover.py (lines ~102-154 build capsules via compile_capsule; line 146 asserts source "own handoff"),
tools/test_rollover_host_affinity.py:114 and test_rollover_session_cwd.py:61 pass goal=None with next_items=["x"] (unaffected: goal not OK -> explicit),
tools/cognitive_ci.py:110 passes goal="g" + next_items=["n1"] (check: "g" may not exist as a file -> goal state not OK -> unaffected).
New gates to add (test_rollover.py): V-OBL-GOAL-WINS (goal file with `## Next` item + paraphrased next_items -> obligations == verbatim item,
source == "goal file"); V-OBL-EXPLICIT-FALLBACK (goal file without Next heading -> next_items kept, source "explicit"); V-OBL-CERTIFY-VERBATIM
(certify with the verbatim goal-file item passes; with the paraphrase fails); V-OBL-LIVE (edit goal Next after seal -> obligations_now follows).
Risk: low-moderate. Behaviour change: a deliberately curated `pending` is overridden by the goal file. Mitigate by the fallback-only rule and by
recording the stated items. Capsules already sealed with source "explicit" are unchanged.

## Defect 2 -- frontier basis `unreadable`

Observed
- K4 state dir has NO `latest/` directory at all (files: capsules/, rollover-ledger.jsonl/.lock). S6 dir has `latest/576459d4.json` (244 bytes) next to its capsule.
- Ledger row for K4 has `"via": "kresume"`-less `capsule_sealed ... "via":"kclear"` (rollover-ledger.jsonl:1), i.e. the session_checkpoint path.

Root cause: CONFIRMED by code + data (receipt value itself not re-read, see header)
- `write_latest_pointer` is called in exactly one place, `rollover.py:1532` (the `seal` CLI subcommand, used by S6). The /kclear path
  `session_checkpoint.seal_capsule` (session_checkpoint.py:329-332) calls `rollover.seal` + `ledger` but never `write_latest_pointer`, so no pointer exists.
- CCR `resolveFrontier` (mods/cpp-cognitive-runtime/hooks/register.ts:142-169): `$.fs.read(<dir>/latest/<rkey>.json)` on a missing file throws; the
  outer `catch { basis = 'unreadable' }` (line 167) fires with `capsule`/`sha` still null, which is exactly {capsule:null, sha:null, basis:'unreadable'}.
  Had the file existed but been bad, `parseFrontierPointer` -> null would give `pointer-missing-or-stale` (line 155) and a hash problem
  `hash-mismatch`, with capsule/sha populated. So `unreadable` + nulls = the pointer read itself threw (absent file / no read access).
- Ruled out by this reading: BOM/encoding, size, retire-after-certify timing (the pointer read happens at session start, before certify; capsule
  json was still present at 19:28:43), schema keys (same rollover-capsule-v1). CPP_ROLLOVER_STATE_DIR resolution is the same code for both runs.
- Residual HYPOTHESIS (cannot exclude without the receipt/env): if the successor's CCR did not see CPP_ROLLOVER_STATE_DIR, it would read
  ~/.claude/state/rollover/latest/<rkey>.json, also absent -> same `unreadable`. Both hypotheses lead to the same fix; to separate them, log `dir` in the frontier receipt.
- Note the repo key: rollover.repo_key(root) (FNV-1a of lowercased, slash-normalised root) must equal policy.ts repoKey(); S6 shows they agree for its repo.

Minimal fix (Python side, no CCR release needed for the main defect)
- `session_checkpoint.seal_capsule`: after `receipt = rollover.seal(cap)`, call `rollover.write_latest_pointer(cap, receipt)` (it already no-ops on an unsealed receipt). Better: factor
  "seal + latest pointer + ledger" into one `rollover.seal_and_record(...)` used by both callers so they cannot drift again.
Files: tools/session_checkpoint.py (seal_capsule), optionally tools/rollover.py (shared helper).
Tests: extend tools/test_rollover_latest.py (V-LATEST-*) with V-LATEST-KCLEAR: call `session_checkpoint.seal_capsule` with a throwaway
CPP_ROLLOVER_STATE_DIR and assert `latest/<repo_key(cwd)>.json` exists, points at the sealed capsule, sha matches. Control: unsealed -> no pointer.
Risk: low; pointer write failure is swallowed (returns None) so /kclear is not blocked.

CCR change (optional, diagnostic only; ships as a release like 0.1.0-39151f03 from 83069706, rollout under HR-2)
- mods/cpp-cognitive-runtime/hooks/register.ts resolveFrontier: split the catch so a missing pointer read gives `basis='pointer-unreadable'`
  (distinct from a failed capsule read) and add `dir` to the receipt. Pure observability; the successor behaviour is unchanged (UNKNOWN, rule files stay).
- Smoke that proves the whole fix: real /kclear -> /clear -> /kresume in a throwaway repo with CPP_ROLLOVER_STATE_DIR set; the successor's
  frontier receipt must read basis 'capsule' with non-null capsule+sha and bytes>0 (rerun of K4). The Python fix alone is provable without a CCR rollout
  because the installed CCR already yields 'capsule' for S6; only the diagnostic split needs a release plus smoke.

## Suggested order
1. Defect 2 fix (tiny, isolated) + V-LATEST-KCLEAR.  2. Defect 1 fix + 4 V-OBL gates.  3. Rerun K4 expecting: first-try certify, frontier basis 'capsule'.
