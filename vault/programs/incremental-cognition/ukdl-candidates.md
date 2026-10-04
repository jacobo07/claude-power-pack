# Incremental Cognition -- candidate learnings (pillar N closeout)

Frozen rule N (verbatim from `ledger.json`, `frozen.pillars` id N):

> candidates go to vault/programs/incremental-cognition/ukdl-candidates.md; promotion into ukdl-universal.md and CBR is reviewed, never silent

These are the candidate learnings of THIS run (mission `incremental-cognition`, GEX44 plane, branch
`mission/incremental-cognition-run`). Nothing in this file is promoted: promotion into `vault/knowledge_base/ukdl-universal.md`
or into a CBR family generation is the Owner's (`[N]` in `owner-bundle.md`), and the closeout gate
(`python3 tools/test_ic_closeout.py`) turns red if a candidate id ever shows up in the UKDL or under `vault/tower/` without a
recorded promotion. Each verdict (PROMOTE-PROPOSED / HOLD / REJECT) and its reason live in
`reviews/ukdl.md` and `reviews/cbr.md`, never here.

Three levels, each with its own target:

| level | what it is | target |
|---|---|---|
| universal | true of any project that does this kind of work | `vault/knowledge_base/ukdl-universal.md` |
| domain | true of this kind of work (measuring and supervising agent sessions) | an existing file under `vault/knowledge_base/`, here `ukdl-cognitive-resource-os.md` (mission-scoped entries, kept out of the universal file because its tail has an automated writer) |
| project | true of this program only | this file |

Block grammar, discovered by the gate and never listed in it: `### IC-<U|D|P>-<NN> -- <title>`, then `level:`, `kind:`
(`hard-rule` | `process-rule` | `trap` | `performance`), `proposed_id:` (UKDL id grammar), `target:`, `statement:`,
`evidence:` (refs separated by ` ; `: a tracked path, an optional `:line` or `:from-to`, or `commit:<sha>` reachable from HEAD)
and, for a performance guarantee, `second_workload:`. Every ref was re-read at its path / line / commit when it was written.

## Universal

### IC-U-01 -- classify an authorization refusal by who wrote the reply, never by its words
level: universal
kind: process-rule
proposed_id: PR-CLASSIFY-A-REFUSAL-BY-ITS-WRITER-NOT-ITS-WORDS-001
target: vault/knowledge_base/ukdl-universal.md
statement: A supervisor that decides "the worker was refused, stop relaunching" from the last reply must judge the AUTHOR of the reply (a host-written row: model `<synthetic>`, zero usage), not the phrase. A model that merely quotes "Please run /login" is not a refusal (the breaker-less fallback in tools/gsd_mission.py needs the host author AND an auth phrase, and the quoted case is pinned by V-PFP-FALLBACK-QUOTED-NOT-PARKED). Matching words alone would park a healthy mission; ignoring the refusal relaunches a locked-out one (the a7 loop: 137 dead relaunches in the replayed transcript shape).
evidence: tools/gsd_mission.py:1957-1972 ; vault/programs/incremental-cognition/evidence/C.md:21-22 ; vault/programs/incremental-cognition/evidence/C.md:93-95 ; vault/programs/incremental-cognition/evidence/C.md:105-107 ; commit:5962571c840943ae0a3aa901efb08e69a04434da

### IC-U-02 -- the environment's install, not the repository, decides which fix runs
level: universal
kind: trap
proposed_id: T-AN-ENVIRONMENTS-INSTALL-NOT-THE-REPOSITORY-DECIDES-WHICH-FIX-RUNS-001
target: vault/knowledge_base/ukdl-universal.md
statement: The repository held the auth-refusal park (5962571c) and the pre-launch gate (60e7947d), but a7's install sat detached at 01199995, before both, so the environment that actually launches workers had neither fix. A green suite in the repository says nothing about the install that runs: refuse a launch when the install head is behind a recorded commit floor (typed reason pp_install_stale), and repair it by a repeatable deploy, never by hand copying.
evidence: .planning/workstreams/incremental-cognition/phases/02-persistent-failures-and-remote-integrity/02-02-PLAN.md:90 ; vault/programs/incremental-cognition/evidence/B.md:18-21 ; vault/programs/incremental-cognition/evidence/B.md:140-141 ; vault/programs/incremental-cognition/evidence/B.md:43-44 ; commit:60e7947dcf3cf0f9c660e412ec6276a8b2922f99

