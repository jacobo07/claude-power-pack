---
status: passed
phase: 03-promote-the-exact-target-lessons
date: 2026-09-21
must_haves_verified: 3
must_haves_total: 3
---

# Phase 3 Verification — Promote the exact-target lessons

**Dir contents at verification time:** only `03-SUMMARY.md` (no PLAN, no
CONTEXT). Confirmed via `Glob`.

## Central-question framing — this SUMMARY repeats Phase 1's red flag

`03-SUMMARY.md` frontmatter self-declares `status: complete` and
`verification_status: passed` — the exact same self-grading pattern that was
found fraudulent in Phase 1 (where every cited artifact was absent). That
pattern alone earns zero trust here; every claim below was independently
re-derived from git history and file content rather than accepted from the
frontmatter or the prose. The outcome differs from Phase 1: here the
underlying deliverable is real and independently corroborated, but the
SUMMARY's own supporting citation for "Half 1" turned out to be evidence for a
**different, unrelated event**, not the one the roadmap asked for — a
documentation-accuracy defect, detailed below, distinct from Phase 1's
outright fabrication.

## Check 1 — do all 14 ids exist in the UKDL?

Grepped `vault/knowledge_base/ukdl-universal.md` for
`^### (HR-CONT-0[123]|PR-CONT-0[1234]|T-CONT-0[1234567])\b`. All 14 present:

| id | line | present |
|---|---|---|
| HR-CONT-01 | 10060 | yes |
| HR-CONT-02 | 10067 | yes |
| HR-CONT-03 | 10072 | yes |
| PR-CONT-01 | 10076 | yes |
| PR-CONT-02 | 10081 | yes |
| PR-CONT-03 | 10085 | yes |
| PR-CONT-04 | 10089 | yes |
| T-CONT-01 | 10093 | yes |
| T-CONT-02 | 10096 | yes |
| T-CONT-03 | 10099 | yes |
| T-CONT-04 | 10103 | yes |
| T-CONT-05 | 10108 | yes |
| T-CONT-06 | 10112 | yes |
| T-CONT-07 | 10120 | yes |

**14/14 present. VERIFIED.** (Headings render with a mangled em-dash,
`â€"`, an encoding artifact of that block, not a content defect.)

## Check 2 — does commit `1b2d6f4` exist and touch that file?

`git show --stat 1b2d6f4` (via absolute-path Git):

```
commit 1b2d6f425847a626f3cea45aa70674d82e7a36ca
Author: jacobo07 <jacobo@costaluzlawyers.es>
Date:   Sat Sep 19 11:33:24 2026 +0200
    docs(03): promote the exact-target continuation rules into the UKDL
    HR-CONT-01..03, PR-CONT-01..04 and T-CONT-01..05 move out of
    vault/lessons/exact-target-continuation.md ... T-CONT-06 ... T-CONT-07 ...
 vault/knowledge_base/ukdl-universal.md | 92 ++++++++++++++++++++++++++++++++++
 1 file changed, 92 insertions(+)
```

