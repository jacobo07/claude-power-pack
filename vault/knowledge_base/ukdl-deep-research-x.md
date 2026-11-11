# UKDL — Deep Research X (DRX), session 2026-11-11

Domain UKDL file, following the precedent of `ukdl-cognitive-resource-os.md` and
`product_demo/ukdl-product-demo-2026-09-24.md`. Written here rather than appended to
`ukdl-universal.md` because that file carried another session's staged and unstaged hunks
during this session; a pathspec commit would have taken them. Promote entries marked
#CROSS-PROJECT into `ukdl-universal.md` when it is quiescent.

Evidence commits on `feature/knowledge-acquisition`: `1c68ddd8` `0c88da6f` `e4cf7bfb` `3f65e070`
`0de91ea6` `9ba43e49`. Suite: `python tools/test_deep_research_x.py` (DRX_PASS=30/30).

## Error log (Knowledge Vault)

| # | Symptom | Root cause (verified unless marked) | Fix | Regression gate | Class |
|---|---|---|---|---|---|
| E1 | 3/3 baseline missions: 0 queries, 0 learnings | `claude.exe -p` child loaded every user/project hook and MCP server: 61.5 s to answer "pong", so the first real prompt crossed the 120 s timeout. Docstring claimed hooks were disabled; only tools were | `--setting-sources local --strict-mcp-config`, cwd outside the repo: 5.0-5.8 s, OAuth kept (`--bare` drops OAuth) | V-DRX-LLM-CHILD-ISOLATED | 2 (false premise in code) |
| E2 | Those empty runs printed "OK" and exited 0 | `main()` returned 0 unconditionally | exit 3 / INSUFFICIENT when nothing persisted | V-DRX-EMPTY-RUN-IS-NOT-OK | 5 (success without work) |
| E3 | Baseline markdown fell to bs4/regex: "No module named trafilatura" | my harness ran the engine with `python -I`, which drops user site-packages where trafilatura/readability live | runner without `-I`; the run was discarded and renamed `*_INVALID_isolated_python` | runner comment; parser layer is printed in every report's "Layers fired" | 2 (harness premise) |
| E4 | Copies cited as VERIFIED kept VERIFIED after the lineage demotion fired | I applied `min()` over `EPISTEMIC_RANK`, which ranks OBSERVED above VERIFIED, so min(OBSERVED, VERIFIED) returned the old label; the module comment warned against exactly this | removed the min(); only targeted moves remain | V-DRX-COPIES-ARE-ONE-LINEAGE | 1 (assumed API semantics) |
| E5 | Running the suite wrote a test checkpoint into the real vault | test redirected `RESEARCH_DIR` but `CHECKPOINT_DIR` is derived from it at import time | test redirects it; stray file deleted after prompt check | V-DRX-TEST-HERMETIC | 2 |
| E6 | Hand-picked mutation drill 5/5 killed, generic probe 5/10 survived | hand-picked mutants test what the author already thought of: `summary()`, `mark_persisted`, a forged span hash and the 10 boundary were unasserted | pinned all four; floor 1/6 -> 3/6 | mutation_ratchet push pair | 5 |
| E7 | Mission prompt names `knowledge-vault/UKDL/universal-knowledge.md` | path does not exist; real file `vault/knowledge_base/ukdl-universal.md` | used the real path; recorded | - | 2 |
| E8 | Approved plan put the ratchet in `baseline_inheritance` | that suite pins the always-loaded doctrine (`parts/core.md`); DRX does not belong there | used `mutation_ratchet`, said so in the commit | - | 2 (plan premise) |
| E10 | 3 of 26 real snapshots failed `audit_ledger` (hash mismatch) | bytes intact; `read_text()` translated CRLF -> LF, so audit hash and resumed span offsets used different text. The tamper test's text-mode "restore" was itself a tamper, masked by the same bug | read with `newline=""`; test restores bytes | V-DRX-CRLF-SNAPSHOT-ROUNDTRIP (failed before fix) | 1 |
| E11 | My triage said 6/9 rejected quotes were misattributed | I classified by >= 40% overlap; a replay of the actual rule found 4 exact | reported 4/9; RESULTS.md carries the corrected numbers | replay script against the real ledgers | 5 (instrument looser than the claim) |
| E12 | Two Edits on one file in one batch, twice (anti-thrash block) | ignoring a known batch cap under momentum | one Edit per file per batch, Read between | anti-thrash hook (worked as designed) | recurring |
| E13 | v0.4.0 yield fell 36 -> 15 learnings, 1 INSUFFICIENT run | HYPOTHESIS: verbatim quotes lengthen extraction output past the 120 s child timeout (2 extraction timeouts in v0.4.0, 0 in v0.3.1; n=3) | not fixed; next experiment in `vault/research/drx_eval/RESULTS.md` | - | open |
| E9 | Minor tool errors: `Set-Content -Encoding utf8NoBOM` on PS 5.1; PowerShell backtick-n inside a Python literal; two Edits on one file in one batch | known PS 5.1 / batch-cap classes | Copy-Item / Edit tool / one edit per batch | - | 4 |