### IC-U-03 -- a red can be a property of the plane: name the plane before blaming the change
level: universal
kind: process-rule
proposed_id: PR-NAME-THE-PLANE-BEFORE-BLAMING-THE-CHANGE-FOR-A-RED-001
target: vault/knowledge_base/ukdl-universal.md
statement: Suite reds on GEX44 (V-MC-PLAN-FACTS-REFUSES-OVERLAP, V-HPKT-ATTACH, V-HPKT-PARTIAL-REFUSED) belong to the plane, not to the change under test: the GEX44 main node is v18.19.1, outside the vendored engine range ^22.23.2 or ^24.14.0, while the a5 and a7 environment nodes (v24.15.0) are inside it. Before blaming a change, name the plane and the cause, and show the same failure list with and without the change.
evidence: vault/programs/incremental-cognition/evidence/C.md:60 ; vault/programs/incremental-cognition/evidence/C.md:66-68 ; vault/programs/incremental-cognition/evidence/B.md:99 ; vault/programs/incremental-cognition/evidence/B.md:151-153 ; vault/programs/incremental-cognition/owner-bundle.md:39

### IC-U-04 -- replay a handed-over command list at the target's base before handing it over
level: universal
kind: process-rule
proposed_id: PR-REPLAY-A-HANDED-OVER-LIST-AT-THE-TARGET-BASE-BEFORE-HANDING-IT-OVER-001
target: vault/knowledge_base/ukdl-universal.md
statement: A list of steps handed to another machine goes stale as later fixes land. The Phase 3 cherry-pick list, replayed literally in a scratch clone at the P0 freeze 18e928af, applied cleanly and left kme_pillars.py with frozen_source 0 times (added later by a4d09a24), so no KME-L file made along it could close D..I; the Phase 4 [K] list left its own fixture suite at 66/67 because the bundle its parse gate reads was never brought. Replay the list in a scratch clone at the target's base, state what that replay printed, and replace the list with one guarded step.
evidence: vault/programs/incremental-cognition/owner-bundle.md:207-213 ; vault/programs/incremental-cognition/owner-bundle.md:323-327 ; vault/programs/incremental-cognition/evidence/L.md:112-122 ; vault/programs/incremental-cognition/evidence/L.md:223-226 ; commit:a4d09a24

### IC-U-05 -- a reference and the checks made against it must be the same session kind
level: universal
kind: trap
proposed_id: T-A-REFERENCE-AND-ITS-CHECKS-MUST-BE-THE-SAME-SESSION-KIND-001
target: vault/knowledge_base/ukdl-universal.md
statement: Two same-day sessions of one repository (the interactive 607795c4 and the mission worker 34f03871) differ by one appended 4,383-char system prompt part, the worker's launcher prompt. The floor gate reads a worker against an interactive reference as a material rise (RISE system_prompt delta=+4383) and the reverse as a drop of the same size, so a baseline taken from one session kind cannot judge another.
evidence: vault/programs/incremental-cognition/evidence/K.md:72 ; vault/programs/incremental-cognition/evidence/K.md:106-107 ; vault/programs/incremental-cognition/evidence/K.md:133-135 ; vault/programs/incremental-cognition/evidence/K.md:249-252

### IC-U-06 -- a per-item check must run every clause the full gate refuses on
level: universal
kind: process-rule
proposed_id: PR-A-PER-ITEM-CHECK-MUST-RUN-EVERY-CLAUSE-THE-FULL-GATE-REFUSES-ON-001
target: vault/knowledge_base/ukdl-universal.md
statement: Before plan 06-01 the per-pillar done-gate (--pillar J) ran R3 and R4 but not R2, and the CE clause L4 accepts any owner_ledger row without reading it, so a J terminal with a misquoted owner terminal printed ICP_PILLAR_J=PASS while the full gate refused it. A narrowed check is only as good as the clauses it carries over: enumerate what the full gate refuses on, drive each from the narrowed entry point, and keep a mutant that removes the clause.
evidence: .planning/workstreams/incremental-cognition/phases/06-consume-owners-and-close/06-01-SUMMARY.md:86 ; vault/programs/incremental-cognition/evidence/JM-blocked.md:248-250 ; tools/test_incremental_cognition_program.py:740-744 ; tools/test_incremental_cognition_program.py:775-782

## Domain

### IC-D-01 -- a frozen denominator over a live corpus reproduces only inside its frozen window
level: domain
kind: trap
proposed_id: T-FROZEN-DENOMINATOR-OVER-A-LIVE-CORPUS-REPRODUCES-ONLY-IN-ITS-WINDOW-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: A population frozen at an instant is reproduced by a rescan only if the rescan is cut back to that instant: the live corpus keeps growing, so an unwindowed scan reads a different population (14 active sessions / 1,679 calls against the frozen 13 / 1,322). The instrument must default to the freeze instant, locate it with a bounded search, and treat a population that does not match as UNMEASURED, never as "below the threshold".
evidence: .planning/workstreams/incremental-cognition/STATE.md:66 ; vault/programs/incremental-cognition/evidence/phase3.md:10-11 ; vault/programs/incremental-cognition/evidence/phase3.md:83-85 ; vault/programs/incremental-cognition/evidence/phase3.md:169-172 ; vault/programs/incremental-cognition/evidence/phase3.md:212-214

