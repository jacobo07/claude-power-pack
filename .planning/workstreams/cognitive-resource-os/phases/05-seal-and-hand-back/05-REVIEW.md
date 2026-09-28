---
phase: 05-seal-and-hand-back
reviewed: 2026-09-28T00:00:00Z
depth: deep
files_reviewed: 1
files_reviewed_list:
  - .planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py
findings:
  critical: 3
  warning: 4
  info: 0
  total: 7
status: issues_found
---

# Phase 05 (seal-and-hand-back): Code Review Report

**Reviewed:** 2026-09-28
**Depth:** deep (full read of `seal_check.py`; `--selftest` run and observed 9/9; every finding below
reproduced live against a temporary fixture tree built from the module's own `_build_fixture()`/
`_FIXTURE_RES` helpers, or against the real committed vault files, using `check_content()` /
`lost_tokens()` / `bullets()` / `ukdl_entries()` called directly — not asserted from reading alone)
**Files Reviewed:** 1
**Status:** issues_found

## Summary

`seal_check.py` passes its own 9-case selftest (`SEALCHK_SELFTEST_PASS=9/9`) and `content --stage 4`
against the real committed RESUMPTION/UKDL/EVIDENCE files. That selftest, however, only fixture-tests
the *happy path plus one word-deletion / one missing-heading / one gate-flip per case* — it never
constructs the adversarial shapes (duplicated headings/IDs, a false headline verdict with the true
token buried elsewhere, a whole deleted sentence whose words survive elsewhere) that the checker is
supposed to guard against. Three of those shapes are provably exploitable right now, using nothing but
the checker's own public functions and fixture builder — they are not hypothetical. All three let a
false or invented claim survive every `content`/`preserve` check with **zero** reported problems. A
fourth class of findings would make the checker fail (or silently under-check) on legitimate,
correctly-labeled content.

## Critical Issues

### CR-01: Verdict/extra-key checks are unanchored substring tests, not headline-claim checks

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:487-489, 611-619, 681-689`
**Issue:** Every place the checker verifies a "verdict token" (phase bullets in RESUMPTION 2d, the
Phase 3 tracer bullet, the UKDL "GEX44 run" paragraph, and the `EXTRA_KEYS` values like
`gates_verdict`/`suite_verdict`/`rule_fired`) does it with a bare `token not in bn` / `tok not in para`
substring test against the *entire* bullet or paragraph text, e.g.:
```python
token = verdict_line.split(":", 1)[1].strip().split()[0] if verdict_line else None
if not token or token not in bn:
    problems.append(f"Phase {n} bullet missing verdict token")
```
This only proves the token's characters appear *somewhere* in the block — not that the bullet's actual
headline claim states that verdict. Since a phase's `EXTRA_KEYS` and `phase_verdict` are frequently the
same small vocabulary (`PASS`/`BLOCKED`/`MEASURED`/`UNJUDGED`), a bullet whose headline asserts the
**wrong** verdict still passes as long as the real token is quoted anywhere else in the same
block (e.g., a parenthetical raw-field dump, or a negation like "nothing is BLOCKED"). Reproduced live:
```python
# real ev1 fixture: phase_verdict: BLOCKED, gates_verdict: PASS, suite_verdict: BLOCKED
old = "- Phase 1 (CRO-01) -- BLOCKED gates_verdict PASS suite_verdict BLOCKED"
new = ("- Phase 1 (CRO-01) -- PASS, all gates cleared and nothing is BLOCKED. "
       "(raw fields: gates_verdict PASS suite_verdict BLOCKED)")
# check_content(root, 2) -> []   <-- zero problems, despite the false PASS headline
```
This is exactly the "verdict-token equality" failure mode the checker exists to prevent: a bullet can
claim the opposite of what its own EVIDENCE says and still be sealed clean.
**Fix:** Anchor the check to the actual verdict clause instead of the whole block, e.g. require the
bullet to start with `- Phase N (CRO-0N) -- {token}` (a regex anchored at the start of the bullet,
matching the plan's own documented format `- Phase 3 (CRO-03) -- PASS ...`), rather than testing
substring containment over arbitrary trailing prose:
```python
head = bn.splitlines()[0]
if not re.match(rf"^- Phase {n} \(CRO-0{n}\) -- {re.escape(token)}\b", head):
    problems.append(f"Phase {n} bullet headline verdict != EVIDENCE token")
