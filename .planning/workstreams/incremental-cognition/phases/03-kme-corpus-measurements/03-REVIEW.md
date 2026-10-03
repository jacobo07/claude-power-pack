---
phase: 03-kme-corpus-measurements
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - wiki/tools/kme_pillars.py
  - wiki/tools/kme_token_audit.py
  - tools/test_kme_pillars.py
  - tools/test_incremental_cognition_program.py
findings:
  critical: 0
  warning: 7
  info: 2
  total: 9
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Review was cut short and written early at the coordinator's request. Coverage:

- `wiki/tools/kme_pillars.py`: read in full (all 2129 lines).
- `wiki/tools/kme_token_audit.py` diff hunks and `tools/test_incremental_cognition_program.py` diff hunks: read in full. The audit hunks are additive, and the `finish_session` extraction is a verbatim move. I found no defect there. I did NOT re-run the byte-identity gate myself.
- `tools/test_kme_pillars.py` (2466 lines): only skimmed (grep plus a few sections). It is NOT fully reviewed.

Verified from the frozen file: the KME-L weighted denominator recomputed from its fields is 1,764,247,687, matching the frozen figure. Interval ordering lo <= hi holds for D, E, F, G (`hi = max(hi, lo)`), H and I. Materiality maps UNMEASURED to its own verdict, never to "< 3 %". Chars, tokens and weighted cost are kept in separate units (chars are converted at 3.0..4.5 chars per token, and I and G use measured usage).

No BLOCKER was proven. WR-01 and WR-02 were confirmed by running the instrument. The rest are confirmed by reading code and are marked "by reading".

## Warnings

### WR-01: `--out-dir` may point inside a scanned corpus root (instrument writes into the corpus)

**File:** `wiki/tools/kme_pillars.py:1852-1934` (`_prepare`, no check), `:2113-2118` (`main`, `mkdir(parents=True)` plus write)
**Issue:** Nothing refuses an `--out-dir` that resolves inside any `--root`. Focus item 4 says the instrument must never write into the scanned roots. Confirmed by running: `h --denominator OTHER --label FX-A --root /tmp/rv/projects/-home-x-kme-p --out-dir /tmp/rv/projects/-home-x-kme-p/out` created `.../-home-x-kme-p/out/H-FX-A-2026-10-03.md` inside the project dir, with exit 0. The gate `g_read_only` (`tools/test_kme_pillars.py:654`) only exercises an `--out-dir` outside the root, so this is unpinned. Pointing it at `/home/kobii/a5-env/home/.claude/projects/...` would write into a read-only env tree.
**Fix:** In `_prepare`, resolve `os.path.realpath(out_dir)` (default included) and each `os.path.realpath(root)`. Refuse with `_fail` when `os.path.commonpath([out, root]) == root`, or when the root is inside out_dir. Add a V-KMEP gate with an out-dir inside a root that asserts rc 2 and no file written.

### WR-02: `cmd_signature` writes a verbatim second token (including URLs) into the measurement file; redaction is pattern-only

**File:** `wiki/tools/kme_pillars.py:1275-1287` (`cmd_signature`), rendered at `:1657-1659` and in the json block
**Issue:** The second token is kept when `re.search(r"[./]", tok)` matches and it fits `[A-Za-z0-9./:_-]{1,80}`. A command like `curl https://api.example.com/verify/<token-in-path>` (the `\bverify\b` alternative in `VERIFY_CMD_RE` selects it, and `curl` is not in `NON_RUN_PROGRAMS`) produced the signature `curl https://api.example.com/verify/ghp1234567890abcdefghijklmnopqrstuv`. I confirmed by running that this string was written to the measurement file. The only protection is `redact()`, which did not fire on this token. It is a made-up string without a real provider prefix format, so a real key shape may be caught. Still, the design goal (focus item 5) is that measurement files carry no transcript content. The doc comment ("never flags, values or arguments") is not true for URL or path arguments.
**Fix:** Keep the second token only if it contains no `:` or `//` and matches a bounded script or subcommand shape, such as `^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$` limited to about 40 chars with no long mixed-case runs of 20 or more. Otherwise drop it. Add a test with a URL-with-token command asserting the token is absent.

### WR-03: R3 fails open when kme_pillars front matter is absent or unparsable

**File:** `tools/test_incremental_cognition_program.py` (`check_measurement_scope`, the `continue  # another instrument's measurement` branch, line 198; `front_matter_fields` at line 162)
**Issue:** (by reading; BOM case not run) A file with neither `evidence_role` nor `terminal_evidence` is skipped and left to the CE clauses. Those clauses (`tools/test_cognitive_economy_program.py` L4, about lines 296-302) only require that the text contains some frozen-denominator name and `command:`. A KME-G smoke file's own front matter already contains `rule_denominators: ["KME-L", ...]`, so it satisfies L4 trivially, which is why R3 exists. Two ways to land in the skip branch:
1. `front_matter_fields` requires `lines[0].strip() == "---"`, and `Resolver.file_text` reads with plain `utf-8`. A UTF-8 BOM (for example a Windows PowerShell 5.1 re-save on the laptop where KME-L runs) makes line 0 `"---"`, so the front matter is empty.
2. Any hand edit of the two key lines.
Either way the smoke file is treated as another instrument's measurement.
**Fix:** In `front_matter_fields`, strip a leading ``. In `check_measurement_scope`, do not skip when the text contains `"instrument": "wiki/tools/kme_pillars.py"` or the `<!-- kmep-json -->` marker. Treat that as an R3 failure ("kme_pillars file without role fields").

### WR-04: R3 never requires a terminal-bearing D..I pillar to cite a primary file, and trusts the file's self-declared `terminal_evidence`

