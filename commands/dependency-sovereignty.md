---
description: What does each dependency cost the institution? Pin discipline, transitive surface, call-site load and the USE/WRAP/DO_NOT_USE ladder — with the unmeasurable parts named rather than assumed safe.
---

# /dependency-sovereignty

A dependency is a standing institutional liability, not a line in a manifest. Nothing in
this estate owned transitive surface, pin discipline, replacement cost or an
internalization threshold until this gate (UPAC residue R1,
`vault/audits/upac/SYSTEM_OWNERSHIP_OVERLAP_MAP.md`). `modules/cdicf` proved the licence
half is tractable — it read five upstream licence files and caught a Commons Clause a
README badge alone would have missed — but only for design-component absorption.

## Run it

```
python -m modules.dependency_sovereignty.sovereignty            # report
python -m modules.dependency_sovereignty.sovereignty --gate     # exit 1 on DO_NOT_USE
python -m modules.dependency_sovereignty.sovereignty --json
python -m modules.dependency_sovereignty.sovereignty --root <path>   # any repo
```

Also standing rows in the umbrella:

```
python tools/verify_spp.py --row dependency-sovereignty
python tools/verify_spp.py --row dependency-sovereignty-gates
```

## What the verdicts mean

| verdict | condition | what to do |
|---|---|---|
| `DO_NOT_USE` | unpinned constraint **and** no lockfile | the resolved version is whatever the registry serves at install time — pin it or add a lockfile before anything else |
| `WRAP` | ≥5 **observed** call sites | a breaking change edits every one; put it behind a single adapter |
| `USE` | exact pin **and** a lockfile | the installed graph is reproducible from this repo alone |
| `REVIEW` | anything else | not a pass — a decisive signal is UNKNOWN, and it says which |

## The part that makes it honest

Most of what a dependency review wants — CVE history, maintainer health, bus factor, API
stability, reimplementation cost — is **not measurable from a repo with no network**. The
failure to avoid is not lacking data; it is reporting a dependency as fine because the
evidence that would have condemned it was never fetched.

So evidence carries one of three states, and they never collapse:

- **MEASURED** — the repo witnesses it (pin, lockfile presence, call sites, vendoring).
- **UNKNOWN** — knowable, but this repo does not carry it (licence, transitive surface
  with no lockfile). Never rendered as zero or as a pass.
- **UNREACHABLE_HERE** — needs the network or a judgment about upstream.

Two consequences worth knowing before you read a report:

1. **Zero call sites does not mean lightly used.** A `vps/requirements.txt` describes a
   *remote* runtime whose code is outside the scan scope. Usage is reported UNKNOWN, not
   low, and cannot earn a favourable verdict.
2. **Four ladder rungs are deliberately not emitted** — `CONNECT`, `EXTEND`, `FORK`,
   `REPLACE`, and `INTERNALIZE`. Each needs upstream knowledge this gate does not have.
   `INTERNALIZE` is in that list because the first cut of this module *did* emit it, and
   recommended internalizing Pillow, PyYAML and Playwright. Import counts and pin strings
   do not carry reimplementation cost. The report prints the withheld rungs and why, so it
   states its own ceiling instead of implying the ladder has four rungs.

`--gate` blocks on `DO_NOT_USE` only. Everything weaker is advisory, because a gate that
blocked on UNKNOWN would block on almost everything and be turned off within a week.
