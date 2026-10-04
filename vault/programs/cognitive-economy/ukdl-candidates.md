# Cognitive Economy Program -- UKDL 3-level and CBR review [R]

Pillar [R] institutionalization. Every candidate the campaign produced, at one of the three UKDL levels (hard rule,
process rule, trap), with its evidence, a verdict and the reason for it. Format checked by
`vault/programs/cognitive-economy/gates/gate_ukdl_candidates.py`.

What the verdicts mean here:

- **promote**: the campaign recommends entry into `vault/knowledge_base/ukdl-universal.md`. That file is peer-hot
  (audit G10), so promotion is an Owner item, listed in `owner-bundle.md` as `[R] UC-NN`. Nothing was written there.
- **reject**: an existing owner already states the rule. A second copy would drift from the first, so the reason
  names that owner.
- **keep-candidate**: real, but seen once in this campaign. It stays here until a second occurrence earns it.

CBR maturity: the plan of record fixes every finding at EXPERIMENTAL until earned (plan s4). None was earned
inside one campaign: no finding was re-observed in an independent run or project. The CBR review is therefore the
`cbr:` line of each block, and every one reads EXPERIMENTAL.

### UC-01 A self-test pole hardcoded from history goes stale when that history grows
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: tools/test_cognitive_economy_program.py
- reason: V-CEP-REAL-HANDOFF assumed that the plan file's only commit was C0. Two later campaign commits (the P0 freeze and the execution log) touched the file, so the "not landed" pole read True and selftest S0 made the done-gate untrustworthy. The poles now come from the file's own log: the newest commit, and the parent of the oldest. Seen once, so it stays a candidate.

### UC-02 An import matcher that knows one import shape files used modules as untested
- level: trap
- verdict: reject
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/measure/t_sweep.py
- reason: The T sweep matched only dotted and slash paths. It missed three shapes: `from modules.pkg import mod`, parenthesised multi-line imports, and relative sibling imports. Each miss sent modules in use toward deletion. Run 3 had 3 RETIRE_CANDIDATE rows, all imported by siblings; after the fix there are 0. The instrument-before-claim skill already owns this rule (could the instrument have returned the other answer? Positive control before a negative claim), so a UKDL copy would duplicate it.

### UC-03 A git-derived label needs an UNKNOWN outcome when git fails or times out
- level: process
- verdict: reject
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/measure/turns.py
- reason: A 60 s `git log` timeout turned every edit in a large repo into edit_uncommitted, and so into non-convergence. The fix labels those edits edit_unknown (UNSETTLED). The real-context-reachability skill already owns this as its core rule (absent is not zero), so this is an instance, not a new rule.

### UC-04 A shared-checkout progress fingerprint makes a no-progress halt unreachable
- level: trap
- verdict: promote
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/handoffs/J.md, vault/programs/cognitive-economy/evidence/H-J-turn-advancement.md
- reason: Verified in source (audit G5). `tools/gsd_mission.py` progress_fingerprint hashes HEAD, the whole-tree porcelain status and the shortstat of the work dir. In a checkout other panes write to, any peer commit or dirty file changes that hash, so a stalled mission reads as progressing and the no_progress halt cannot fire. This is a structural blindness in a live supervisor, and no current UKDL entry names it. The fix belongs to the mission owner (handoff J); the entry belongs to the Owner's promotion. Promoted 2026-10-04 on Owner decision 6 as T-A-WHOLE-TREE-PROGRESS-FINGERPRINT-CANNOT-SEE-A-STALL-IN-A-SHARED-CHECKOUT-001 in a new section, "Cognitive Economy Program, pillar R promotion", at the end of ukdl-universal.md. Re-checked in source at 37d1940d (`tools/gsd_mission.py:2022` and `:1897`). Still unfixed.

### UC-05 Measure a lever against frozen materiality before building it
- level: process
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/evidence/F-G-P-C-carriage.md, vault/programs/cognitive-economy/evidence/D-E-context-lifetime.md, vault/programs/cognitive-economy/evidence/K-tool-output-admission.md
- reason: Of the levers measured on D-W7 under the frozen 3 % rule, one cleared it: J, with HUMAN-rooted recovery + repeat + non-convergent at 3.51 %. These fell below: F identity re-reads 1.88 %, K largest dead class 2.67 %, P verification 0.50 %, C-tools schema carriage 0.002 %, E earlier rotation at most 2.78 %, and the D economic trigger at most +0.19 % net. Each was a build somebody had proposed. HR-NOVELTY-001 covers proposals for new systems; this candidate covers optimization levers. Its strength is one campaign, so it stays a candidate.

