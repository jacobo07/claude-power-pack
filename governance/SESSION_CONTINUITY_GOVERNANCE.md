# SESSION_CONTINUITY_GOVERNANCE.md — RESUMPTION_FILE for long work

> Normative. Domain: any task spanning more than one session.
> Origin: Hermes Personal Intelligence OS compendium (wave-by-wave authoring across
> context compactions).

## The problem
`/compact` cannot self-trigger — a slash command printed as assistant text is inert. On a
long build the context fills without being emptied, and a mid-run crash loses the thread.
State written to disk is the durable substitute for in-session autonomy.

## The rule
Any task that spans more than one session MUST keep a `RESUMPTION_FILE.md` at the project
root. It is a self-contained execution prompt — imperative, under 400 words, NOT a
narrative summary — that a fresh session reads to continue with zero prior context.

## Structure (five blocks)
1. Identity: project, path, one-line thesis.
2. Exact state: sealed vs pending units, plus a coherence anchor (counts that must match
   the project's index).
3. Active decisions that affect pending work.
4. The next 3 concrete actions, in imperative voice.
5. Start instruction: "read this file, then the index, then execute block 4; do not ask,
   do not explain."

## When to write
Update after EVERY sealed unit of work, never only at the end. Write proactively at ~65%
of estimated context, not at exhaustion — a mid-run crash must always leave a valid resume
point.

## Applies to
Any multi-day project, or any compendium of more than ~10 units of work.
