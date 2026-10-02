# Phase 1: Baseline integrity repair - Research

**Researched:** 2026-10-02
**Domain:** PP `modules/tower` constitutive-baseline ratchet / done-gate (pure Python stdlib, no external packages)
**Confidence:** HIGH (every claim below was read from source or observed by running it this session; tags `[VERIFIED: path:line]` mean the file was opened with Read this session)

## Package Legitimacy Audit
No external packages are installed by this phase (stdlib only). Section not applicable.

## Findings log (appended as confirmed; planner-facing summary follows at the end)

### F0. ENVIRONMENT TRAP (read first): worktree checkout is CRLF, generation anchors are LF
- `C:/Program Files/Git/etc/gitconfig` sets `core.autocrlf=true` [VERIFIED: `git.exe config -l --show-origin`]. The worktree therefore holds CRLF bytes for every tracked text file; `git ls-files --eol` shows `i/lf w/crlf` for all 5 baseline files [VERIFIED: `git ls-files --eol vault/tower/baselines`]. (`/usr/bin/git` from the Bash PATH has no such config and reports 3502 "modified" files - ignore it; use `C:\Program Files\Git\cmd\git.exe`, which reports 0.)
- `bl.generation_sha256` hashes the on-disk bytes (`modules/tower/baselines.py:130-133`). `web_surface/B1.json` stores `parent_sha256: 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7` = the sha of the LF form of B0.
- Consequence observed: `tools/test_tower_ratchet.py` is **20/21 in this worktree**, `V-TRAT-REAL-CHAINS FAIL ... web_surface ... 'tampered': [1]` - an environment (CRLF) failure, not a logic failure.
- Consequence for the plan: a new generation written here (`reanchor` -> `persistent_state/B1.json`) would store `parent_sha256 = sha256(CRLF B0)`, which is TAMPERED everywhere LF bytes are checked out. **Normalise line endings of the baseline files BEFORE any reanchor write.**
- Precedent for the fix: `.gitattributes:28-35` already pins byte-sensitive files with `text eol=lf`. Recommended: append `vault/tower/baselines/**  text eol=lf` to `.gitattributes`, then re-checkout the 5 B*.json files (unmodified vs HEAD, so safe) so disk bytes == committed blob. Alternative (code, not config): make `generation_sha256` hash with CRLF->LF normalisation. Choose one in plan; do NOT leave it unaddressed.
- sha256 record (task Q7). "blob" = `git show HEAD:<path>` = LF = the bytes that are meant to be immutable; "worktree" = CRLF bytes currently on disk:

| file | blob sha256 (LF, canonical) | worktree sha256 (CRLF, current) |
|---|---|---|
| vault/tower/baselines/kobiicraft_mode/B0.json | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | c2ebd2567006784ea5510f376586a02ad8b9d5402d49e9396e131097fd5fe7af |
| vault/tower/baselines/persistent_state/B0.json | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | 62757541f34812961681eff73aae0538cb5dfaaa6ab79105347587ea5b5d60eb |
| vault/tower/baselines/web_surface/B0.json | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | c5e9c67e861f255de5580992c19f09de24b6f1aa9031ddefa0aecbb6634d9d9e |
| vault/tower/baselines/web_surface/B1.json | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | 883d7918fc4c7b980020e53e3fc8b93f807aa920ec2e8a531f188d6b236f84f6 |
| vault/tower/baselines/wii_homebrew/B0.json | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | 1a73b1e83d0b054109fdf525ead742ec499a577adf5969852bcc743155bf7e30 |

  (LF-normalised hash of each worktree file equals its blob hash: verified by a Python hash of `bytes.replace(b"\r\n", b"\n")`.) Immutability gate = blob hash via `git show HEAD:<path>` / `git hash-object`, or the LF-normalised hash, never the raw CRLF hash.
- Only `persistent_state` and `wii_homebrew` have B0 only; `web_surface` has B0+B1 (B1 = 17 entries, `parent: 0`, `promoted_by: "Owner (approved 'both', 2026-10-01)"`) [VERIFIED: B1.json header read]. No `archetype/` dir exists yet.
- Tooling note: PowerShell tool is DISABLED in this session; Bash works only with the `# bash-safe` marker (guard `windows-bash-bridge-guard.js`) and `git` must be the absolute-path git.exe.

### F1. Baseline test status at HEAD of this worktree (task Q6)
| test | exit | result line |
|---|---|---|
| `tools/test_baseline_generations.py` | 1 | `BASELINE_GENERATIONS_PASS=15/16  threshold=16/16` (FAIL `V-BGEN-REAL-B0-CITATIONS-HOLD population=62`) |
| `tools/test_tower_ratchet.py` | 1 | `TOWER_RATCHET_PASS=20/21  threshold=21/21` (FAIL `V-TRAT-REAL-CHAINS`, F0) |
| `tools/test_tower_donegate.py` | 0 | `TOWER_DONEGATE_PASS=10/10  threshold=10/10` |
| `tools/test_family_baselines.py` | 0 | `FAMILY_BASELINES_PASS=20/20  threshold=20/20` |
| `tools/test_tower_select.py` | 0 | `TOWER_SELECT_PASS=15/15` |
| `tools/test_tower_checks.py` | 0 | `TOWER_CHECKS_PASS=23/23` |
| `tools/test_tower_capsule.py` | 0 | `TOWER_CAPSULE_PASS=16/16` |
| `tools/test_tower_inheritance.py` | 0 | `TOWER_INHERITANCE_PASS=16/16` |
| `tools/test_family_injection.py` | 0 | `FINJ_PASS=23/23` |
| `tools/test_tower_o4.py` | 0 | prints "CLAIM NOT PROVEN (b)" by design; exit 0 |

