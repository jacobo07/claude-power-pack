---
title: Universal Meta-Systems — Corpus Reference (read-only contract)
tier: reference
purpose: How to locate the read-only meta-systems corpus from any project, and the contract that governs reading it. The corpus is the source of truth; this module never modifies it.
---

# Corpus Reference

The seven meta-systems' doctrine lives in a **separate, read-only corpus**. This
module references it — it never copies it and never modifies it.

## Identity

- **Corpus:** `universal-meta-systems-corpus`
- **Pinned commit:** **`45dd1f9`** — *"universal-corpus-session-log-final:
  corpus complete, all gates PASS"*. All corpus DONE-gates pass at this SHA.
- **Remote:** none configured. The corpus is a **local artifact**, referenced by
  SHA + discovery order below — never by a public URL. If a project needs it and
  does not have it, obtain the corpus at commit `45dd1f9` from the Owner; do not
  fabricate a URL.

## Discovery order (how a project locates the corpus)

A project looks for the corpus in this order and uses the first that exists:

1. **Env var** — `$UNIVERSAL_META_SYSTEMS_CORPUS` pointing at the corpus root
   (the directory containing `MASTER_INDEX.md`).
2. **Sibling of the workspace** — a directory named `universal-meta-systems-corpus`
   next to, or one level up from, the project root.
3. **Owner default (this host)** — `C:\Users\User\Apps\universal-meta-systems-corpus`.

Verify the located directory is the right corpus by checking that
`MASTER_INDEX.md` exists at its root and that `git -C <root> rev-parse --short HEAD`
reports `45dd1f9` (or a descendant that still passes `DONE_GATE.md`).

If none of the three resolve, the meta-systems are still usable **conceptually**
from `index.md` + this module's summaries, but the full 18-Part datasets require
the corpus. Say so plainly rather than inventing dataset contents.

## What lives where (inside the corpus root)

| Path | Contents |
|------|----------|
| `datasets/MS-0_PROVENANCE_SUBSTRATE.md` | MS-0 full 18-Part dataset |
| `datasets/MS-1_COMPOSITION_FABRIC.md` | MS-1 |
| `datasets/MS-2_INTENT_COMPILER.md` | MS-2 |
| `datasets/MS-3_COMPOUNDING_SUBSTRATE.md` | MS-3 |
| `datasets/MS-4_CAPITAL_LEDGER.md` | MS-4 |
| `datasets/MS-5_EVOLUTION_INTEGRITY_FABRIC.md` | MS-5 |
| `datasets/MS-6_ABSENCE_ENGINE.md` | MS-6 |
| `phases/FASE0…FASE3_*.md` | The 4-phase discovery that justifies exactly these seven |
| `MASTER_INDEX.md` | Full navigation |
| `META_SYSTEM_REGISTRY.md` | Filter scorecards; the two killed candidates + reasons |
| `CAPABILITY_GRAPH.md`, `GAP_MATRIX.md` | The capability graph + gap→meta-system map |
| `COMPOUND_EFFECT_MAP.md` | How each dataset makes the others cheaper |
| `UNIVERSALITY_PROOF.md` | ≥5 distinct-domain instantiations per meta-system |
| `DONE_GATE.md` | Corpus-level verification incl. contamination scan |

## Read-only contract

1. **Never write** to any path under the corpus root. No edits, no appends, no
   "small fixes". If the doctrine seems wrong, that is a finding to report — not
   a file to change.
2. **Pin to `45dd1f9`.** Treat this SHA as the authoritative version. If the
   corpus has advanced, confirm the new HEAD still passes `DONE_GATE.md` before
   relying on it.
3. **Read only what the tier needs.** LIGHT reads none (use `index.md`);
   STANDARD reads one dataset; DEEP reads the loop-relevant few. Do not bulk-read
   all seven — each dataset is a full 18-Part document.
4. **Quote, don't paraphrase, the laws.** When applying a meta-system, cite the
   dataset's own laws and map your nouns onto them. Do not restate them loosely.
