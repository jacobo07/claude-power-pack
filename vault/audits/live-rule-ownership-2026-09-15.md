# Live rule ownership — `~/.claude/rules/`

**2026-09-15.** Step 4 of the S+++ programme. The prior step closed command
durability and handed forward a suspicion: nine live rule files with no repo
source, in a domain the census did not model at all. This is the archaeology
that resolves who owns them.

The handoff's framing was *"the next live-only class"*. That framing is wrong,
and correcting it is the finding.

## The census, measured

Eleven files, not nine — the two PP mirrors live in the same tree and were
excluded from the earlier count by the same aperture that excluded the domain.

| file | bytes | mtime | repo source |
|---|---|---|---|
| `common/code-review.md` | 1772 | 2026-05-29 | ✅ identical repo-relative path |
| `python/testing.md` | 2516 | 2026-05-29 | ✅ identical repo-relative path |
| `capability-preserving-compaction.md` | 3833 | 2026-09-06 | ✗ |
| `concurrent-writers-shared-tree.md` | 7047 | 2026-09-10 | ✗ |
| `scoped-side-effect-authority.md` | 7059 | 2026-09-12 | ✗ |
| `evaluation-corpus-governance.md` | 10280 | 2026-09-10 | ✗ |
| `guard-event-reachability.md` | 11967 | 2026-09-15 | ✗ |
| `monetary-quantity-integrity.md` | 13920 | 2026-09-10 | ✗ |
| `real-context-reachability.md` | 21868 | 2026-09-14 | ✗ |
| `destructive-state-authorization.md` | 26836 | 2026-09-14 | ✗ |
| `instrument-before-claim.md` | 29710 | 2026-09-13 | ✗ |

## Ownership

### PP_CANONICAL — PROVEN (2)

`common/code-review.md` and `python/testing.md` each carry a self-declaring
provenance line — `> Mirrored from ~/.claude/skills/claude-power-pack/rules/…`
— plus ECC v2.0.0-rc.1 MIT attribution, sit at identical repo-relative paths,
and are already asserted by `V-GLOB-RULES-COMMON` / `V-GLOB-RULES-PYTHON` in
`tools/verify_globalization.py`. Both are recoverable today. PP's rule
durability has **no missing source**.

### OPERATOR_GLOBAL — HIGH-CONFIDENCE, not proven (9)

Cross-repo doctrine written by sessions in the operator's other repositories
directly onto the global surface. Five independent instruments agree, and no
instrument dissents:

1. **No repo source anywhere.** Absent from all 109 files of this repo's
   `rules/` tree and from the whole repo by filename.
2. **No front matter.** Every one opens on an `# H1`. PP's own materialiser
   stamps `origin: unattended-compound` / `run_at` / `source_project` /
   `signal_count` on anything it creates (`commands/compound.md`), so none of
   these came from it.
3. **PP's materialiser has never run.** `~/.claude/state/compound-learnings.json`
   → `"last_run_global": null`, read 2026-09-15. Not "ran and produced these" —
   never executed at all.
4. **Their own `## Source` sections name other repositories** — Orca X,
   Jacobo/Neom, CommonWealth Ops/TUA-X, GEO-audit, KobiiCraft, CodeEditorClone
   — and the compound state file independently confirms every one of those as a
   real registered project root. Two instruments, built differently, agreeing.
5. **No project-scoped copy exists.** None of Orca X, Jacobo, TUA-X or
   GEO-audit has a `.claude/rules/` directory. These files live in exactly one
   place on this machine.

Not PROVEN because there is no direct writer attribution: `~/.claude/` is not a
git repository, so the surface carries no history of its own.

**Evidence against my own thesis, recorded rather than omitted.**
`instrument-before-claim.md` lists *"2026-09-01 (Power Pack,
`modules/session_delta/delta.py`)"* among its source sessions. PP contributed a
case to that file's corpus. That is content authorship, not artifact ownership,
and per the PP-owned criteria a mention of PP inside a rule is not sufficient
evidence to claim it. The file is one rule assembled from six projects'
incidents; PP owns one paragraph of it and none of the artifact.