- Output-line convention: `_check(gate, cond, evidence, diagnostic)` prints `  PASS %-38s <evidence>` or `  FAIL %-38s <diagnostic>`, final line `<NAME>_PASS=%d/%d  threshold=%d/%d`, `return 0 if _FAIL == 0 else 1` [VERIFIED: tools/test_baseline_generations.py:27-34,211-214; tools/test_tower_ratchet.py:36-43,246-249]. `test_family_injection.py` uses `check(name, cond, detail)` and prints `FINJ_PASS=`.
- Hermetic HOME [VERIFIED: tools/test_family_injection.py:78-84]: `home = tempfile.mkdtemp(prefix="finj-home-"); env = dict(os.environ, HOME=home, USERPROFILE=home, ...); os.environ.update(HOME=home, USERPROFILE=home); os.environ.pop(cli.FAMILY_SWITCH, None)`; first gate asserts `Path.home() == Path(home)`. Needed only by tests that import `modules.gsd_x.cli` (its `heartbeat.py:31` calls `Path.home()` at import). The tower-only tests are hermetic via `root=<tmp>` and need no HOME.
- Run-environment trap: under Git-Bash, wrapping Python in `timeout N` strips HOME and makes `modules.gsd_x.heartbeat` raise `RuntimeError: Could not determine home directory` at import (observed on test_tower_inheritance / test_family_injection). Run Python directly, no `timeout`.

### F2. `modules/tower/ratchet.py` (task Q1, Q3) - all line numbers [VERIFIED by Read this session]
Signatures:
- `revert(family: str, entry_id: str, reason: str, authority: str, root: str | None = None) -> str` (`ratchet.py:146-161`) - one id per call; writes `changes={entry_id: {"kind": REVERTED, "reason", "authority"}}`.
- `promote(family: str, new_entries: list, reason: str, authority: str, root=None) -> str` (`:164-183`) - `existing = {e["id"] for e in (cur or {}).get("entries", [])}` at `:169` (includes reverted ids, so re-adding a reverted id raises "entry id %s already exists"); sets `extra={"promoted_by": authority}`; checks only `bl.REQUIRED` keys; no `verify_origin`, no admission.
- `diff(parent: dict, child: dict) -> list[(id, kind)]` (`:72-91`). Compares ONLY: presence/`status=="reverted"` (WITHDRAWN/REVERTED), `check` (WEAKENED if `check_rung` rose, else CHECK_CHANGED if `_squash` differs), `requirement` (REWORDED). Fields `why`, `origin`, `class`, `propagation_scope` are never read -> H2.
- `_recorded(child, ident, kind) -> bool` (`:94-99`): `rec = child["changes"][ident]`; `kind in rec["kind"]` (kind may be str or list) AND `str(rec.get("reason") or "").strip() != ""` AND `str(rec.get("authority") or "").strip() != ""`. Any non-empty string is an "authority" -> H1.
- `_need(reason, authority)` (`:139-143`): non-empty only; raises `RatchetRefusal(ValueError)` (`:46-47`).
- `verify_chain(family, root=None) -> ChainReport` (`:120-136`): per child: `anchor = child.get("parent_sha256")`; `if not anchor: rep.unanchored.append(cur)` / `elif anchor != bl.generation_sha256(family, prev, root): rep.tampered.append(cur)`; then every `diff` item not `_recorded` -> `regressions` `{generation, id, kind}`; `DUPLICATE_ID` per generation (`:124-125`).
- `ChainReport.ok` (`:110-112`): `return not self.regressions and not self.tampered` - **`unanchored` is reported but not part of `ok`** -> H3b. `as_dict()` keys: family, generations, regressions, tampered, unanchored, ok (`:114-117`).
- Kind constants (`:38-43`): `WITHDRAWN REVERTED WEAKENED CHECK_CHANGED REWORDED DUPLICATE_ID`. `REANCHORED` does not exist yet.
- `check_rung(check)` (`:50-57`): 0 for kinds in `ck.STATIC_KINDS`, 1 for `ck.DELEGATED_KINDS`, else 2.

Generation file shape (`bl.write_generation`, `baselines.py:141-199`; example `web_surface/B1.json` header read this session):
`{"family", "generation", "parent", "parent_sha256", "created_at", "reason", "entries": [...]}` plus `extra` keys. `_CORE = ("family","generation","parent","parent_sha256","created_at","reason","entries")` (`baselines.py:137-138`) - `extra` may not override these (raises ValueError); `changes` and `promoted_by` are free extras. Duplicate ids raise ValueError (`:168-174`). Publication = private temp + `os.link` (create-if-absent), LF bytes (`newline="\n"`, `:178`). Entry shape (persistent_state/B0.json:8-20): `id, requirement, why, origin{file,line,quote}, class, check, status` (`status` default "auto" on promote). `REQUIRED = ("id","requirement","why","origin","class")` (`baselines.py:34`). No entry carries `propagation_scope` today.

`verify_origin(entry, window=3) -> str` (`baselines.py:62-97`): returns `VERIFIED` only if every REQUIRED key exists, `origin.file` is a file, `origin.line >= 1`, and - WITH `origin.quote` - `_squash(o["quote"]) in _squash(lines[line - 1])` (quote must be on the cited line exactly, whitespace-insensitive, `:87-89`). Otherwise `MOVED` (quote elsewhere in file), `QUOTE_MISSING`, `FILE_MISSING`, `MALFORMED`; with no quote it falls back to a +-3 line shared-vocabulary test (`WEAK`/`VERIFIED`) - that fallback must NOT be accepted for reanchor (require a non-empty quote). Constants `VERIFIED/WEAK/LINE_MISSING/FILE_MISSING/MALFORMED/MOVED/QUOTE_MISSING` (`:28-45`).

Authority is checked nowhere except "non-empty string" (`ratchet.py:94-99,139-143`). Callers outside tests (task Q9) [VERIFIED by grep]: `tools/family_baseline.py:115-116` (`rt.verify_chain(family)`), `:128-131` (`rt.revert(family, entry_id, reason=reason, authority=authority)`, catches `rt.RatchetRefusal`), `modules/tower/donegate.py:76` (`rt.verify_chain(family, root).ok`), `wiki/tools/cbr_probe.py` (read-only probe). `modules/gsd_x/cli.py:104` mentions donegate in a docstring only. `rt.promote` has NO production caller. `donegate.judge` has NO production caller. Additive changes (new kinds, new function, stricter `ok`/allowlist) break none of them as long as signatures of `verify_chain/revert/promote` are unchanged and the CLI's authority input is an allowlisted token (`family_baseline.py` `verify` prints "(no reason+authority on record)" for every regression - the message wording should be generalised when new kinds are added, `family_baseline.py:118-119`).
Authority strings in use: tests pass `"Owner"` everywhere (`tools/test_tower_ratchet.py`, `test_tower_donegate.py:162`); real data: `promoted_by: "Owner (approved 'both', 2026-10-01)"` (web_surface/B1.json). No real generation has a `changes` key.