### UC-06 Rent avoided by a boundary is not a saving relative to the alternative it replaced
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/evidence/D-E-context-lifetime.md
- reason: Context crossings avoided at most 17.16 % of D-W7 in carried context relative to never crossing. The real alternative at the wall was compaction or ending the session, and neither was measured. So the figure is an upper bound with unknown displacement, not a saving. The post-effect-resource-truth rule covers measured effects, not counterfactual ones, so the gap is real. It was seen once.

### UC-07 A JSON state file with case-variant duplicate keys breaks PowerShell readers
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/evidence/L-prg.md
- reason: `ConvertFrom-Json` on PowerShell 5.1 rejects keys that differ only in case, and compound-learnings.json carries such a pair. The steps78 module writes case-sensitive keys and was proven on temp copies. The live switch is Owner item [L]. The pair's share of the STUCK counter was not measured, so the candidate's weight is unknown.

## Closure candidates (W6, 2026-10-04)

Added after the 2026-10-04 closure work on `feature/knowledge-acquisition` (commits d1876ce1, acbaabcf, a1d00a66,
f207585b). Same format and the same bar: one occurrence each, so none is promoted.

### UC-08 A closed terminal is read as a built, running capability
- level: process
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: tools/test_cognitive_economy_program.py, vault/programs/cognitive-economy/ledger.json
- reason: Pillar L closed at IMPLEMENTED_AND_VERIFIED while its module had only ever run on temp copies and no live call site reached it. A terminal records how an obligation closed; it says nothing about whether the capability is built, running or measured, and the status surfaces read it as all three. Clauses X1 and X3 (d1876ce1) now keep terminal, built, activation (WIRED, and ACTIVE only with a pinned real-run receipt) and owner decision apart, and `--status` prints them as separate columns. The nearest owner, documented-capability-must-be-executable, gives documents a LIVE / PLANNED / ABSENT status; it does not cover a ledger's terminal vocabulary. Seen once.

### UC-09 A gate whose precondition is a transient live artifact fails on correct code
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: vault/programs/cognitive-economy/gates/gate_compound78.py, vault/programs/cognitive-economy/CLOSE.md
- reason: The first `--final` after the [RUN] merge failed pillar L because gate_compound78 refused to run without the live `LEARNINGS_PENDING.md`. That marker is residue: a successful `/cpp-compound` deletes it and the sentinel recreates it, so the gate judged what the last run left behind, not the module. Fix acbaabcf: the module only unlinks the marker, so with no live marker the gate judges a synthetic one and prints `marker=live|synthetic`, and the synthetic `--break-rollback` run still goes red. Seen once.

### UC-10 A second status surface drifts from the ledger it summarizes
- level: process
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: tools/test_cognitive_economy_program.py, .planning/workstreams/cognitive-economy/REQUIREMENTS.md
- reason: REQUIREMENTS.md traceability rows read "Complete" for pillars whose ledger terminal was DEFERRED or FALSIFIED. The table was hand-maintained beside the ledger and nothing compared them. Clause X2 (d1876ce1) requires every closed pillar's row to name its ledger terminal, and two mutants (row drifted, row missing) each go red. PR-COVERAGE-BY-CONSTRUCTION-001 is about which subjects an audit enrolls, not about a hand-kept copy of a status that already exists elsewhere. Seen once.

### UC-11 A text decode judged successful because it raised nothing
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: modules/liveness/reachability.py, tools/test_reachability.py
- reason: On this Spanish-locale host `schtasks /query /xml` emits the ANSI code page (387 KB cp1252, 232 tasks). Decoding it as utf-16 produces garbage with no error, utf-8 raises on the first accent, and the probe list held nothing else, so discovery returned "no scheduled tasks" and hibernate_runner read ORPHAN while PP-Hibernation ran it every 5 minutes. The suite stayed green because it only injected a hand-made XML string. A second defect hid behind the first: the wscript `.vbs` launcher was not a known extension, so the path match ran into the next argument. Fix a1d00a66 judges each decode by finding a `<Task ` element; task seeds went 0 -> 14. instrument-before-claim owns the general question. This specific shape is not in the UKDL: a successful decode is not evidence of the right encoding, and a fixture written by hand is not the producer's output. The cp1252 lesson in session_lessons is about `subprocess text=True` mojibake, which is a different mechanism. Seen once.

### UC-12 Live code runs from an uncommitted working tree in a shared checkout
- level: trap
- verdict: keep-candidate
- cbr: EXPERIMENTAL
- evidence: tools/compound_unattended.py
- reason: The unattended compound driver runs from the working tree of a checkout that several panes share. Since about 2026-09-10 that file has carried a foreign uncommitted diff (+118 / -13 at 2026-10-04), so no commit records the code the scheduled run executes. A reviewer reading HEAD reviews different code, and a checkout or stash by any pane changes production behaviour without a trace. f207585b staged its one-line change from the committed blob so that the foreign diff stayed out of the commit. The defect is recorded as a finding; fixing it belongs to that file's owner. Seen once.