**VERIFIED.** This commit exists, touches exactly the named file, and its
message independently confirms it carries precisely the 14 ids found in Check
1 (3 + 4 + 5 base + 2 new traps = 14), sourced explicitly from
`vault/lessons/exact-target-continuation.md` — the file the roadmap named.
Corroborated a third way: that lessons file itself carries a header note,
`vault/lessons/exact-target-continuation.md:7-12`, reading *"PROMOTED
2026-09-19 in `1b2d6f4`"* and naming the same two new traps (T-CONT-06,
T-CONT-07). Three independent sources (UKDL content, commit message, origin
file's own marker) agree.

## Important finding: the SUMMARY's own "Half 1" citation is NOT this commit

`03-SUMMARY.md` cites a splice of `HR-CONT-04`, `T-CONT-12`, `T-CONT-13`,
`PR-CONT-06` (lines 10189–10220) as its evidence for "the UKDL carries the
rules with their ids." Grepped and confirmed those four ids are real and
present at exactly those lines — but they are **not** among the 14 ids the
roadmap named, and they do **not** appear anywhere in
`vault/lessons/exact-target-continuation.md` (grepped, zero hits for any of
the four). They are traced instead to commit `27a7094` ("ukdl: an advisory may
be layered on a load-bearing path, never swapped in", 2026-09-20), whose own
message states these four rows come from *"the 2026-09-20 continuation
work"* — a later, separate batch, unrelated to the lessons file this phase was
supposed to promote. Two sibling commits from the same day
(`d55c7c7`: T-CONT-08..11 + PR-CONT-05; `ea395ed`: 4 unrelated autocompact
rules) fill the numbering gap between T-CONT-07 and T-CONT-12/PR-CONT-06.

**Classification of this specific SUMMARY claim:** the cited content is
byte-accurate (VERIFIED as literally true — 43 lines staged, hunk-isolated,
matches `27a7094` exactly) but it is **evidence for the wrong thing**: it does
not demonstrate the roadmap's stated done-criterion. The done-criterion is
independently met anyway, via `1b2d6f4`, which the SUMMARY does not cite. This
is a documentation-accuracy defect in the SUMMARY, not a failure of the
underlying deliverable — the roadmap-mandated ids are genuinely present,
genuinely sourced from the named lessons file, and genuinely committed.

## Check 3 — router sentence in `~/.claude/CLAUDE.md`

This file is **outside** the `claude-power-pack` repo and is confirmed
unversioned (no git history to check; the SUMMARY flags this itself). Read
directly. The current "Context Pressure Response" section reads:

> "The daemon routes that line by SESSION id to the terminal inbox, and it is
> typed only if the extension that owns that terminal accepts — focus is never
> consulted, and neither is the window title. With no owning extension the
> request is REFUSED and ledgered, nothing is typed into whichever window is
> in front, and the Owner submits the line in the pane. The old
> foreground-SendKeys fallback is Owner opt-in only
> (`CPP_LEGACY_FOREGROUND_SENDKEYS=1`)... it is what typed
> `/absw2-continue` into a stranger's session on 2026-09-18."

**Content-level claim: VERIFIED.** This text does describe exact-or-refused
delivery, not "the SendKeys daemon presses Enter when Cursor is foreground."
The old stale sentence does not appear anywhere in the file as currently
read.

**Attribution: UNVERIFIABLE, stated as a limit, not a failure.** Because this
file carries no version history, there is no way to prove *this phase* made
the edit, that it wasn't already correct before, or when the change actually
landed. The content matching the claim today is the only evidence available;
who/when cannot be established.

## Check 4 — uncommitted CEPS rows

`git diff --stat -- vault/knowledge_base/ukdl-universal.md`:

```
vault/knowledge_base/ukdl-universal.md | 254 +++++++++++++++++++++++++++++++++
1 file changed, 254 insertions(+)
```

The diff content (read directly) is exclusively `ceps_*` auto-appended rows in
the same one-entry-per-two-lines shape described by the SUMMARY/commits.
**Current count: 254 uncommitted lines (~127 `ceps_` entries)**, not the
~1,029 recorded when the phase was written. This is a real drift downward
(some of the backlog was evidently swept up as incidental hunks inside later,
unrelated commits — `d55c7c7` alone shows a 90,507-byte / 337-row CEPS block
being carefully preserved-then-restored around a splice, and other commits in
the same window record similar handling). Per the task's own framing, **this
is an open Owner decision, not a gap**: the rows are still present, still
uncommitted, and this verification takes no position on whether they should
be committed, discarded, or left alone.

## Per-claim summary table

| Claim | Verdict | File read | Evidence |
|---|---|---|---|
| 14 named ids live in UKDL | VERIFIED | `vault/knowledge_base/ukdl-universal.md:10060-10120` | grep hit on all 14 |
| Sourced from `vault/lessons/exact-target-continuation.md` | VERIFIED | `vault/lessons/exact-target-continuation.md:1-12` | file's own "PROMOTED 2026-09-19 in `1b2d6f4`" marker |
| Commit `1b2d6f4` exists, touches the file, carries these ids | VERIFIED | `git show --stat 1b2d6f4` | commit message names exactly this set |
| SUMMARY's "Half 1" citation (HR-CONT-04/T-CONT-12/13/PR-CONT-06) proves the roadmap ask | CONTRADICTED (as a proof, though the cited content itself is real) | `git show --stat 27a7094`; `vault/lessons/exact-target-continuation.md` (no hits) | these 4 ids are real and committed, but are from unrelated 2026-09-20 work, not from the named lessons file |
| Router sentence now describes exact-or-refused delivery | VERIFIED (content); UNVERIFIABLE (attribution) | `C:\Users\User\.claude\CLAUDE.md`, "Context Pressure Response" | text matches; file has no version history |
| ~1,029 uncommitted CEPS rows | PARTIALLY STALE, not a gap | `git diff --stat -- vault/knowledge_base/ukdl-universal.md` | current count is 254 lines / ~127 entries |

## UNVERIFIABLE items — what would close them

- **Attribution of the CLAUDE.md router edit to this phase.** Would be closed
  by bringing `~/.claude/CLAUDE.md` under version control, or by a dated
  changelog entry in that file naming the phase/commit that made the edit.
- **Why the SUMMARY cites the wrong commit for Half 1.** Not closeable
  retroactively; noted here so a future reader does not re-cite `27a7094` as
  proof of the lessons-file promotion.

## What this phase does NOT establish

- **Activation/reachability** of the promoted rules — the SUMMARY says this
  itself ("promotion is not activation... nothing here measures whether any
  future session actually consults them"). Confirmed as an honest, correctly
  scoped limitation, not walked back by this verification.
- **That the router sentence was changed BY this phase** rather than already
  correct beforehand, or changed by unrelated work — the file's lack of
  version control makes this permanently unprovable from this repo.
- **Resolution of the uncommitted CEPS backlog** — explicitly an open Owner
  decision per the task framing, not evaluated for correctness here.
- **Requirement traceability** — no `REQUIREMENTS.md` exists in this project;
  n/a, not a gap.

## Verdict

**passed, 3/3 must-haves verified** (14 ids present and correctly sourced;
commit `1b2d6f4` exists and matches; router sentence content matches current
behavior). The roadmap's actual done-criterion is met, independently
corroborated three ways. The one substantive finding — that `03-SUMMARY.md`
cites a different, later, unrelated commit as its "Half 1" evidence instead of
the one that actually satisfies the ask — is reported as a documentation-
accuracy defect for the record, not scored as a failed must-have, since the
roadmap's actual requirement is independently satisfied by evidence this
verification located directly.
