# USEA Constitution — Provenance Record

> Authority record for the Universal Software Engineering Architect constitutional
> payload. Read this BEFORE trusting any derived representation.

## What this directory holds

| File | Role | Authority |
|---|---|---|
| `constitution.raw.md` | The payload exactly as it arrived in-session | **Canonical** |
| `PROVENANCE.md` | This file — origin, integrity, fidelity claims | Metadata |

Derived representations (compiled rules, routing metadata, activation indexes,
capability maps) may be produced from the canonical file. **None of them may
become the only recoverable copy, and none of them is an independent semantic
owner.** The canonical file is the authority; every derivative retains a
provenance pointer back to it.

## Origin

- **Supplied by:** the Owner, in-session, on 2026-09-10.
- **Channel:** the `AskUserQuestion` answer field of this session.
- **First line:** `# UNIVERSAL SOFTWARE ENGINEERING ARCHITECT`
- **Last line:** `**RECONSTRUCT REALITY → UNDERSTAND CAUSALITY → IMPLEMENT MINIMALLY → VERIFY EMPIRICALLY → GENERALIZE ONLY WHEN PROVEN.**`

## Fidelity — read this before claiming exactness

The evidence state of the byte-fidelity claim is **INFERRED, not PROVEN**, and the
reason is specific and measurable:

The answer channel that carried the payload **collapsed its line structure**.
Markdown block boundaries were lost — headings concatenate directly onto the
following prose (`...AI Software Engineering AgentsYou are operating as...`) and
list items run together (`* Claude* Claude Code* ChatGPT`).

Two consequences, both stated plainly rather than papered over:

1. **The stored copy preserves every word and their order, but not the original's
   whitespace.** Semantic content — every law, every clause, every enumeration
   member — is intact and is what the ownership audit and the binder consume.
2. **Perfect reflow is not achievable and must not be attempted as a "restore".**
   The boundary between a heading's final word and the following paragraph's first
   word is genuinely ambiguous after collapse (`AgentsYou` could split before or
   after `You` on evidence available here). Any reflow is therefore a *guess*
   presented as a restoration — which is precisely the silent modification the
   exactness contract forbids. No reflowed variant is stored as canonical.

### To upgrade the fidelity claim to PROVEN

Save the Owner's original file to disk and replace `constitution.raw.md` with it
byte-for-byte, then record the resulting hash below. Until that happens, this
record must continue to say INFERRED. A hash computed over a transport-degraded
copy proves that *this file* has not changed since it was written; it does not
prove the file matches the Owner's source. Those are different claims and only
the weaker one is currently supported.

## Integrity

The hash below pins the stored bytes so later drift is detectable. It is a
tamper-evidence mechanism for the copy on disk — see the fidelity section above
for what it does **not** establish.

- **Algorithm:** SHA-256
- **Hash:** recorded by `tools/usea_corpus_gate.py --seal`
- **Drift gate:** `tools/usea_corpus_gate.py --verify` (non-zero on mismatch)

## Read-only contract

Following the precedent set by `modules/universal-meta-systems`
(`INTEGRATION_NOTES.md`, corpus HEAD `45dd1f9`): the integration **exposes** the
corpus, it never mutates it. `constitution.raw.md` is not edited to fix wording,
tighten prose, or reconcile it with Power Pack vocabulary. If the Owner revises
the constitution, the replacement arrives as a new sealed version with its own
hash and a superseding entry here — never as an in-place edit.