**File:** `tools/test_incremental_cognition_program.py` (`check_measurement_scope`; it never reads `st.get("terminal")`), `:front_matter` consumption of `terminal_evidence`
**Issue:** (by reading) R3 only judges the kme_pillars files that happen to be cited. A pillar D..I whose ledger state has a terminal but cites zero kme_pillars measurement files, such as a hand-written `KME-G ... command:` md, returns `[]`. A KME-G smoke file is therefore substitutable for KME-L through that route. R3 also never cross-checks the file against itself: a file with `terminal_evidence: true` plus `denominator: "KME-G"`, `evidence_role: "primary"`, or `population_match: "drifted"` passes. The text of the check is "the mechanical form of never substitute KME-G for KME-L", but it only holds for honestly generated files.
**Fix:** For pillars in D..I with a terminal, require at least one cited file with `instrument == wiki/tools/kme_pillars.py`, `evidence_role == primary`, `terminal_evidence is True`, `denominator in rule_denominators`, and `population_match in ("exact", "referenced")`. Add a drill for each contradiction.

### WR-05: `second_workload_valid` ignores the materiality verdict; R3 accepts a second workload that is UNMEASURED or "< 3 %"

**File:** `wiki/tools/kme_pillars.py:2038` (`sw_valid = full or match == "not_frozen" ...`); `tools/test_incremental_cognition_program.py` (`check_measurement_scope`, the `role == "second_workload"` branch at line 212)
**Issue:** (by reading) Frozen rule E says "confirmed on a second workload". `sw_valid` is True whenever the population is exact or the workload is not frozen. It stays True when `materiality` is `UNMEASURED` (low observability, empty denominator) or `< 3 %`. R3 then accepts that file next to any primary file. An UNMEASURED run is not a confirmation. For a named workload (`not_frozen`), `sw_valid` is True even when no share could be judged.
**Fix:** `sw_valid = (full or match == "not_frozen") and verdict in (">= 3 %", "STRADDLES")`, or have R3 also require `materiality in (">= 3 %", "STRADDLES")` for a second_workload file. If "< 3 %" on the second workload should count as disconfirmation, record that explicitly.

### WR-06: Referenced CPP-D-W7 share divides a measured numerator by the frozen denominator when coverage > 1

**File:** `wiki/tools/kme_pillars.py:2009-2012` (share vs `wf`), `:2021-2023` (`cov_ok`, `full`, `terminal`)
**Issue:** (by reading; not run) For `kind == "referenced"`, `share = [wlo / wf, whi / wf]`, with `wf` taken from the CE ledger. The numerator comes from the measured population. When `measured calls / frozen calls > 1` (extra projects in `--root`), the numerator covers more than the denominator does, so the share is inflated. `obs` uses `min(1.0, coverage)`, so only the observability side is clamped. `full = cov_ok = coverage >= 1.0` makes the file `terminal_evidence: true`, so an inflated lower bound can clear 3 % and produce a ">= 3 %" terminal-grade file. The caveat text admits that coverage >= 1 does not prove the same call set, but the arithmetic still mixes the two populations.
**Fix:** Treat `coverage != 1.0` combined with any `deltas` on the five usage fields as `drifted` for the share (UNMEASURED), or compute the share over the measured weighted when the fields differ and mark `terminal_evidence` false unless every `DW7_FIELDS` delta is empty.

### WR-07: `--frozen-file` / `--frozen-ce-ledger` produce `terminal_evidence: true` against a denominator the repo did not freeze, and the file does not record which was used

**File:** `wiki/tools/kme_pillars.py:1917-1924` (`_prepare`), `:2023` (`terminal`), `:2049-2071` (result has no frozen-file path or hash)
**Issue:** (by reading) `--denominator KME-L --frozen-file <any json>` accepts a caller-chosen file. If it carries a KME-L entry equal to the smoke corpus population, the run is `exact`, `primary`, `terminal_evidence: true`. The only trace is the `command:` argv string, and R3 does not inspect it. The tests use `--frozen-file` heavily, so the flag is needed for testing, but the production artifact does not distinguish the two cases.
**Fix:** Record `frozen_file` (relative path) and `frozen_file_sha256` in the front matter. Set `terminal_evidence` false when either differs from the repo `DENOMS_REL` / `CE_LEDGER_REL`. Have R3 compare the recorded sha against the committed file.

## Info

### IN-01: Pillar D observability is session-level "any attachment line seen"

**File:** `wiki/tools/kme_pillars.py:456`, `:500-502`, `:511`
**Issue:** (by reading) A session counts as observed for D if it has any `attachment` line, even if it never had a hook-related attachment. An old transcript format that records only `file` or `todo_reminder` attachments but not `hook_additional_context` would read as observed with 0 chars, giving `< 3 %` instead of UNMEASURED. This is partly covered by the caveat that other channels are not measured. Consider counting a session as observed only when some `hook_*` attachment type appears in it (corpus-wide, or per hook-event version).
**Fix:** Track `hook_sessions` (any `hook_*` attachment) and derive observability from it. Otherwise raise the caveat to the verdict reason.

### IN-02: Minor robustness and hygiene

**File:** `wiki/tools/kme_pillars.py:1316` (a literal invisible BOM character inside the source string; use `""`); `:1161-1163` (G hits whose call has no recorded usage have `span = None` and are silently dropped from `hi`, so the upper bound can be too low); `:2117` vs `:2054` (the filename date and `measured_at` come from two separate `_utcnow()` calls and can straddle midnight).
**Fix:** Use `""`; count the span-less hits in a `details` field and treat them as widening `hi` (or mark the interval open); compute `now` once per run.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
