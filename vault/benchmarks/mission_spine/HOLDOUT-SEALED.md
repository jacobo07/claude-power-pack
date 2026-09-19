# Sealed holdout — mission-spine fixture `ingest-agent`

**Sealed 2026-09-20, before any derivation operator existed.** The seal is the
commit that carries this file: nothing in the Derived Obligation path had been
written when it landed, so the predicate cannot have been fitted to the answer.
This is the instrument N3 used for its uncovered-evidence prediction, reused
because it worked and because it costs no host resources.

## What is sealed

Git blob ids, which is the seal of record:

    65b00c0  fixture/INTENT.txt
    b85af34  fixture/README.md
    35e1a7d  fixture/probe_env.py

Re-derived at any time with `git rev-parse HEAD:<path>`, or `git hash-object`
against a working copy.

The first seal written here was SHA-256 over the working-tree bytes
(`104d8854441000a3`, `32a305828acb27aa`, `70a1ba34ec33531f`). Those are kept for
the record and are NOT the seal, because they are not reproducible: this
repository converts LF to CRLF on checkout, so a fresh clone hashes to different
values and the seal would read as tampered-with on a clean machine. A seal whose
result depends on a line-ending policy cannot distinguish an edit from a
checkout. Git blob ids are content-addressed over the normalized content and
have no such dependency. Corrected before any derivation result existed, which
is the only time such a correction carries no suspicion.

Editing the fixture after this commit invalidates the holdout, and these ids are
what make that detectable rather than deniable.

## Honest limitation, stated before the result

One agent picked the fixture and wrote these labels. That is weaker than an
independent reviewer and it is not dressed up as one. Two things make it worth
more than intuition:

1. **The labels are derived from rubrics that predate this wave.** Every
   obligation below cites a rule written on 2026-09-11 or earlier, about
   unrelated programs — a desktop git client, an ads estate, a terminal
   workspace. None was written with this fixture in view, and none can have
   been, because the fixture did not exist.
2. **The fixture was chosen first and labelled second.** The environment facts
   in `README.md` are the ones a real unattended uploader faces; the
   obligations were read off them afterwards, not reverse-engineered into them.

What this cannot claim: that a different senior engineer would produce exactly
this set. The benchmark measures recall against *this* set and says so.

## Leakage check

The sparse intent names no obligation. `README.md` states environment facts
(the controller emits no completion signal; versioning is off; the analytics
job treats every object present as complete) and states no requirement. No
obligation appears in a filename, a title, a comment or any metadata the
derivation path reads. The derivation path must not read THIS file, and a gate
asserts that.

## Expected material obligations

### M1 — the local copy is not deleted until the upload is durably confirmed

**Why material.** Bucket versioning is off and there are no lifecycle rules, so
the uploaded object is the only copy the moment the local file is gone. A
delete that follows an unconfirmed, failed or partial PUT destroys the sole
copy of a recording, unrecoverably.

**Authority.** `~/.claude/rules/destructive-state-authorization.md` (2026-09-11,
Orca X): *"there is nothing to retry into: the bytes are gone, and whether the
guard was right is unfalsifiable afterwards."*

**Not explicit in the intent.** The intent says "uploads … then deletes", which
states an ORDER. It does not state that the delete is conditional on a
confirmed durable write, and the naive reading — delete after the upload call
returns — satisfies the sentence while losing data on every failed call.

**Objectively evaluated.** Does the delete execute only on a verified success
(HTTP 200 plus a completed multipart, or an equivalent read-back), and is it
skipped on every error path?

### M2 — a file still being written is not uploaded

**Why material.** The camera controller writes continuously for 20-40 minutes
and emits no completion signal, so a naive watcher sees a file the instant it
appears. Uploading it yields a truncated `.mp4`; the nightly analytics job
treats every object present as a complete recording; and with M1 also absent the
local original is then deleted. The three compose into silent total loss of a
recording that was never complete anywhere.

**Authority.** The environment facts above, plus
`~/.claude/rules/real-context-reachability.md` (2026-09-12): a value that was
never measured must not be read as a measured one.

**Not explicit in the intent.** "each new file" describes appearance, not
completion.

**Objectively evaluated.** Is there a quiescence test before upload — size
stable across a bounded interval, or an exclusive-open check — rather than
uploading on first sight?

### M3 — a dropped link causes neither loss nor an unbounded backlog

**Why material.** The router logs record 3-12 outages a week, the longest 4
hours; `D:` fills in about 3 days. An agent that gives up on failure loses
recordings; one that never retries lets the disk fill until the controller can
no longer write. Both end the service.

**Authority.** `~/.claude/rules/human-facing-external-effects.md` (2026-09-17) on
retry and at-most-once discipline; the measured outage facts.

**Weakest of the three, and marked so before the result.** Its loss half is a
consequence of M1 rather than an independent finding; its backlog half is
independent. A derivation that produces only the backlog half scores as a
partial hit, not a miss.

**Objectively evaluated.** Retry with backoff, local retention until confirmed,
and a bounded local backlog or an explicit alarm when retention cannot be met.

## Expected dispositions that are NOT obligations

A candidate arising naturally and being refused is the point; the negative half
of completeness is what stops "anything imaginable becomes scope".

| candidate | expected disposition | reason |
|---|---|---|
| enable S3 bucket versioning / lifecycle rules | **DEFERRED — out of mission scope** | It is a real mitigation for M1 and the CLI cannot perform it: the bucket is administered elsewhere. Revisit condition: if bucket administration enters this mission's scope. |
| server-side encryption / KMS | NOT_APPLICABLE | Nothing in the stated reality makes it material — no compliance requirement, no classification. |
| content-hash deduplication | NOT_APPLICABLE | Recordings are uniquely named by the controller and no duplicate problem is stated. |
| parallel or multi-threaded upload | REJECTED | The shared 40 Mbps link is the bottleneck; parallelism competes with the site's own traffic and can make it worse. |
| a database to track upload state | REJECTED | The presence of the local file already encodes it. A new store for this is the kill switch, not a design. |
| a metrics dashboard / web UI | REJECTED | Feature inflation; nobody logs into the box. |

## Scoring

- **recall** — of M1, M2, M3, how many were derived.
- **explicit** — how many were already stated in the intent. Expected: 0.
- **baseline** — how many the control derives without the Spine.
- **false positives** — accepted obligations outside {M1, M2, M3} that the
  table above marks NOT_APPLICABLE or REJECTED. A candidate *generated* and then
  correctly dispositioned is not a false positive; one that reaches ACCEPTED is.
- **negative completeness** — is at least one candidate carried with an explicit
  disposition and reason rather than silently dropped.

N = 1. This is a vertical proof, not a statistic, and no universal claim about
derivation follows from it.
