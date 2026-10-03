---
name: develop-here-prove-there
description: Development-plane vs validation-plane doctrine. Use when the machine you code on is not the one that can run the thing honestly (emulator on a GPU box, device lab, staging, a phone, a remote host): naming which plane observed a claim, pinning the instrument configuration, hashing the artifact that actually ran at both ends, evidence bundles and currency gates, comparators with four outcomes, A/A before A/B, and fixtures that must never touch real data on the validation host. Core rule - a runtime claim names the plane that observed it, or it is not a claim.
metadata:
  opportunity_detector: none
  opportunity_detector_reason: coverage class none; no registered card hook and no CO-12 adapter names this skill
---

# Develop Here, Prove There

When the machine you write code on is not the machine that can run it honestly — a
console emulator on a GPU box, a device lab, a staging cluster, a phone — the two are
not interchangeable, and the failure is not that you used the wrong host. It is that a
result crosses between them carrying no record of which one produced it.

> **The development plane optimizes speed of engineering. The validation plane owns
> every runtime verdict. A claim names the plane that observed it, or it is not a claim.**

## The cycle

    edit / search / static + host tests / build   LOCAL   (fast, cheap, interruptible)
    commit a causal unit                          LOCAL
    run, capture, measure                         VALIDATION PLANE (authoritative)
    ingest the evidence bundle, diagnose          LOCAL
    silicon / production only for what the validation plane cannot answer

Keep a written table of which plane owns which capability, and a tier vocabulary so a
handoff cannot say "proven" without naming the authority. Tiers that have worked:
`STATIC`, `LOCAL-HOST`, `LOCAL-<plane>-AUXILIARY`, `<plane>-PROVEN`, `PACKAGED/RUNTIME`,
`SILICON`. The auxiliary tier matters most: it lets local runtime work stay useful and
stop being evidence, so nobody has to delete it to keep the record honest.

## An instrument is a CONFIGURATION, not a host

This is the trap that looks like a plane difference and is not. Two hosts running the
same binary produced different capture geometries, which was written down as "the
planes are different instruments". Measured properly, one host had inherited a settings
file the other did not: under identical configuration both produced identical bytes.

- **Before attributing a difference to a host, equalize the configuration.** Otherwise
  you will build doctrine on a settings file.
- **Pin the instrument as a committed artifact** — a config file copied into a private
  runtime directory per run, hashed into the evidence — never a shared file a neighbour
  edits. A shared config is a variable with no changelog.
- **A setting that the tool accepted is not a setting the tool applied.** A command-line
  override was accepted and silently ignored; the same key in a config file was honoured.
  Record the resulting property (the codec, the resolution, the locale) in the evidence
  and have the gate REFUSE anything else, or a silent fallback looks like a good run.
- **A lossy capture layer imports the thing you excluded.** Frame-wide rate control let
  a moving background change the encoded bytes of a static region: 17% of that region's
  pixels moved between frames of one run. Under a lossless codec the same region was
  byte-identical. If you are measuring a subject, capture it losslessly or you are
  measuring the encoder.

## Identity is captured, never reconstructed

- **Source identity is not artifact identity.** Two clean builds of one commit differ in
  the bytes of an embedded build clock. Record the hash of the artifact that **actually
  ran**; never infer it by rebuilding later.
- **Hash at both ends of every transfer**, and again on the machine at launch.
- **Build from a clean checkout when the tree is shared.** A build from a working tree
  another writer is editing produces an artifact that matches no commit.
- **Prefer transferring the artifact over rebuilding remotely** when the remote toolchain
  is unproven: a hash comparison is stronger evidence than a second build.

## The evidence bundle, and the currency gate

A remote run returns a bundle, not a verdict: commit, artifact hash at both ends, input
tree manifest, runtime configuration and version, the full command, run id, UTC bounds,
inputs sent with timestamps, every captured artifact by hash, and the hashes of the tools
that will judge it.

Then a **currency gate** refuses a verdict unless every link is present and consistent,
and says `UNJUDGED`, never `PASS`, when one is missing. Give it a **positive control** — a
genuinely good run that must come back current. Mine had a relative-versus-absolute path
bug that would have refused every legitimate run; only the positive control could find it,
because a gate that refuses everything satisfies every refusal test.

## Comparators: four outcomes, and refuse before you compare

A comparator that cannot say "I could not judge this" will eventually say PASS about
nothing. One printed REPRODUCIBLE having computed no hash at all: a helper name collided
with a shell alias, both operands were empty strings, and empty equals empty.

The same trap lives one layer down in whatever you are comparing. A capture taken before
the system drew anything is a uniform frame; it loads fine, and two of them are identical.
So validate operands **before** comparing: unreadable, empty, wrong geometry, wrong shape,
**degenerate** (carries no signal), or the reference compared with itself — each is a
refusal with its own reason. One unjudged member makes the aggregate unjudged.

And **a verdict is about the subject that was judged**: if the caller asked for a region,
equality means that region. Mine reported whole-frame equality under a region request, and
the test written beside it had pinned the defect.

## A/A before A/B, on the authoritative plane

Measure what independent, unchanged runs produce before changing anything. Predeclare, in
a committed file, before the first counted run: the subject, the per-run validity checks,
the decision table and the thresholds. A threshold chosen after seeing the numbers is not
a threshold.

- **Isolate the variable.** A subject that animates measures time plus your change. Prefer
  a region the interface itself makes static (an opaque panel over a moving background) to
  compensating for noise you could have excluded.
- **Per-run controls that can fail:** the subject is stable *within* the run; the
  comparator rejects a deliberately perturbed copy of that run's own capture; a known-bad
  capture (the pre-boot frame) is refused. Without the second, a comparator that answers
  MATCH to everything passes every A/A.
- **An invalid run is replaced, never averaged in**, and a bounded number of replacements
  before you stop and call the instrument unreliable.

## Never let the fixture be someone's real data

A fixture safe on one plane is not safe on another: locally there was nothing to lose, and
on the validation host the same navigation path focused a heritage record and one keypress
would have overwritten it.

- **Build the fixture so the hazard cannot be reached**, rather than navigating around it:
  an image whose only record is disposable cannot focus a real one. Prove that from the
  fixture's own manifest before use, and again per run.
- **Make the destructive input unrepresentable** — an allow-list that refuses the key, not
  a comment saying not to send it.
- **Do not lock the shared resource just because you are careful.** Another programme was
  legitimately using the real data; a read-only lock would have broken a live neighbour.
  Hash it before and after as a **witness** instead, and say so.
- **Restore by writing the exact bytes back, not by rolling back a snapshot**, and verify
  by reading them out again. Container identity may legitimately differ (allocation,
  timestamps) while the content tree is identical — compare the tree digest, and say which
  one you are claiming.

## DON'T

- **Don't read "the tool is present" as "the toolchain is configured."** Present,
  discoverable, configured and complete are four states; 26 build failures were reported
  as a missing tool that was on disk the whole time, missing only two environment variables.
- **Don't let a shared checkout's dirty set surprise you.** Bracket long operations on the
  set of dirty paths; a path that appears mid-run belongs to another writer, not to you.
- **Don't retry a call that failed twice the same way.** Pivot the mechanism. Three of my
  edits died on the same host-side gate; the fix was to move the work to a different file,
  not to send it a fourth time.
- **Don't route around a refusing safety gate** because you believe your content is safe.
  An unenforced gate is not permission; record the owed work instead.

## Source

Incident evidence moved to `~/.claude/knowledge_vault/rules-evidence/develop-here-prove-there.md` (2026-09-28) so it is not re-read on every call. The rule text above is unchanged.