### F3. Why H1/H2/H3b pass today, and a trap in the probe (task Q3)
Probe source `wiki/tools/cbr_probe.py:92-146` [VERIFIED]. Mechanism and proof, reproduced this session on a B0-ONLY synthetic copy of web_surface (script output: `H1 ok= True`, `H2 ok= True`, `H3b ok= True [] [1]` i.e. tampered=[] unanchored=[1]):
- **H1**: B1 drops `entries[0]` with `changes[id] = {"kind":"WITHDRAWN","reason":"x","authority":"x"}` -> `_recorded` true -> ok=True. Fix = authority allowlist (and optionally a minimum reason).
- **H2**: B1 rewrites `why`, `origin={"file":"nowhere.md","line":1}`, flips `class` C<->D, no record -> `diff` is blind to those fields -> ok=True. Fix = diff `why`, `origin`, `class`, `propagation_scope`.
- **H3b**: `entries[3:]` removed from BOTH B0 and B1 and B1's `parent_sha256` set to None -> nothing to diff, `unanchored=[1]` but not in `ok` -> ok=True. Control with anchor intact -> `tampered=[1]`, ok=False. Fix = `ok` must also require `not unanchored`.
- **PROBE TRAP (important for the plan):** the probe copies the WHOLE `web_surface` dir (`cbr_probe.py:74-77`). Since commit `09b1172` web_surface has B0+B1, so the probe's `child_with` writes **B2 from B0's entries**, silently withdrawing B1's two additions. Run today (`python wiki/tools/cbr_probe.py`, exit 0) it already prints `H1 ... ok=False`, `H2 ... ok=False`, `H3b ... ok=False tampered=[2] unanchored=[1]` - **for the wrong reason**. "Probe goes red" is therefore VACUOUS against the real tree. The plan's attack gates must (a) use a synthetic family built the way `test_tower_ratchet.py:62-66` does (`fresh()`), or copy only `B0.json`, and (b) be shown GREEN-on-attack (ok=True) against the UNFIXED code first (RED step), then flip after the fix, each paired with a control that stays ok=True (clean `revert`+`promote`; same edit WITH an allowlisted authority and record; same hollowing with anchor intact stays tampered). Instrument-before-claim: a gate that was never seen to pass the attack on old code proves nothing.
- Remaining non-attack observation: `H3` (editing the newest generation in place) is REFUTED/caught already (probe line 26; keep as a control, do not "fix").
- Not closable by Phase 1: a forger who recomputes `parent_sha256` after hollowing both generations is undetectable; the newest generation's integrity is repo history (docstring `ratchet.py:26-28`). State this limit in EVIDENCE.

### F4. The 9 QUOTE_MISSING entries (task Q2) [VERIFIED: ran verify_origin + `bl.locate_quote` against candidate files this session]
Failing gate: `V-BGEN-REAL-B0-CITATIONS-HOLD population=62` (62 = 15 x 3 + 17 web_surface). Every one cites a stub under `~/.claude/rules/` (quote + old line below), and **every quote is still present verbatim in the skill**, at old line + 5 (a 5-line frontmatter). So all 9 re-anchor; none need reverting ("text gone" = 0).

| id (family) | old origin (file:line) | NEW line in SKILL.md | skill |
|---|---|---|---|
| persistent_state-destructive-op-authorizes-exact-state-seen | `C:\Users\User\.claude\rules\destructive-state-authorization.md`:8 | 13 | destructive-state-authorization |
| persistent_state-destructive-identity-falsification-test | same :21 | 26 | destructive-state-authorization |
| persistent_state-absence-of-identity-refuses | same :37 | 42 | destructive-state-authorization |
| persistent_state-precondition-window-must-be-closed | same :77 | 82 | destructive-state-authorization |
| persistent_state-batch-reauthorize-per-item | same :104 | 109 | destructive-state-authorization |
| persistent_state-monetary-qualifiers-travel-with-amount | `...\rules\monetary-quantity-integrity.md`:10 | 15 | monetary-quantity-integrity |
| persistent_state-monetary-conflicting-qualifiers-refuse | same :21 | 26 | monetary-quantity-integrity |
| persistent_state-monetary-no-conversion-without-authorized-source | same :32 | 37 | monetary-quantity-integrity |
| wii_homebrew-claim-must-name-observing-plane | `...\rules\develop-here-prove-there.md`:9 | 14 | develop-here-prove-there |

Quotes (verbatim, from B0.json; the new origin must carry exactly the same `quote`):
1. `> **What exact state did the user authorize destroying, and is it still there?**`
2. `**The test is a falsification, and it is cheap:** construct one case where the destructive target`
3. `**Absence of an identity is never "unchanged".** A missing value means the caller could not say, and`
4. `## The check is authoritative for the effect only if nothing can move in between`
5. `**A batch cannot share one authorization moment.** Authorize every item in one pass and then destroy`
6. `**An amount travels with its qualifiers as fields, or it cannot be combined with`
7. `- **Two known qualifiers that disagree → refuse.** There is nothing to go and`
8. `Conversion needs a rate, a rate date, a provider and provenance. Without all`
9. `> every runtime verdict. A claim names the plane that observed it, or it is not a claim.**`

Candidate new origin paths - both hold all 9 quotes at the lines above:
- `C:\Users\User\.claude\skills\<skill>\SKILL.md` (stable absolute path, outside any worktree; this is the path I verified with `bl.locate_quote`; the home copy is NOT git-tracked in the worktree).
- `<worktree>\skills\<skill>\SKILL.md` (verified identical lines) - **do not use: audit G15 forbids worktree-path origins**, they rot when the worktree is removed.
- PP main-checkout path `C:\Users\User\.claude\skills\claude-power-pack\skills\<skill>\SKILL.md` would be the git-tracked canonical (audit G15 / Phase-4 "main-checkout path"); I did not read it (parent checkout is off-limits for this research). The executor may probe it read-only with `bl.verify_origin` through `reanchor`'s own refusal and fall back to the home path. Recommendation: use the home path (verified), note the main-checkout alternative in EVIDENCE.
- Existing convention: every origin in B0 is an absolute Windows path with backslashes (persistent_state/B0.json:13,26).
- The home-copy and worktree-copy of each SKILL.md have equal LF-normalised sha256 prefixes (2985bd97.., 34e63a8d.., f649b72b..), so the lines are stable across both.