**Consequence: PP must not capture any of the nine.** Copying another
repository's doctrine into PP sources would manufacture a second canonical copy
of a file whose real author is elsewhere, and would put PP's name on work it did
not do. They are preserved, untouched, and classified.

## Reachability — the ladder, answered without a new instrument

All eleven are **injected into every session's context** as global instructions.
That is the top rung: not PRESENT, not LOADED, but AFFECTING DECISION. This
session followed `instrument-before-claim` while performing this very audit.

The instrument is the one that settled `rules/common/agents.md` in the previous
step, used in the opposite direction: a session's own injected instructions are
a reachability oracle. There, two sibling files appeared and the subject did not,
proving it dead. Here, all eleven appear, proving them live.

This also settles the scope question. `~/.claude/rules/` is **GLOBAL USER**
scope — host-native, unconditional, every project. Nothing about it is
project-scoped, which is precisely why writing to it from one repository has the
blast radius it does.

## The defect is latent, not historical

PP *does* claim this directory. `commands/compound.md` names
`~/.claude/rules/[name].md` as the materialisation target for `/cpp-compound`,
capped at three artifacts per unattended run, each stamped with provenance.
`.gitignore` line 116 records the same claim.

That claim has never been exercised — `last_run_global: null`. So:

> PP's rule-durability defect is not nine lost files. It is that the **first**
> PP-owned global rule ever written would be live-only and unrecoverable by
> construction, invisible to a census whose `DOMAINS` tuple omits `rules`
> entirely.

The PP-owned live-only rule population is **zero today**, and that is exactly
what made this invisible: an empty offender list satisfies every completeness
claim whether or not the check works. The correct target is therefore not
`live-only → 0` — nine of them legitimately stay. It is that the PP-owned class
cannot silently disappear, measured by a control that still fires when the class
is empty.

## The domain decision, measured before it was made

Adding `("rules", "**/*.md")` to the census aperture, measured in-process
against the real trees before any change was committed:

| domain | paired | live-only | repo-only |
|---|---|---|---|
| rules | **2** | **9** | 107 |

Deltas against the shipped baseline: `+2` paired, `+9` live-only, `+107`
repo-only, `0` duplicates. The baseline already carries 244 live-only rows — 189
of them `knowledge_vault` — and the producer's own contract is that a file
present on one side only is *inventory, never drift*. So the nine join an
existing, correctly-typed class; they are listed, not accused. No flood, no
false defects.

The 107 repo-only rows are equally true: this repo's language-scoped rule
taxonomy deliberately does not mirror, and only two of its files ever have.

### The coupling the measurement caught and reading would not have

`install_global_core._repo_population(repo, "rules")` returns `{}` today **only
because** `rules` is absent from `DOMAINS` — the function resolves its glob
through `dict(_md.DOMAINS)`. With the domain added it returns **109 entries**.

So the census extension *arms* the installer's population resolver for rules,
and the single thing preventing 109 repo files from being written into the
operator's home is `SHIPPABLE_KINDS = ("agents", "commands")` — a separate
tuple, three lines away, whose separateness is currently load-bearing and
undocumented.

Two apertures that were independent by accident are now independent by
consequence. That deserves a gate rather than a comment, because a comment
cannot fail.

## What this step does not claim

- No writer attribution for the nine. HIGH-CONFIDENCE, not PROVEN.
- No audit of whether the nine are internally consistent with PP doctrine; they
  are foreign and their content is not PP's to arbitrate.
- Cross-repo global writeback is **observed and judged intentional** — the files
  are written as universal doctrine, carry per-incident sourcing, and are in
  active use. Whether that mechanism should be governed is a separate question
  with a separate owner, and it is not opened here.