### IC-D-02 -- a workload whose sessions lack the observed channel is UNMEASURED, not below threshold
level: domain
kind: trap
proposed_id: T-A-WORKLOAD-WITHOUT-THE-OBSERVED-CHANNEL-IS-UNMEASURED-NOT-BELOW-THRESHOLD-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: Pillar D on the named workload GEX44-B001 first read "< 3 %" while only 7 of its 10 sessions carried a hook_* attachment at all; the silence of the other three says nothing about hook rent. After the review fix D requires a hook_* attachment in a session before its silence counts, the file was regenerated, and the same reading became UNMEASURED (observability 0.855). An absent channel is a gap in the measurement, never a measured zero.
evidence: vault/programs/incremental-cognition/evidence/phase3.md:76 ; vault/programs/incremental-cognition/evidence/phase3.md:162-163 ; vault/programs/incremental-cognition/evidence/phase3.md:185-188

### IC-D-03 -- a rollover policy can only save the growth above the thread floor, not the absolute context
level: domain
kind: performance
proposed_id: PR-A-ROLLOVER-CANDIDATE-MEASURES-GROWTH-ABOVE-THE-THREAD-FLOOR-NOT-ABSOLUTE-CONTEXT-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: On GEX44 the first-call floor of a thread runs 124,905 .. 194,591 tokens (median 173,427.5 over 24 threads), above the 150,000 large-context mark, so an absolute threshold crosses on every first call and measures the floor, not lateness. The late-rollover candidate therefore replays growth above the thread's own floor (default 100,000). The KME-G smoke puts its upper bound at 8,773,728 weighted (15.98 % of 54,899,558.8), an optimistic ceiling on one corpus, not a saving.
evidence: vault/programs/incremental-cognition/evidence/L.md:33-37 ; vault/programs/incremental-cognition/evidence/L.md:106-110 ; vault/programs/incremental-cognition/evidence/L.md:218-220 ; wiki/tools/kme_replay.py:21-25

### IC-D-04 -- retry identity is the command text, not the input JSON
level: domain
kind: trap
proposed_id: T-RETRY-IDENTITY-IS-THE-COMMAND-TEXT-NOT-THE-INPUT-JSON-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: A Bash input carries a description beside its command, so keyed by the full input JSON the planning probe of the a5 / a7 / b001 trees found 1 identical repeat, while keyed by the command text it found 75 (19 with no intervening write tool, 5 with only read-only tools between). The ranker keys Bash and PowerShell calls by the stripped command text; on the KME-G smoke population that leaves 3 loose and 0 strict retries.
evidence: vault/programs/incremental-cognition/evidence/L.md:38-42 ; vault/programs/incremental-cognition/evidence/L.md:106-109 ; vault/programs/incremental-cognition/evidence/L.md:221-222 ; wiki/tools/kme_replay.py:152-156

