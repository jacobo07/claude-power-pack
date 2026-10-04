# Incremental Cognition -- UKDL review of the pillar N candidates

What was reviewed: every candidate block of `vault/programs/incremental-cognition/ukdl-candidates.md` (discovered by its
`### IC-<U|D|P>-<NN> -- ` headers, not listed here), against the universal UKDL and the domain UKDL files as they stand at the
commit recorded below. Frozen rule N: "candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion
into ukdl-universal.md and CBR is reviewed, never silent".

reviewer: this run (mission `incremental-cognition`, GEX44 plane, branch `mission/incremental-cognition-run`, plan 06-03); a reading by the mission itself, not the Owner's decision
promotion: left to the Owner, recorded through the `[N]` item of `vault/programs/incremental-cognition/owner-bundle.md`; this review proposes and never writes into the UKDL

reviewed_against: vault/knowledge_base/ukdl-universal.md @ 54128e64edf672b72344b2a1c5c90fdb4a9c6c13 sha256 a57ddbb8b2a5f796ce34c7864107bb6b1b7b7e9c2fdc9c400e035147007a01d0

Verdicts: PROMOTE-PROPOSED (evidence from this run, no existing entry owns it), HOLD (single sample, smoke reading, named debt,
or a partial overlap the Owner should settle), REJECT (an existing entry already owns it: `duplicate of <ID>`). Each reason
states the deciding fact. Totals: 4 PROMOTE-PROPOSED, 11 HOLD, 1 REJECT.