### F5. `ratchet.reanchor` design (task Q1) - constraints derived from the code
`reanchor(family: str, new_origins: dict, reason: str, authority: str, root: str | None = None) -> str`, new origin = `{"file","line","quote"}`:
1. `_need(reason, authority)` (+ allowlist, see F6).
2. `cur = bl.latest(family, root)`; refuse if none; every id must be in `_active(cur["entries"])` (same refusal wording as `revert` `ratchet.py:153-155`); refuse an empty dict.
3. For each id: candidate = `dict(old_entry, origin=new_origin)`; require non-empty `quote`, require `_squash(new.quote) == _squash(old.quote)` (recommended: same words, new home - a different quote is a REWORDED/revert+promote case and is the H2 laundering vector), and `bl.verify_origin(candidate) == bl.VERIFIED` (MOVED/WEAK/QUOTE_MISSING all refuse; message names id + verdict). Refuse a no-op (new origin == old). **All-or-nothing**: if any id refuses, nothing is written.
4. One `bl.write_generation(family, entries_with_new_origins, "reanchor <ids>: <reason>", root=root, extra={"changes": {id: {"kind": REANCHORED, "reason": reason, "authority": authority, "from": old_origin, "to": new_origin}}})` - ids, status, check, why, class unchanged; one generation per family (persistent_state: 8 ids; wii_homebrew: 1 id; two calls, two files).
5. `diff` must emit `REANCHORED` when `origin` differs (compare `file`, `line`, `quote` after `_squash`); then `_recorded(child, id, REANCHORED)` is satisfied by the record above. Do NOT call `verify_origin` inside `verify_chain` (it would turn every future rot of a historical origin into a chain regression and double-count what `V-BGEN-REAL-B0-CITATIONS-HOLD` already owns); verification happens at write time (refusal) and in the citations gate.
6. Why not revert+promote: `promote` rejects re-adding a reverted id (`ratchet.py:169,175`) and `revert` is one id per call (9 generations B1..B9). [VERIFIED: ratchet.py:146-183]
7. Expected result: `persistent_state/B1.json` and `wii_homebrew/B1.json` exist, `verify_chain` ok for both, `V-BGEN-REAL-B0-CITATIONS-HOLD` passes with population 62 and `broken={}`. B0.json of both stays byte-identical (blob hashes in F0).
8. **Ordering constraint (F0):** fix line endings BEFORE the first `reanchor` write, otherwise `parent_sha256` of the new B1 is the hash of CRLF bytes.
9. Downstream effect: the injected stamp (`family_block`, `cli.py` uses the latest generation) changes for persistent_state and wii_homebrew to the B1 sha; `V-FINJ-STAMP-*` recomputes from `bl.generation_sha256(fid, latest)` so it stays consistent. `test_tower_select`/`test_family_injection` read `bl.active_entries` (latest) - entry text unchanged so injected/deferred counts (7/8, 8/7) are unchanged.

