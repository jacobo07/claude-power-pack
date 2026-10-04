---
phase: 06-consume-owners-and-close
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - tools/ic_r2_evidence.py
  - tools/test_ic_closeout.py
  - tools/test_ic_r2_evidence.py
  - tools/test_incremental_cognition_program.py
  - tools/test_kme_replay.py
findings:
  critical: 0
  warning: 9
  info: 5
  total: 14
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-10-04
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed `ic_r2_evidence.py`, `test_ic_r2_evidence.py` and `test_ic_closeout.py` whole, and the `594745b6..HEAD` hunks of
`test_incremental_cognition_program.py` and `test_kme_replay.py`.

Observed on this worktree: `test_ic_r2_evidence.py` 14/14, `--drill` killed 6/6, `test_ic_closeout.py` 11/11, the icp selftest R2
gates `ok`. The printer itself holds the stated invariants. It is read-only, it prints rows only when every consumed pair
has a terminal and the commit is an ancestor of HEAD, and it prints the full 40-hex sha. No partial or abbreviated
`owner_ledger` row is reachable through the code paths the gates drive. The icp hunks (`only=` scoping, R2 in `--pillar` mode)
and the kme_replay glob change are correct.

The defects found are at the edges. The printer accepts terminals it never validates. Its exit-code contract can be
broken by a traceback. Several closeout checks can be bypassed by path spelling. A few gates are time-bombed or
environment-sensitive. No finding reaches BLOCKER: nothing here produces a wrong paste on the happy path or loses data.

## Warnings

### WR-01: Printer emits a READY row for an unvalidated owner terminal (empty string, non-string, non-terminal name)

**File:** `tools/ic_r2_evidence.py:89-97`
**Issue:** `terminal = owners.terminal_at(...)` is tested only with `terminal is None`. An owner ledger holding
`"terminal": ""`, `0`, `false`, `{}` or a typo such as `"DONE"` (not in `ce.TERMINALS`) is reported `READY` and printed as a
pasteable `owner_ledger` row. The round-trip does not catch it, because R2 (`check_consumed`) also compares only `got is None`
and `got != claimed`, so a row with the same junk value matches itself. The value is a free string pasted into the
ledger as consumed-owner evidence. A falsy or unknown terminal is not "the owner pillar is closed".
**Fix:**
```python
terminal = owners.terminal_at(sha, ref, pillar)
if terminal is None:
    ...OPEN...
elif terminal not in ce.TERMINALS:      # str membership; also rejects "", 0, {}
    lines.append(f"OPEN {ref}#{pillar} at {short}: terminal {terminal!r} is not a known terminal")
    flags.append(False); continue
```
Add a scratch gate (and a drill mutant) where the owner ledger carries `""` / an unknown name and no row is printed.

### WR-02: A malformed ledger raises an uncaught AttributeError, and the traceback exit code (1) collides with "not ready"

**File:** `tools/ic_r2_evidence.py:33-36, 145-154`
**Issue:** The documented contract is exit 2 = could not run, 1 = not ready. `main` catches only
`(KeyError, TypeError)` around `consumed()`. A ledger that parses as JSON but has the wrong shape raises `AttributeError`.
Examples: top level is a list, so `led.get` fails; or a `consumes[pid]` entry is a string, so `w.get` fails. The uncaught traceback
makes Python exit 1, so a caller or a bundle reader sees "not ready, wait for the owner" rather than "the printer could not run".
The same applies inside `predicted_at` (`frozen` or `pillars` of the wrong type, line 65) when an owner ledger at an old
commit is oddly shaped.
**Fix:** Catch `(KeyError, TypeError, AttributeError)` in `main`, or validate shape in `consumed()` and return a typed
error. Wrap the `owner_rows` call and map any unexpected exception to `ICR2_COULD_NOT_RUN` with exit 2. In `predicted_at`,
guard `isinstance(frozen, dict)` and `isinstance(pillars, list)`.

### WR-03: V-ICR2-TRACER-REAL-HEAD becomes permanently red once the owner closes D, E and I

**File:** `tools/test_ic_r2_evidence.py:131-137`
**Issue:** The gate runs the printer on the real HEAD and requires `rc == 1`, three `OPEN ... no terminal` lines and
`ICR2_READY=NO`. That is true only while the CE ledger on this line of history is open. The program's success state (the owner
pillars closed and merged into this history) is exactly the state that makes this gate FAIL. The tool exists to produce the
ready output, yet its own gate asserts the not-ready one. `--drill` also drops this gate (`DRILL_GATES`), so it is the only
real-HEAD check.
**Fix:** Derive the expectation from independent reads (as `g_real_freeze_pole` does with `predicted_by_owner`). Assert that the
printer's verdict agrees with what `git show HEAD:<owner ledger>` says: `rc == 0` and rows iff all pairs have a terminal,
otherwise OPEN lines. Do not hardcode D, E and I as open.