```
Apply the same anchoring to the UKDL "GEX44 run" paragraph and to `EXTRA_KEYS`.

### CR-02: `bullets()` / `ukdl_entries()` key by ID in a plain dict — an earlier duplicate is silently dropped from every check, but stays in the committed file

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:243-267 (bullets, `result[phase] = ...` at 263), 270-293 (ukdl_entries, `result[eid] = ...` at 289)`
**Issue:** Both parsers build `{key: paragraph_text}` and overwrite on repeat keys, keeping only the
**last** occurrence. `check_content()` only ever iterates `entries.items()` / `res_bullets.get(n)`, i.e.
only the surviving (last) paragraph. If a document contains two blocks with the same phase number / UKDL
ID — e.g. a fabricated block immediately followed by a correctly-formatted legitimate one — the
fabricated block is invisible to every content check (verdict, citation, figure-provenance, "unplanned
ID") while remaining physically present and committed in the file. Reproduced live, twice:
```python
# RESUMPTION: insert a fabricated duplicate bullet right before the real Phase 3 bullet
fake = "- Phase 3 (CRO-03) -- INVENTED: 99.99% reuse, no EVIDENCE cited, no GEX44 label, totally fabricated.\n"
text = text.replace(marker, fake + marker)
# check_content(root, 1) -> []   <-- the fabricated bullet is never checked

# UKDL: insert a fabricated duplicate entry right before the real T-RULE-EXCLUSION-SCOPE-001
fake = ("**`T-RULE-EXCLUSION-SCOPE-001`** -- GEX44 claims 99.99% coverage with zero citation "
        "and an invented $1,000,000 figure, no evidence path at all.\n")
text = text.replace(marker, fake + marker)
# check_content(root, 1) -> []   <-- the invented $1,000,000, uncited paragraph is never checked
```
Both cases print `content OK`-equivalent (empty problem list) while the fabricated block ships in the
committed vault file. This directly defeats the "closed UKDL ID set" and "verdict-token equality"
guarantees the plan advertises (`vault/knowledge_base/ukdl-cognitive-resource-os.md` gets "only the
entries planned here" / "none invented").
**Fix:** Make both parsers fail loudly on a repeated key instead of silently overwriting, e.g. in
`bullets()`/`ukdl_entries()`:
```python
if phase in result:          # or: if eid in result
    raise ValueError(f"duplicate block for {phase!r}")
```
or collect a list per key and have `check_content` add a "duplicate {id}" problem when `len(list) != 1`,
mirroring the exact-count-1 pattern already used elsewhere in the file (e.g. `_heading_count(...) != 1`).

### CR-03: `lost_tokens()` is a word-**set** difference, not a word/line **multiset** — an entire original sentence can be deleted undetected

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:158-170`
**Issue:**
```python
def lost_tokens(orig: str, new: str) -> list:
    o = set(norm_tokens(orig))
    n = set(norm_tokens(new))
    return sorted(o - n)
```
`preserve` mode's entire "no lost line" guarantee rests on this function. Because it is a set (not
multiset/positional) comparison, it only detects a word that is completely absent from the *whole* new
document — it cannot detect that a specific sentence/line was deleted if every word that sentence used
also happens to occur anywhere else in the (thousands-of-words) document, which is the common case for
short filler or cross-referencing sentences built from words ("the", "GEX44", "laptop", figures already
quoted elsewhere, etc.) that recur throughout RESUMPTION/UKDL. Reproduced live:
```python
orig = ("The pytest suite passed 25 of 25 cases on the laptop host today.\n"
        "Passed today, the laptop host suite of 25 on 25 cases the pytest.")
new  =  "The pytest suite passed 25 of 25 cases on the laptop host today."
lost_tokens(orig, new)   # -> []   <-- the entire second sentence is gone, zero words reported lost
```
This is the exact "lost line" failure mode named in this review's brief: a whole clause of the cd4e436
original can be deleted from RESUMPTION/UKDL and `preserve <which> --stage N` will still print `OK`.
**Fix:** Compare at line/sentence granularity in addition to (or instead of) the word set, e.g. require
every non-empty line of `orig` to survive as a normalized-token multiset subset check against some
contiguous span of `new`, or at minimum switch to `collections.Counter` so a word's *count* — not just
presence — must be preserved:
```python
from collections import Counter
o, n = Counter(norm_tokens(orig)), Counter(norm_tokens(new))
lost = sorted((o - n).elements())   # words whose count dropped, not just words that vanished entirely
```
Counter-based counting alone still would not catch this specific synthetic case (a full permutation of
the same multiset), so a genuine fix needs a line-level check: each original non-blank line's normalized
token sequence (or a sufficiently large n-gram of it) must appear as a contiguous run somewhere in `new`,
not just have its words individually present somewhere.

## Warnings

### WR-01: The unlabelled-figure check is per physical line, not per logical bullet — fragile to the file's own documented line-wrapping style

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:656-660`
**Issue:**
```python
for heading in ("## 1a.", "## 2c.", "## 2d.", "## 2e.", "## 4."):
    sec = section(res_text, heading) or ""
    for line in sec.splitlines():
        if figures(line) and "GEX44" not in line and "laptop" not in line.lower():
            problems.append(f"unlabelled figure line under {heading}: {line[:60]}")
```
This requires "GEX44" or "laptop" on the *same physical line* as a figure. The plan explicitly allows
(and the real committed RESUMPTION 2d Phase 3 bullet actually uses) multi-line wrapped bullets — e.g.
lines 73-78 of the real `vault/plans/cognitive-resource-os-RESUMPTION.md` wrap one bullet across six
physical lines, with "GEX44." landing on the last line. The current real content happens not to place a
figure on an unlabelled wrapped line, so `content --stage 4` passes today, but this is incidental: any
future edit that wraps a figure onto a line whose "GEX44"/"laptop" label falls on the next physical line
would spuriously fail a fully-correct, fully-labeled sentence.
**Fix:** Check per-bullet (the block already captured by `bullets()`/`section()`) rather than per
physical line, e.g. verify each figure occurs within N characters of a GEX44/laptop mention in the
joined (whitespace-collapsed) bullet text, not that they share a `splitlines()` line.

### WR-02: `_stage_arg()` silently falls back to the weakest stage on any malformed `--stage` argument

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:1212-1219`
**Issue:**
```python
def _stage_arg(rest) -> int:
    if "--stage" in rest:
        i = rest.index("--stage")
        try:
            return int(rest[i + 1])
        except (IndexError, ValueError):
            return 1
    return 1
```
A missing `--stage`, a typo'd flag (e.g. `--stag 4`, `--stage=4`), or a non-integer value all silently
resolve to `stage=1` — the weakest check tier — with no warning printed, and the process still exits 0
on success. A harness/CI typo in one of the plan's own verify commands (which are hand-spelled shell
strings, not driven by a single source of truth) would silently downgrade validation from stage 4 to
stage 1 and still report `content OK`.
**Fix:** Treat a present-but-unparseable `--stage` value as a hard error (`sys.exit` with a clear
message) rather than defaulting; only a wholly absent `--stage` should default (and arguably should also
be an error, since every documented call site always passes it explicitly).

### WR-03: `classify_status()`'s TRACKING allowlist ignores the git status code — a deleted/renamed tracked file is treated the same as a benign edit

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:344-372`
**Issue:** The loop only inspects `path` (the tail of the porcelain line) against `TRACKING`/
`ALLOWED_UNTRACKED`; it never looks at the two-character status code (`XY`) at the start of the line.
A staged deletion of `STATE.md` (` D .../STATE.md`), or a rename that moves it out from under
`.planning/workstreams/cognitive-resource-os/` (`R  .../STATE.md -> elsewhere`, whose post-arrow path
would then miss the allowlist and correctly fall to `dirty` — but a rename *into* the tracked path, or
any other same-path status combination such as a conflicted merge marker `UU`, is accepted identically
to a routine ` M` edit. `status` mode would print `final_status: TRACKING_ONLY (...)` and exit 0 for a
deletion of a workstream-owned planning file, which is a materially different, more severe event than
the "orchestrator is mid-edit on STATE.md" case this allowlist was designed for.
**Fix:** Restrict the TRACKING allowlist to specific, expected status codes (e.g. ` M`/`M `/`MM`) and
classify anything else touching a TRACKING path (deletion, rename, unmerged) as `dirty`.

### WR-04: `key_line()` returns only the first match — a duplicated/forged key line later in the file is never inspected

**File:** `.planning/workstreams/cognitive-resource-os/phases/05-seal-and-hand-back/seal_check.py:319-322`
**Issue:**
```python
def key_line(text: str, key: str):
    pat = re.compile(r"^" + re.escape(key) + r":\s.*$", re.MULTILINE)
    m = pat.search(text)
    return m.group(0) if m else None
```
`.search()` returns the first match only. Every equality check built on `key_line` (e.g.
`pN_verdict_line`, `base_commit`, `cro05`, `final_status`) is therefore blind to a second, contradictory
occurrence of the same key appended later in the same file (whether by accident from a bad merge/edit, or
adversarially). The same root cause as CR-02 (first/last-match-wins parsing hides a duplicate), applied
to `EVIDENCE.md`'s own key: value lines rather than to bullets/UKDL-entries.
**Fix:** Assert single-match — raise or record a problem when `len(pat.findall(text)) > 1` — rather than
silently taking the first.

---

_Reviewed: 2026-09-28_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_

## Orchestrator disposition (2026-09-28)

Not auto-fixed in this run. The findings are about what `seal_check.py` would fail to catch under an
adversarial or careless future edit; none claims a defect in the committed RESUMPTION/UKDL content.

- Content was checked independently of seal_check.py: 05-VERIFICATION.md (commit 828f2ed, status passed)
  re-read both vault files cold and matched every verdict and figure against phases 1-4's own
  EVIDENCE/VERIFICATION/REVIEW files, and reviewed `git diff cd4e436` line by line.
- CR-02's practical failure mode (a duplicate block shadowing the checked one) was probed directly on the
  committed files: exactly one `- Phase N (CRO-0N)` bullet per phase in RESUMPTION, and every UKDL entry ID
  occurs exactly once.
- Status: OPEN. seal_check.py is a phase-local helper; before anyone relies on it as a gate for a future
  edit, fix CR-01 (anchor the verdict to the bullet headline), CR-02/WR-04 (reject duplicate keys),
  CR-03 (line/multiset preservation), WR-02 (reject a bad --stage), WR-03 (status code aware), WR-01.