### F6. Ratchet hardening design (task Q3) - Claude's discretion items, with recommendations
- New `diff` kinds (constants next to `ratchet.py:38-43`): `WHY_CHANGED`, `ORIGIN_CHANGED`->use `REANCHORED`, `CLASS_CHANGED`, `SCOPE_CHANGED` (`propagation_scope`; absent==absent so no churn on today's entries). Compare with `_squash` for strings, and a normalised `(file,line,quote)` tuple for origin. Treat `new.get(k)` vs `old.get(k)` identically so missing==missing.
- `ChainReport.ok` = `not regressions and not tampered and not unanchored` (`ratchet.py:110-112`). Real chains are fine: web_surface B1 is anchored (`parent_sha256` present), B0s have no parent. No existing test hand-writes a child without an anchor (V-TRAT-DUPLICATE-ID hand-writes a lone B0, `test_tower_ratchet.py:191-194`). Add `unanchored` to the `family_baseline.py verify` printout (`family_baseline.py:117-124`), which currently prints REGRESSION/TAMPERED only.
- Authority allowlist: recommended = module constant `AUTHORITIES = ("Owner",)` in `ratchet.py` plus `is_authorized(authority) -> bool` matching the FIRST token of the stripped string (`re.split(r"[\s:(,;]", s, 1)[0]`) case-sensitively, so `"Owner"` and `"Owner (approved 'both', 2026-10-01)"` pass and `"x"` fails; apply it in `_need` (revert/promote/reanchor) AND in `_recorded` (raw `write_generation` records). Constant in code, not a data file: tests are hermetic via `root=` and a data-file lookup would need a root parameter and would be writable by the same attacker that writes generations. A mission-run reanchor uses authority `"Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)"` [ASSUMED: the Owner's plan approval is accepted as the Owner's authority; confirm]. Optionally also require `len(reason.strip()) >= 8` and reason != authority so `reason="x"` stops being a licence; pin with a control. Existing tests use reasons like "superseded by b" / "moved to docs site" (>= 8) and `reason=" "`/`"x"` only in refusal cases (`test_tower_ratchet.py:82-89` - `reason="x"` is used in cases that must refuse for ANOTHER reason (unknown id, already reverted, duplicate promote); they still refuse, so a min-length rule does not change their outcome).

### F7. Donegate and checks (task Q4) [VERIFIED by Read]
- Verdict constants (`donegate.py:33-40`): `APPLIED_VERIFIED VIOLATED DELEGATED NOT_APPLICABLE UNJUDGED NO_BASELINE JUDGED`; `SOURCE = "tower-baseline"`; `_FROM_CHECK = {ck.PASS: APPLIED_VERIFIED, ck.FAIL: VIOLATED, ck.DELEGATED: DELEGATED}` (`:42`), everything else -> UNJUDGED (`:68`).
- `judge(family, repo_root, registry=None, root=None, not_applicable=None) -> dict` (`:45-80`). N/A today (`:56-64`): `na = not_applicable or {}`; `if ident in na and str(reason or "").strip()` -> NOT_APPLICABLE with the free-text reason as detail (**any non-empty string, no vocabulary, no cap, no expiry**); `elif ident in na` -> UNJUDGED "declared not applicable with no reason". N/A short-circuits the check (never evaluated).
- `would_block = any(x["verdict"] in (VIOLATED, UNJUDGED) for x in out)` (`:78`): VIOLATED and UNJUDGED are lumped; DELEGATED and NOT_APPLICABLE never block. Report keys: family, judged_under, generation_sha256, chain_ok, status, report_only (always True), would_block, entries[{entry_id, verdict, check_outcome, detail, requirement, injected, source, judged_under}], deferred_from_prompt.
- `checks.py`: grammar kinds `file glob regex registry test` (`checks.py:53-54`); `test:` -> `_evaluate` returns `(DELEGATED, "test exists; run by the repo, not here")` if the file exists else `(FAIL, "named test does not exist")` (`:148-155`). `checks.py` imports no subprocess and never executes anything (imports at `:35-39` are glob/json/os/re/dataclass). `evaluate()` returns a `CheckResult` carrying `.kind` (`:58-68,159-170`), so donegate can tell a `test:` DELEGATED from a `registry:` DELEGATED.
- **H5** (probe, reproduced above): all 17 entries declared N/A with reason `"n/a"` -> `would_block=False {'NOT_APPLICABLE': 17}`. **H6**: `test:tests/test_x.py` whose only test is `assert False` -> `verdict=DELEGATED would_block=False`. Both reproduce today (probe lines 36-37) and the probe's donegate section is NOT contaminated by the B1 issue (it builds its own `probe_fam` for H6; H5 control `would_block=True {'UNJUDGED': 17}`).
- `test_tower_checks.py:129-131` PINS `test:<existing>` -> `ck.DELEGATED` at the checks layer (`V-TCHK-TEST-DELEGATED`); `:118-119` pins registry -> DELEGATED. **Do not change `checks.py` outcomes**; remap in `donegate.judge`: `if r.kind == "test" and r.outcome == ck.DELEGATED -> UNJUDGED` with a distinct reason code.
- Recommended donegate design (discretion): constants in `donegate.py` (NOT a new module -> no liveness registration, and Phase 6 imports them from the same place):
  - `NA_REASONS` closed vocabulary (tokens, kebab-case): `no-persistent-state`, `no-user-interface`, `no-external-effect`, `no-money`, `single-actor-local`, `not-this-family`, `superseded-by-entry`, `out-of-scope-this-change` [ASSUMED: wording; derived from the trait names in ROADMAP Phase 2 criterion 1]. Accept `token` or `token: free text`; a reason whose token is not in the set -> UNJUDGED ("not in closed vocabulary"), same row shape as today's no-reason case.
  - `NA_SHARE_CAP = 0.30` of active entries, count allowed = `floor(cap * n)` (n=5 fixture -> 1, matches V-TDG-VERDICT-KINDS's single N/A; n=15 -> 4) [ASSUMED value]. When over the cap, void ALL N/A claims of that run to UNJUDGED ("N/A share %d/%d over cap") - which entries are legitimate is unknowable and picking some is gameable. Report `na_count`, `na_cap`, `na_over_cap` bool.
  - Rows get `unjudged_reason` in {`prose`, `empty`, `test-not-run`, `na-no-reason`, `na-not-in-vocabulary`, `na-over-cap`, `unreadable`, `other`}; report adds counts `{violated, unjudged, unjudged_tests, delegated, not_applicable, applied}` and an `unjudged_tests: [ids]` list, so "test not run" is never merged into VIOLATED (G13). Keep `would_block` semantics (violated OR unjudged) and add `would_block_on_violated` for the stricter number.
  - Pin "never executed on a hook path" by (a) a gate whose `test:` file writes a marker file when run - assert the marker is absent after `judge()` (positive control: running the file by hand creates it), and (b) an AST/import scan asserting `modules/tower/checks.py` and `donegate.py` import none of `subprocess, os.system, runpy, importlib, exec` (positive control: a fixture source that imports `subprocess` is flagged).
- Existing tests that MUST change with the vocabulary: `tools/test_tower_donegate.py:98` and `:121` use `not_applicable={"web-mobile": "desktop-only admin tool"}` and `V-TDG-VERDICT-KINDS` (`:116`) / `V-TDG-CONTROL-WIRED` rely on NOT_APPLICABLE; switch those reasons to a vocabulary token (e.g. `"no-user-interface: desktop-only admin tool"`). `V-TDG-NA-NEEDS-REASON` (`:127-130`, reason `"  "`) stays UNJUDGED unchanged. `V-TDG-REPORT-ONLY` (`:132-137`) expects would_block True - still true.
- Production callers of `judge`: none (grep this session). `modules/gsd_x/cli.py:143-145` (delivered sentence "The done-gate judges every active entry ... `NO APLICA: <reason>`") promises it; the sentence fix is deferred to Phase 6 per CONTEXT.

### F8. The hardcoded family tuples and discovery (task Q5)
- `tools/test_tower_ratchet.py:235-244` [VERIFIED]: `for f in ("web_surface","persistent_state","kobiicraft_mode","wii_homebrew"): if bl.generations(f): seen += 1; r = rt.verify_chain(f); if not r.ok: bad[f] = r.as_dict()` then `_check("V-TRAT-REAL-CHAINS", seen == 4 and not bad, ...)`.
- `tools/test_baseline_generations.py:200-209` [VERIFIED]: `for fam in (same 4): for e in bl.active_entries(fam): real[e["id"]] = bl.verify_origin(e)`; `broken = {k: v ... if v not in (bl.VERIFIED, bl.MOVED)}`; `_check("V-BGEN-REAL-B0-CITATIONS-HOLD", len(real) >= 60 and not broken, ...)` (note: MOVED is tolerated here, VERIFIED is required by `reanchor`). This test mutates `bl.BASELINES_DIR` elsewhere (`:185-191`) and restores it, so the walker must read `bl.BASELINES_DIR` at call time, not import time.
- `BASELINES_DIR = <PP_ROOT>/vault/tower/baselines` (`baselines.py:26`). Today it contains exactly: `kobiicraft_mode/B0.json`, `persistent_state/B0.json`, `web_surface/B0.json`, `web_surface/B1.json`, `wii_homebrew/B0.json` [VERIFIED: `find` this session]; there is no `archetype/` directory yet. `_family_dir(family, root)` is `os.path.join(root or BASELINES_DIR, family)` (`baselines.py:100-101`), so a nested subject id like `archetype/WORLD_MUTATION` (forward slash) resolves with no change to `generations()/load_generation()/latest()/active_entries()/write_generation()` (audit-clean note, `audit.md:24`). `generations()` matches `^B(\d+)\.json$` (`baselines.py:35,104-108`) so `.B1.*.tmp` residue is ignored.
- Recommended: add `discover_subjects(root: str | None = None) -> list` to `baselines.py` (additive, ~10 lines): `os.walk(root or BASELINES_DIR)`; a directory is a subject iff it directly contains a file matching `_GEN`; id = `os.path.relpath(dirpath, base).replace(os.sep, "/")`; return sorted. Both tests call it. Floors (discretion): `len(subjects) >= 4` AND each of the four known family ids present is NOT required (that would reintroduce the hardcoded tuple) - instead floor on population: subjects >= 4, total active entries >= 60 (today 62), and every subject's generation list starts at 0. Positive controls in the new test file: a temp root with `archetype/X/B0.json` -> `["archetype/X"]` (nested axis is found); an empty temp root -> `[]` (so a floor of 4 would FAIL on an empty walk - the floor is exercised); a stray `B9.json.tmp` and a dir with only `notes.json` are ignored. This also satisfies Phase 4 criterion 3 ("discovered-subject gates include them") with no further edit.
- Sensible floor sentence for the gate message: "N subjects, M active entries, floor 4/60".

### F9. Liveness registry (task Q8)
`vault/liveness/reachability_registry.json` = `{"known_orphans": [..9 strings..], "modules": {<pkg>/<module>: {"class": "LIBRARY"|"SCHEDULED"|"DEPRECATED"|"PLANNED", "note": "..."}}}` (151 modules); PLANNED notes name the consumer and an "Owner queue: <path>" [VERIFIED: registry read this session, e.g. `lease/__init__`]. No `tower/*` key is present today. **Phase 1 needs no new module** if the recommended design is followed (everything lands in `ratchet.py`, `donegate.py`, `baselines.py`, tests, plus one new TEST file, which the scanner does not treat as a module). If the planner chooses a new module (e.g. `modules/tower/na_vocab.py`), declare it PLANNED + owner-queue line in the same commit and never run `reachability.py --baseline` [roadmap constraint G11].

## Summary

Phase 1 is small, mostly additive, and fully understood. The baseline chain is red for two independent reasons: (1) nine `persistent_state`/`wii_homebrew` origins cite stubbed `~/.claude/rules/*.md` files (all nine quotes still exist verbatim in the matching skill, +5 lines), and (2) in this Windows worktree `core.autocrlf=true` makes every baseline file CRLF while `web_surface/B1.json` anchors the LF hash of B0, so `test_tower_ratchet` fails `V-TRAT-REAL-CHAINS` (TAMPERED) here regardless of any logic. Fix (2) before writing any new generation, or the new B1 anchors will be wrong everywhere LF is checked out.

The ratchet and gate holes are exactly as the CBR gap analysis describes (any non-empty string is an authority; `why/origin/class/propagation_scope` are outside `diff`; `unanchored` is outside `ChainReport.ok`; N/A is a free-text string with no cap; `test:` returns DELEGATED which never blocks). The probe `wiki/tools/cbr_probe.py` can no longer be trusted as the RED/GREEN instrument for the ratchet cases: the web_surface B1 landed after it was written, so its attacks already read `ok=False` for the wrong reason. Prove the attacks against a B0-only or synthetic family on unfixed code first (I did: H1/H2/H3b all `ok=True`), then fix.

**Primary recommendation:** (a) normalise line endings of the 5 baseline files (`.gitattributes` `vault/tower/baselines/** text eol=lf` + re-checkout, precedent `.gitattributes:28-35`); (b) add `ratchet.reanchor` + diff coverage + `ok`-includes-unanchored + authority allowlist, written test-first in a NEW file `tools/test_ucep_baseline_integrity.py`; (c) run `reanchor` twice (persistent_state 8 ids, wii_homebrew 1 id) to the verified home-skill paths; (d) donegate: closed N/A vocabulary + share cap + `test:` -> UNJUDGED counted separately; (e) `baselines.discover_subjects` replaces both hardcoded tuples; (f) record sha256 before/after and write `01-EVIDENCE.md`.

## Project Constraints (from CLAUDE.md and ROADMAP)
- Worktree `.claude/worktrees/ucep`, branch `ucep/mission`; never touch the parent checkout, never push; commit only own paths with `git commit -F <msgfile> -- <paths>`; verify `git log -1 --format=%s` after (CLAUDE.md anti-overlap, ROADMAP operating constraints). Use `C:\Program Files\Git\cmd\git.exe` (the Bash-PATH `git` is a different build without autocrlf and reports ~3500 phantom modifications).
- Never edit `~/.claude/settings.json`, `~/.claude/CLAUDE.md`, `~/.claude/rules/`, `~/.claude/hooks/` (so the reanchor origin must point INTO `~/.claude/skills/`, read-only use).
- Reality Contract: no stubs/placeholders; DONE needs observed evidence (HR-OUTPUT-002/003). Tests narrow, hermetic, bracketed by dirty-path SET before/after (concurrent-writers rule). Windows: Python via absolute interpreter path, `PYTHONIOENCODING=utf-8`; PowerShell tool was unavailable in this research session (executors may have it).
- Plan-first (Ley 26) is satisfied by the GSD plan; >1 file -> SDD-OS T2: the plan of record `vault/plans/ucep-naked-verb-2026-10-02.md` is the spec.
- New modules -> PLANNED liveness entry in the same commit (none expected).

## Architectural Responsibility Map
Not a multi-tier app. Ownership per plan of record (`vault/plans/ucep-naked-verb-2026-10-02.md:60-71`): `tower` owns maturity/ratchet/donegate; `gsd_x` consumes (Phase 6). Phase 1 touches only `modules/tower/{ratchet,donegate,baselines}.py`, `tools/family_baseline.py` (message wording), tests, two new generation files, `.gitattributes`.

## Standard Stack
Python 3.12 stdlib only (`json`, `hashlib`, `os`, `re`, `tempfile`); tests are plain scripts (no pytest) [VERIFIED: tools/test_tower_ratchet.py]. No external packages -> no legitimacy audit needed.

## Architecture Patterns / Don't Hand-Roll
- Generations are append-only records published create-if-absent via hard link; never edit one in place; new operations call `bl.write_generation` with `extra={"changes": {...}}` (`ratchet.py:158-161`). Do not write generation JSON by hand in production code or in gates that claim the API works.
- Reuse `ratchet._active/_squash/_need/_recorded`; do not re-implement quote verification (use `bl.verify_origin`).
- Gates pair each refusal with a control in which the same call with the missing fact succeeds (rule: refusal without control is indistinguishable from "refuses everything").

## Common Pitfalls
1. **CRLF anchors** (F0): hash a CRLF file, commit LF -> TAMPERED elsewhere. Normalise first; verify `git ls-files --eol` shows `w/lf`.
2. **Vacuous probe** (F3): never cite probe output for ratchet cases on the real web_surface dir.
3. **Changing `checks.py` outcomes** breaks `V-TCHK-TEST-DELEGATED` (`test_tower_checks.py:129-131`); remap in donegate only.
4. **Free-text N/A in existing tests** (`test_tower_donegate.py:98,121`) must move to the vocabulary or 2 gates go red.
5. **`verify_chain` calling `verify_origin`** would turn future origin rot into chain regressions; keep it write-time.
6. **MOVED is not VERIFIED**: `reanchor` must refuse MOVED/WEAK; the citations gate currently tolerates MOVED.
7. `timeout` wrapper in Git-Bash strips HOME -> spurious `Could not determine home directory` in gsd_x-importing tests.
8. Walker must read `bl.BASELINES_DIR` at call time (tests monkeypatch it, `test_baseline_generations.py:185-191`).
9. Editing shared test files while another session is live: keep edits to the two tuple blocks and the two N/A reason strings; put all new gates in the NEW test file.

## Code Examples (shape only; all names exist as quoted except the new ones marked NEW)
```python
# ratchet.py (NEW) - skeleton, uses only verified helpers
REANCHORED = "REANCHORED"
def reanchor(family, new_origins, reason, authority, root=None):
    _need(reason, authority)                          # ratchet.py:139
    cur = bl.latest(family, root)                     # baselines.py:117
    if not cur or not new_origins: raise RatchetRefusal("nothing to reanchor")
    active, out, changes = _active(cur["entries"]), [], {}
    for e in cur["entries"]:
        new = new_origins.get(e["id"])
        if new is None: out.append(e); continue
        if e["id"] not in active: raise RatchetRefusal("%s is not active" % e["id"])
        cand = dict(e, origin=new)
        if _squash(new.get("quote")) != _squash((e.get("origin") or {}).get("quote")) or not new.get("quote"):
            raise RatchetRefusal("%s: quote must be unchanged and non-empty" % e["id"])
        v = bl.verify_origin(cand)                    # baselines.py:62
        if v != bl.VERIFIED: raise RatchetRefusal("%s: new origin is %s" % (e["id"], v))
        out.append(cand)
        changes[e["id"]] = {"kind": REANCHORED, "reason": reason, "authority": authority,
                            "from": e["origin"], "to": new}
    unknown = set(new_origins) - {e["id"] for e in cur["entries"]}
    if unknown: raise RatchetRefusal("unknown ids %s" % sorted(unknown))
    return bl.write_generation(family, out, "reanchor %s: %s" % (", ".join(sorted(changes)), reason),
                               root=root, extra={"changes": changes})
```

## State of the Art / Assumptions Log
| # | Claim | Section | Risk if wrong |
|---|---|---|---|
| A1 | The Owner's approved plan of record is acceptable as "Owner" authority for the mission's reanchor (authority string starting `Owner`) | F6 | If not, there is no allowlisted authority an agent may cite; reanchor would need an Owner step (BLOCKED) |
| A2 | N/A vocabulary tokens and cap 0.30 | F7 | Wrong cap blocks legitimate N/A; cheap to change, pinned by constants + test |
| A3 | Home-skill path `C:\Users\User\.claude\skills\<skill>\SKILL.md` is an acceptable origin (vs main-checkout tracked path) | F4 | Home copy is untracked and Owner-editable: origin may rot again (the gate will say so) |
| A4 | Fixing CRLF with `.gitattributes` + re-checkout is acceptable (alternative: CRLF-insensitive `generation_sha256`) | F0 | If `.gitattributes` edit is refused, use the code-level normalisation; both pass the same gates |

## Open Questions
1. Should `reanchor` also allow a changed quote (rule text re-worded in the skill)? Recommended NO (refuse; use revert+promote with REWORDED) - none of the 9 needs it.
2. `ok` including `unanchored`: a grandfathered unanchored child would now be non-ok. None exists (checked: only web_surface B1, anchored). Confirm during execution with `verify_chain` on all discovered subjects.
3. Whether the main checkout (other session) is also CRLF-red on `V-TRAT-REAL-CHAINS` - not checked (off-limits); irrelevant to this worktree's result.

## Environment Availability
| Dependency | Available | Version | Note |
|---|---|---|---|
| Python | yes | 3.12 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` | run directly, not under `timeout` |
| git | yes | `C:\Program Files\Git\cmd\git.exe` (autocrlf=true); `/usr/bin/git` has no autocrlf | use the absolute one |
| PowerShell tool | NO in this research session | - | Bash with the `# bash-safe` marker worked; executor may differ |
| rtk proxy | prints "[rtk] No hook installed" noise on stderr | - | harmless |

## Validation Architecture

### Test Framework
| Property | Value |
|---|---|
| Framework | plain Python scripts printing `<NAME>_PASS=n/m threshold=n/m`, exit 0 iff all pass |
| Config file | none |
| Quick run | `python tools/test_ucep_baseline_integrity.py` (NEW, this phase) |
| Full phase suite | the 4 required files + the 5 regression files below |

Python invocation (PowerShell form from the task): `$env:PYTHONIOENCODING='utf-8'; & 'C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe' tools\<file>.py *> $env:TEMP\x.log; $LASTEXITCODE; Get-Content $env:TEMP\x.log -Tail 40`. Failure = non-zero exit OR a `FAIL` line OR `PASS=n/m` with n<m.

### Phase Requirements -> Test Map (UCEP-01)
| Success criterion | Verifying command | Passing output | Failure looks like |
|---|---|---|---|
| 1 reanchor API + 9 entries re-anchored | `tools/test_ucep_baseline_integrity.py` gates `V-UCEP-REANCHOR-*` (one generation, kind REANCHORED, ids kept, refuses MOVED/QUOTE_MISSING/changed quote/empty reason/bad authority; control: VERIFIED origin accepted) + `tools/test_baseline_generations.py` | `BASELINE_GENERATIONS_PASS=16/16`, `V-BGEN-REAL-B0-CITATIONS-HOLD ... holds`; `bl.generations("persistent_state") == [0, 1]` and `["wii_homebrew"] == [0, 1]` | any `FAIL`; `broken={...QUOTE_MISSING}` |
| 2 diff covers why/origin/class/scope; unanchored not ok; allowlist; H1/H2/H3b red, controls green | NEW gates `V-UCEP-H1`, `-H2`, `-H3B` (each built on a synthetic/B0-only family, each with an `-CONTROL` that stays ok) + `tools/test_tower_ratchet.py` | `TOWER_RATCHET_PASS=21/21` (after F0 fix) and new file all PASS; RED proof recorded in EVIDENCE: the same attacks return `ok=True` against the pre-change commit | attack returns `ok=True` after the fix; control returns `ok=False` |
| 3 donegate N/A vocabulary + cap; `test:` UNJUDGED counted separately | NEW gates `V-UCEP-H5` (15 vocabulary-valid N/A over cap -> would_block True, all UNJUDGED; `"n/a"` reason -> UNJUDGED; control: 1 valid N/A within cap -> NOT_APPLICABLE), `V-UCEP-H6` (failing test file -> UNJUDGED, marker file absent, `unjudged_tests` lists it, `violated` count excludes it; control: marker written when file is run by hand), `V-UCEP-NO-EXEC-IMPORTS` + `tools/test_tower_donegate.py` + `tools/test_tower_checks.py` | `TOWER_DONEGATE_PASS=10/10`, `TOWER_CHECKS_PASS=23/23` (unchanged) | `verdict=DELEGATED` for a `test:` check; `would_block=False` with all-N/A |
| 4 discovery walk + floor, no tuple | `V-UCEP-DISCOVER-*` (nested axis found; empty root -> `[]`; tmp residue ignored) + both edited tests | `V-TRAT-REAL-CHAINS ... N subjects` and `V-BGEN-REAL-B0-CITATIONS-HOLD` messages cite discovered counts | a hardcoded tuple remains (`grep "\"web_surface\", \"persistent_state\"" tools/test_tower_ratchet.py tools/test_baseline_generations.py` must return nothing) |
| 5 green + immutability | the 4 required files (see counts) + regression files; sha check: `git hash-object` / LF-normalised sha256 of the 5 pre-existing generation files equals F0 table | all PASS; `git diff --stat HEAD -- vault/tower/baselines/*/B0.json vault/tower/baselines/web_surface/B1.json` empty | any hash differs from the F0 table |

Regression set to run after every change: `test_tower_select` 15/15, `test_tower_checks` 23/23, `test_tower_capsule` 16/16, `test_tower_inheritance` 16/16, `test_family_injection` 23/23, `test_family_baselines` 20/20, `test_tower_o4` exit 0. Ledger hygiene: `test_family_injection` uses a TEMP ledger via hermetic HOME; the new tests must write only under `tempfile` roots and never `~/.claude/state/tower/` (verify by listing that ledger's mtime/row count before and after).

### Sampling Rate
- Per task commit: the NEW file + the single test file for the touched module.
- Per wave: the 4 required + regression set. Bracket every wide run with the sorted dirty-path SET (`git.exe status --short`) before/after; a changed set -> INCONCLUSIVE, not PASS.
- Phase gate: all green + F0 table re-checked + `wiki/tools/cbr_probe.py` NOT used as evidence for ratchet cases (F3); H5/H6 probe lines should flip (`would_block=True {'UNJUDGED': 17}`; `verdict=UNJUDGED`) and may be quoted as a secondary observation.

### Wave 0 Gaps
- [ ] `tools/test_ucep_baseline_integrity.py` (NEW) - all V-UCEP-* gates above, RED first against unchanged code.
- [ ] Line-ending normalisation (`.gitattributes` line + re-checkout) before any generation write; pre-check `git ls-files --eol` -> `w/lf`.
- [ ] Record F0 sha table (blob form) at start; recompute at end.

## Security Domain
`security_enforcement` not set in `.planning/config.json` (treated enabled). Phase is local, stdlib, no network/auth/crypto-of-secrets. Applicable: V5 input validation (reanchor origin dict shape, vocabulary parse, path handling: `verify_origin` reads arbitrary absolute paths - restrict nothing new but never follow reanchor to a path under `.claude/worktrees/` [audit G15]); V6 hashing = `hashlib.sha256` for anchors (no hand-rolled crypto). Threat patterns: authority forgery via free-text string (closed by allowlist; residual: allowlist is code, a forger with write access to `ratchet.py` wins - repo history is the root of trust); laundering provenance via origin rewrite (closed by diff + same-quote rule); gate gaming via N/A (closed by vocabulary + cap); executing untrusted test files from a hook path (closed: never executed, pinned by import scan + marker gate). Secrets: none handled.

## Sources
Primary (read this session): `modules/tower/{ratchet,baselines,donegate,checks}.py`; `tools/test_{tower_ratchet,baseline_generations,tower_donegate,family_injection}.py`; `tools/family_baseline.py:95-160`; `wiki/tools/cbr_probe.py`; `wiki/syntheses/cbr-gap-analysis.md`; `vault/plans/ucep-naked-verb-2026-10-02{,.audit}.md`; ROADMAP/REQUIREMENTS/CONTEXT; `vault/tower/baselines/**`; `.gitattributes`; `vault/liveness/reachability_registry.json`. Executed this session: the 9 test files listed in F1, the probe, a B0-only H1/H2/H3b reproduction, sha256/EOL measurements, quote lookups in the three SKILL.md files.

## Metadata
**Confidence:** HIGH for code facts, hashes, citations and baseline counts (all read/run); MEDIUM for chosen vocabulary/cap/authority shape (design discretion, tagged ASSUMED).
**Research date:** 2026-10-02. **Valid until:** until `modules/tower/*` or the baseline files change (re-run F0 hashes and F1 counts first).