### WR-04: Evidence and ref resolution accept a directory as "a file at HEAD"

**File:** `tools/test_ic_closeout.py:120-122, 136-141, 262-264, 897-899`
**Issue:** `blob_at()` treats `git show HEAD:<path>` returncode 0 as success. For a directory, `git show` prints a tree
listing with rc 0 (observed: `git show HEAD:tools` returns `tree HEAD:tools ...`, rc=0). So `ref_resolves("tools")` and a delta
evidence item `{"ref": "tools", "sha256": <sha of the listing>}` both pass as "resolves / is a file at HEAD". The error text
"is not a file at HEAD" is therefore false for directories. The line-count check is applied to the tree text.
**Fix:** Resolve with `git cat-file -t HEAD:<path>` and require `blob`, or use `git cat-file blob HEAD:<path>` in
`blob_at`. Add a control: a directory ref is refused.

### WR-05: The smoke-measurement label rule is bypassed by `./`-prefixed evidence refs

**File:** `tools/test_ic_closeout.py:896-904`
**Issue:** The rule fires only when `ref.startswith(f"{PROG}/measurements/")`. `blob_at("HEAD", ref)` accepts
`./vault/programs/incremental-cognition/measurements/L-KME-G-....md` (observed: `git show HEAD:./tools/ic_r2_evidence.py`
resolves relative to the repo root because of `-C`). That spelling resolves to the same smoke file, but does not match the
`startswith`, so a statement that never says "smoke" passes. The gate pins "never say a smoke measurement is a measurement",
and a different spelling defeats it. This is the same identity-by-spelling class that R4 in icp handles with `samefile`.
**Fix:** Normalize before comparing: `ref = posixpath.normpath(ref)`, and refuse any ref that is absolute, starts with `..`
or contains `//`. Better, require `ref == posixpath.normpath(ref)` as a shape check. Add a control for `./`-prefixed refs.

### WR-06: Domain-candidate target check is bypassable with `..` segments

**File:** `tools/test_ic_closeout.py:225-232`
**Issue:** For D-level candidates the target is accepted when `tgt.startswith("vault/knowledge_base/")`, the file exists on
disk and `git ls-files --error-unmatch` succeeds. `vault/knowledge_base/../../CLAUDE.md` satisfies all three. `git ls-files`
normalizes the path and returns rc 0 (observed), and `(REPO / rel).is_file()` resolves it. So a "domain" candidate can
target any tracked file in the repo, including CLAUDE.md or a governance file.
**Fix:** Reject any target where `posixpath.normpath(tgt) != tgt` or `".." in tgt.split("/")`, as `ref_resolves` already does for evidence paths.

### WR-07: V-ICR2-READ-ONLY compares whole-repo state and will false-FAIL under any concurrent writer

**File:** `tools/test_ic_r2_evidence.py:383-404`
**Issue:** The snapshot includes the entire `git status --porcelain`, `git rev-parse HEAD` and `git for-each-ref`. Any other process
touching the tree or refs during the 8 in-process runs changes the snapshot. That includes another session committing,
or a doc-generating hook writing untracked `docs/**` files. This worktree's own git status shows such untracked files appearing
spontaneously. The gate then reports FAIL ("changed=['status']") for a printer that wrote nothing. Per the shared-tree doctrine,
a wide oracle whose dirty set moved is INCONCLUSIVE, not FAIL.
**Fix:** Narrow the oracle to what the printer could touch: the three ledger hashes, the `.git/index` bytes and the refs. Return
`"INCONCLUSIVE"` when the only differing key is `status` and the diff is confined to untracked paths the printer cannot have
written. Alternatively run the printer in a subprocess against a scratch clone and diff that.

### WR-08: V-ICR2-JM-BLOCKED-COVERS accepts a hand-typed "measured" line; it never re-derives it