## Distilled rules

### T-CHILD-CLI-INHERITS-THE-ESTATE-001  #CROSS-PROJECT

PROVEN (E1). A tool that spawns `claude -p` as a text generator inherits the whole estate: every
user/project hook and every MCP server start on each call. On this host that is ~56 s of a 61.5 s
call. `--disallowed-tools "*"` disables tools, not hooks. Use `--setting-sources local
--strict-mcp-config` and an empty cwd outside any repo; `--bare` also skips hooks but never reads
OAuth. Measure a "pong" call before trusting any timeout. PP `0c88da6f`.

### T-EMPTY-RUN-REPORTED-OK-001  #CROSS-PROJECT

PROVEN (E2). A pipeline whose success exit does not depend on having produced anything makes a total
outage indistinguishable from a working run for every caller and scheduler. Exit non-zero when the
output count is zero, whatever the reason. PP `0c88da6f`.

### T-ISOLATED-PYTHON-DROPS-USER-SITE-001  #CROSS-PROJECT

PROVEN (E3). `python -I` (recommended for scripts that read untrusted files) also removes user
site-packages. Code with an import-fallback cascade then degrades silently instead of failing. Use
`-I` for scripts you did not write; run your own engines the way production runs them, and make
the chosen fallback layer visible in the output.

### T-RANK-SCALE-IS-NOT-A-DEGRADE-ORDER-001

PROVEN (E4). A strength ranking used for display is not a demotion order: in this repo OBSERVED >
VERIFIED, because they fail for different reasons. A min() over it re-promotes a demoted claim.
Express demotions as explicit moves and pin each with a gate.

### T-DERIVED-PATH-CONSTANTS-ESCAPE-TEST-REDIRECTION-001  #CROSS-PROJECT

PROVEN (E5). Redirecting a module's base directory in a test does not redirect constants computed
from it at import time. Add a hermeticity witness (snapshot of the real directory before and after
the suite) instead of trusting the redirect list.

### PR-HAND-PICKED-MUTANTS-ARE-NOT-COVERAGE-001  #CROSS-PROJECT

PROVEN (E6). A drill of mutants chosen by the author only re-asks the author's own questions. Pair
it with a sampled probe (`tools/mutation_probe.py`) and ratchet the probe's kill count; triage
every survivor as gap / equivalent / cosmetic in writing.

### PR-VERIFY-THE-INTEGRATION-POINT-BEFORE-NAMING-IT-001

PROVEN (E8, E7). A plan that names an integration point (a ratchet, a path, a registry) names a
premise. Read the target's contract before the plan is approved, or mark the point "to be
verified" in the plan; changing it later is allowed only with the reason stated.

### HR candidate (not promoted): claims need a locatable quote

DRX enforces in code that no claim is labelled above HYPOTHESIS without a verbatim quote found in
a stored snapshot (`evidence_ledger.verify_claim`, audited by `audit_ledger`). This is a project
invariant, not yet a universal Hard Rule: one session of evidence is not enough to impose it on
every research-producing system. Promotion criterion: a second system adopts it and a run shows
it caught a fabricated citation that would otherwise have shipped.
