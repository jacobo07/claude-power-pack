# Incremental Cognition -- UKDL review of the pillar N candidates

What was reviewed: every candidate block of `vault/programs/incremental-cognition/ukdl-candidates.md` (discovered by its
`### IC-<U|D|P>-<NN> -- ` headers, not listed here), against the universal UKDL and the domain UKDL files as they stand at the
commit recorded below. Frozen rule N: "candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion
into ukdl-universal.md and CBR is reviewed, never silent".

reviewer: this run (mission `incremental-cognition`, GEX44 plane, branch `mission/incremental-cognition-run`, plan 06-03); a reading by the mission itself, not the Owner's decision
promotion: left to the Owner, recorded through the `[N]` item of `vault/programs/incremental-cognition/owner-bundle.md`; this review proposes and never writes into the UKDL

reviewed_against: vault/knowledge_base/ukdl-universal.md @ 189497a8348d799691d719b3e2954be29af367f9 sha256 a57ddbb8b2a5f796ce34c7864107bb6b1b7b7e9c2fdc9c400e035147007a01d0

Verdicts: PROMOTE-PROPOSED (evidence from this run, no existing entry owns it), HOLD (single sample, smoke reading, named debt,
or a partial overlap the Owner should settle), REJECT (an existing entry already owns it: `duplicate of <ID>`). Each reason
states the deciding fact.

| candidate | verdict | reason |
|---|---|---|
| IC-U-01 | PROMOTE-PROPOSED | no existing entry owns it: the two sweep hits are an unrelated attribution rule (ukdl-cognitive-resource-os.md:28, subagent rows) and a compaction rule that reads a host-written `compact_boundary` row (ukdl-universal.md:10317), neither classifies a refusal by its writer; the evidence is red-first and drilled (evidence/C.md: V-PFP-FALLBACK-QUOTED-NOT-PARKED and the 137-relaunch shape, drill 5/5) |
| IC-D-01 | PROMOTE-PROPOSED | the one sweep hit is unrelated (sqi_02_test_reach_v1.txt:37, out-of-tree test suites); measured on a real corpus: the unwindowed rescan reads 14 active sessions and 1,679 calls against the frozen 13 and 1,322, and the windowed rescan reproduces the frozen population exactly (evidence/phase3.md:83-85, 212-214); target is the domain file because the lesson is about measuring session corpora |
| IC-P-01 | HOLD | stays project-level: R3 and the smoke / primary roles are this program's own done-gate, and the sweep finds no UKDL home for it (0 hits); the general half (a figure from another workload is not a result about this one) is partly this program's frozen displacement rule (a saving is realized only when measured on the same denominator), and nothing in this run's evidence argues the rest generalises beyond the program |

## Duplicate sweep

One read-only command per candidate over the repository's UKDL surface, then the same terms over the Owner's global rules as
gex44-plane context only (read, never written). A hit is a line to read, not a verdict; the reasons above say what each hit was.

- IC-U-01: `grep -rnEi 'host-written|<synthetic>' vault/knowledge_base CLAUDE.md governance rules` -> 2 hits; ~/.claude/rules (context only) -> 0 hits
- IC-D-01: `grep -rnEi 'frozen denominator|freeze instant|frozen window' vault/knowledge_base CLAUDE.md governance rules` -> 1 hits; ~/.claude/rules (context only) -> 0 hits
- IC-P-01: `grep -rnEi 'evidence_role|terminal_evidence|smoke measurement' vault/knowledge_base CLAUDE.md governance rules` -> 0 hits; ~/.claude/rules (context only) -> 0 hits

## Promotions recorded

none