**File:** `tools/test_ic_r2_evidence.py:505-518` (evidence file `vault/programs/incremental-cognition/evidence/JM-blocked.md:81,93,154,166`)
**Issue:** The check is `any(line.startswith("ICR2_READY=NO pillar=J "))`. The control only proves the text is searched for. It does not
check that the quoted `commit=` is a reachable commit, nor that the owner ledger at that commit really has the quoted open set.
A fabricated line passes. The file's claim is that these lines are "measured". It also stays "OPEN" forever with no link to
the current printer output.
**Fix:** Parse `commit=<sha> open=[...]` from each line. For each, require the commit to be reachable and re-run the printer
(`ev.main(["--pillar", pid, "--commit", sha])`) in the gate, comparing the open list. This is cheap, as the gate already runs the printer in-process elsewhere.

### WR-09: Controls are silently omitted, and the drill has no mutant for several gates

**File:** `tools/test_ic_closeout.py:1000-1002, 1032-1036, 592; 1185-1198`
**Issue:**
(a) `peer = _full_sha("5cdd7d9f")` and `foreign_phase = _full_sha(...)` add their controls only when the commit exists in the
clone. In a clone without them the gate still prints PASS with fewer controls. These are the only controls that drive the
integrated `commit_subject` / `commit_paths` path against real foreign commits. They should SKIP or INCONCLUSIVE, not vanish.
(b) The control `commit:21671d6c is refused` assumes that commit is absent from every clone. Fetching it flips the gate red.
(c) `MUTANTS` has no mutant for `duplicate_problems` (V-ICN-DUPLICATE-CITED) or `bundle_n_problems` (V-ICN-BUNDLE-N), so the
drill cannot show that those gates' controls bite. The printer's drill likewise has no mutant for `resolve_commit` (the `-x` guard) or the `terminal is None` branch.
**Fix:** Return `"INCONCLUSIVE"` naming the missing control commits. Build the "absent commit" control from a synthetic 40-hex that cannot exist.
Add `_without(duplicate_problems, "no such id")`, `_without(bundle_n_problems, "exactly one")` and a `resolve_commit` mutant, each with its targeted gate.

## Info

### IN-01: Literal BOM character inside a string in source

**File:** `tools/ic_r2_evidence.py:60`; `tools/test_ic_r2_evidence.py:98`
**Issue:** `lstrip("<U+FEFF>")` embeds an invisible U+FEFF in the source (the injection scanner flagged both files). It is easily lost by
an editor or formatter, and then BOM-prefixed ledgers fail to parse.
**Fix:** Write it as `"﻿"`.

### IN-02: `full_commit` is an identity function that exists only as a mutation seam

**File:** `tools/ic_r2_evidence.py:49-51`
**Issue:** Production code carries a no-op indirection for the drill's benefit. Harmless, but it reads as dead code.
**Fix:** Keep it, but state the purpose in the docstring ("seam for V-ICR2 drill M3"), or assert `len(sha) == 40` there so it does something.

### IN-03: `open=` list is ambiguous when two ledgers share a pillar letter, and an empty `consumes[pid]` yields an unexplained NO

**File:** `tools/ic_r2_evidence.py:137-138, 175`
**Issue:** For pillar I (CE B and SC B) the summary prints `open=['B', 'B']` (visible in `JM-blocked.md:222`). A consumes list
that is empty prints `ICR2_READY=NO ... open=[]` and exits 1 forever with no reason.
**Fix:** Print `open=['<ledger>#B', ...]` and add an explicit `ICR2_COULD_NOT_RUN pillar X consumes an empty list` (exit 2).

### IN-04: V-ICR2-SEAM-RESTORED greps source text for `setattr` / `REPO =`

**File:** `tools/test_ic_r2_evidence.py:377-379`
**Issue:** A substring scan is a weak proxy for "the helper does not rebind a REPO global" (`globals()["REPO"] = ...` or
`ce.__dict__.update` pass). It is a useful tripwire, but not a proof.
**Fix:** Add an AST walk for assignments to attributes named `REPO` and to `globals()`, or state in the gate evidence that it is a tripwire.

### IN-05: Scratch gates are coupled to the real program ledger's J consumption

**File:** `tools/test_ic_r2_evidence.py:197, 248-251, 293-296`
**Issue:** `PAIRS` and `CE_LEDGER` are hardcoded as D, E, I. `scratch_main` runs the printer with the real program ledger. If J's frozen
`consumes` is ever revised, all scratch gates fail for a reason unrelated to the printer.
**Fix:** Build `PAIRS` from `program_ledger()["frozen"]["consumes"]["J"]`, or pass a synthetic program ledger through a ledger-path parameter.

---

_Reviewed: 2026-10-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