| candidate | verdict | reason |
|---|---|---|
| IC-U-01 | PROMOTE-PROPOSED | no existing entry owns it: the two sweep hits are an unrelated attribution rule (ukdl-cognitive-resource-os.md:28, subagent rows) and a compaction rule that reads a host-written `compact_boundary` row (ukdl-universal.md:10317), neither classifies a refusal by its writer; the evidence is red-first and drilled (evidence/C.md: V-PFP-FALLBACK-QUOTED-NOT-PARKED and the 137-relaunch shape, drill 5/5) |
| IC-U-02 | REJECT | duplicate of T-COMMIT-IS-NOT-INSTALL-WHEN-THE-INSTALL-IS-A-WORKING-TREE-001: that entry already says the version that runs is the install, not the commit log; a7 at 01199995 is a second instance of the same lesson and the Owner may append it there, while the typed refusal pp_install_stale is code, not a new rule |
| IC-U-03 | HOLD | partly owned by the Owner's global rules develop-here-prove-there and validation-planes-do-not-transfer (gex44-plane context, outside this repository: the sweep finds 0 repository hits and 1 global hit); the evidence is three reds with one cause on one plane (node v18.19.1), so it is one sample, and the Owner should decide whether a repository entry adds anything to the global rule |
| IC-U-04 | PROMOTE-PROPOSED | the 7 sweep hits are all citations of PR-VERIFY-HANDOFF-PREMISES-001, which covers the RECEIVING side (verify the premises you were handed); this is the sending side (replay what you hand over at the target's base) and it was measured twice in this run: the Phase 3 list at 18e928af left frozen_source at 0 and the [K] list left its fixture suite at 66/67 (evidence/L.md:112-122); it would be a sister entry, not a duplicate |
| IC-U-05 | HOLD | a single pair of sessions (607795c4 against 34f03871) and one 4,383-char part; the generalisation to any baseline is an inference from one sample, and no other session-kind pair was measured |
| IC-U-06 | PROMOTE-PROPOSED | the sweep finds 0 hits; a measured defect with a red-first fix: before plan 06-01 `--pillar J` printed ICP_PILLAR_J=PASS for a misquoted owner terminal, fixed by running check_consumed with only=[pid] and pinned by V-ICP-R2-PILLAR-MODE plus a mutant that removes the clause (06-01-SUMMARY.md:86, test_incremental_cognition_program.py:775-782) |
| IC-D-01 | PROMOTE-PROPOSED | the one sweep hit is unrelated (sqi_02_test_reach_v1.txt:37, out-of-tree test suites); measured on a real corpus: the unwindowed rescan reads 14 active sessions and 1,679 calls against the frozen 13 and 1,322, and the windowed rescan reproduces the frozen population exactly (evidence/phase3.md:83-85, 212-214); target is the domain file because the lesson is about measuring session corpora |
| IC-D-02 | HOLD | the general rule (an absent channel is not a measured zero) is already the Owner's global rule real-context-reachability (gex44-plane context, 1 global hit) and is honoured across this repository's UNMEASURED doctrine; this run adds one concrete instance (GEX44-B001: 7 of 10 sessions carry a hook attachment, the earlier `< 3 %` was corrected), which suits an appended instance rather than a new entry |
| IC-D-03 | HOLD | a performance reading on a smoke corpus: 8,773,728 weighted is an upper bound on KME-G (plane gex44, evidence_role smoke) and the displacement rule says a saving is realized only when measured on the same denominator; KME-L decides, and the growth-above-floor modelling choice is this program's instrument design |
| IC-D-04 | HOLD | the 1-versus-75 repeats come from an unwindowed planning probe that evidence/L.md:38-42 itself labels "not a measurement"; the smoke population shows only 3 loose and 0 strict retries |
| IC-D-05 | HOLD | proven on scratch credentials files only (V-ENVPF-AUTH-LAPSED-REFRESHABLE); no real environment was observed lapsed-but-refreshable and the CLI's own refresh behaviour was not measured here, so the claim that the launch succeeds is untested |
| IC-D-06 | HOLD | a smoke reading: KME-G and GEX44-B001 are both GEX44 workloads of the same kind of work, so the second is not independent confirmation, and pillar H's own verdict waits on the KME-L run and on CE P and G terminals |
| IC-P-01 | HOLD | stays project-level: R3 and the smoke / primary roles are this program's own done-gate, and the sweep finds no UKDL home for it (0 hits); the general half (a figure from another workload is not a result about this one) is partly this program's frozen displacement rule (a saving is realized only when measured on the same denominator), and nothing in this run's evidence argues the rest generalises beyond the program |
| IC-P-02 | HOLD | stays project-level: R4 is this program's done-gate rule about its own bundle; the 7 sweep hits are unrelated owner_decision fields in other datasets (setup_os, pp_dataset), so there is no UKDL home and no argument here that it generalises |
| IC-P-03 | HOLD | stays project-level: the NOT RUNNABLE HERE label and the parse-only proof are this bundle's convention for laptop-plane commands; the sweep finds 0 hits, and the general half is already covered by the plane-naming rule of IC-U-03 |
| IC-P-04 | HOLD | a named debt, not a rule: the R3 gate still trusts self-asserted front matter (STATE.md Phase 5 review-fix NAMED DEBT (1)); promoting a rule the gate does not yet enforce would be a documented capability that is not executable |

## Duplicate sweep

One read-only command per candidate over the repository's UKDL surface, then the same terms over the Owner's global rules as
gex44-plane context only (read, never written). A hit is a line to read, not a verdict; the reasons above say what each hit was.

- IC-U-01: `grep -rnEi 'host-written|<synthetic>' vault/knowledge_base CLAUDE.md governance rules` -> 2 hits; ~/.claude/rules (context only) -> 0 hits
- IC-U-02: `grep -rnEi 'COMMIT-IS-NOT-INSTALL|pp_install_stale|install is a working tree' vault/knowledge_base CLAUDE.md governance rules` -> 3 hits; ~/.claude/rules (context only) -> 0 hits
- IC-U-03: `grep -rnEi 'outside the vendored|name the plane|names the plane|plane-dependent' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 1 hits
- IC-U-04: `grep -rnEi 'HANDOFF-PREMISES|replayed in a scratch|scratch clone' vault/knowledge_base CLAUDE.md governance rules` -> 7 hits; ~/.claude/rules (context only) -> 0 hits
- IC-U-05: `grep -rnEi 'same session kind|same kind of session' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-U-06: `grep -rnEi 'cross-object clause|per-pillar check|per-item check' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-D-01: `grep -rnEi 'frozen denominator|freeze instant|frozen window' vault/knowledge_base CLAUDE.md governance rules` -> 1 hits; ~/.claude/rules (context only) -> 0 hits
- IC-D-02: `grep -rnEi 'unobserved-as-zero|absent is not zero|not observed for the whole' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 1 hits
- IC-D-03: `grep -rnEi 'growth above|thread floor|rollover growth' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-D-04: `grep -rnEi 'retry identity|retry key|identical repeat' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-D-05: `grep -rnEi 'access_token_lapsed|lapsed access token|refresh token' vault/knowledge_base CLAUDE.md governance rules` -> 1 hits (rules/python/fastapi.md, unrelated); ~/.claude/rules (context only) -> 0 hits
- IC-D-06: `grep -rnEi 'verifier subagent|verification share|verifier-driven' vault/knowledge_base CLAUDE.md governance rules` -> 1 hits (craif_00_constitution_v1.txt:347, scanner-verifier collusion, unrelated); ~/.claude/rules (context only) -> 0 hits
- IC-P-01: `grep -rnEi 'evidence_role|terminal_evidence|smoke measurement' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-P-02: `grep -rnEi 'mission.s request|bundle is the|owner_decision' vault/knowledge_base CLAUDE.md governance rules` -> 7 hits; ~/.claude/rules (context only) -> 0 hits
- IC-P-03: `grep -rnEi 'NOT RUNNABLE HERE|laptop-plane command|proven only to parse' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits
- IC-P-04: `grep -rnEi 'self-asserted|trusts self' vault/knowledge_base CLAUDE.md governance rules` -> 3 hits; ~/.claude/rules (context only) -> 0 hits

The three IC-P-04 hits are prose in other datasets (acis_00:96, ias_c1:2048, daif_08:251) about self-reported inputs, not
this gate.

## Promotions recorded

none