### IC-D-05 -- a lapsed access token with a live refresh token is READY, not an expired login
level: domain
kind: trap
proposed_id: T-A-LAPSED-ACCESS-TOKEN-WITH-A-LIVE-REFRESH-TOKEN-IS-READY-NOT-EXPIRED-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: The env preflight reads an expired access token with no usable refresh token as NOT_READY (auth_expired, a7's measured state: expiresAt 0), but an access token that has lapsed while the refresh token is still valid as READY with the finding access_token_lapsed_refreshable; a lapsed token with no judgeable refresh expiry is UNMEASURABLE, never READY. Proven on scratch credentials files; the CLI's own refresh behaviour was not observed here.
evidence: vault/programs/incremental-cognition/evidence/B.md:140-145 ; tools/gex44_env_preflight.py:171-178 ; tools/test_gex44_env_preflight.py:154-158 ; tools/test_gex44_env_preflight.py:160-164

### IC-D-06 -- verification share on mission workloads is driven by verifier subagents
level: domain
kind: performance
proposed_id: PR-VERIFICATION-SHARE-ON-MISSION-WORKLOADS-IS-DRIVEN-BY-VERIFIER-SUBAGENTS-001
target: vault/knowledge_base/ukdl-cognitive-resource-os.md
statement: Pillar H's weighted verification share reads [7.30 %, 7.40 %] on KME-G and [8.73 %, 9.15 %] on GEX44-B001, both at or above 3 %, driven by verifier subagents (7 files on KME-G: kme-g1-ownership-arbiter x6, pp-code-reviewer x1; 3.90 M weighted); the test and gate tool calls plus output carriage are only about 0.2 to 1.25 %. Both are GEX44 workloads of the same kind of work, so this is a smoke reading, not a KME-L result.
evidence: vault/programs/incremental-cognition/evidence/phase3.md:80 ; vault/programs/incremental-cognition/evidence/phase3.md:203-207 ; vault/programs/incremental-cognition/evidence/phase3.md:10-13

## Project

### IC-P-01 -- a smoke measurement taken on another plane is instrument evidence, never terminal
level: project
kind: process-rule
proposed_id: PR-SMOKE-ON-ANOTHER-PLANE-IS-NEVER-TERMINAL-001
target: vault/programs/incremental-cognition/ukdl-candidates.md
statement: Every measurement committed from GEX44 is about the instrument, not the pillar: the denominator it ran on (KME-G, or the named GEX44-B001 workload) is outside each pillar's frozen rule (KME-L, laptop-plane), so the file carries evidence_role smoke and terminal_evidence false and the program done-gate (R3) refuses it as terminal. A KME-G figure is never stated as a KME-L result, never generalised to it, and an upper bound is never presented as a saving.
evidence: vault/programs/incremental-cognition/evidence/phase3.md:10-13 ; vault/programs/incremental-cognition/evidence/phase3.md:14-20 ; vault/programs/incremental-cognition/evidence/L.md:91-93 ; vault/programs/incremental-cognition/evidence/L.md:109-110 ; tools/test_incremental_cognition_program.py:419

### IC-P-02 -- the owner bundle is the mission's request, never the Owner's decision
level: project
kind: process-rule
proposed_id: PR-THE-OWNER-BUNDLE-IS-THE-MISSIONS-REQUEST-NEVER-THE-OWNERS-DECISION-001
target: vault/programs/incremental-cognition/ukdl-candidates.md
statement: An owner_decision evidence row is refused (R4) when its ref is the owner bundle in any spelling, a byte copy of it, or any file the mission wrote (anything under the program's evidence/ except the Owner's L-owner-decision file, anything under measurements/); identity is judged by os.path.samefile, the spelled tail, the sha256 and where a symlink really points, never by the spelling alone. The bundle asks; only the Owner's own file answers.
evidence: tools/test_incremental_cognition_program.py:46-52 ; tools/test_incremental_cognition_program.py:549-557 ; vault/programs/incremental-cognition/evidence/L.md:57-59 ; vault/programs/incremental-cognition/evidence/L.md:236-238

### IC-P-03 -- a laptop-plane command is recorded as a bundle line proven only to parse
level: project
kind: process-rule
proposed_id: PR-A-LAPTOP-PLANE-COMMAND-IS-RECORDED-AS-PROVEN-ONLY-TO-PARSE-001
target: vault/programs/incremental-cognition/ukdl-candidates.md
statement: The KME-L corpus and the laptop install are not on GEX44, so the Phase 3, 4 and 5 bundle commands carry the status NOT RUNNABLE HERE and are proven only to parse with the instrument's own argument parser (V-KMEP-BUNDLE-ARGV-PARSES, 11 commands, none rejected). What GEX44 could run (the code sync, scratch-clone replays) was run; the parse proof never stands in for an observed run on the laptop.
evidence: vault/programs/incremental-cognition/owner-bundle.md:215-216 ; vault/programs/incremental-cognition/evidence/phase3.md:119-124 ; vault/programs/incremental-cognition/evidence/L.md:112-122 ; tools/test_kme_pillars.py:2284

### IC-P-04 -- the D..I terminal gate trusts self-asserted front matter: a named debt
level: project
kind: trap
proposed_id: T-THE-DONE-GATE-TRUSTS-SELF-ASSERTED-FRONT-MATTER-A-NAMED-DEBT-001
target: vault/programs/incremental-cognition/ukdl-candidates.md
statement: The R3 gate believes a terminal_evidence claim only when the file's own fields agree with it, but terminal_claim_problems never parses the kmep-json block, so a hand-edited front matter that is internally consistent passes. It was recorded as named debt at the Phase 5 review fix, not closed; this candidate waits on that debt rather than stating a rule the gate does not yet enforce.
evidence: .planning/workstreams/incremental-cognition/STATE.md:56 ; tools/test_incremental_cognition_program.py:336-340 ; tools/test_incremental_cognition_program.py:434-436
