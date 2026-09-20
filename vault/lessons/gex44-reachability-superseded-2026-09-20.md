# GEX44 reachability — SUPERSEDES the 2026-04-21 "firmware-broken" record

**Date measured:** 2026-09-20 · **Scope of this correction: REACHABILITY AND
CAPACITY ONLY.** It does not touch any other GEX44 claim, and §3 below names
what it deliberately leaves standing.

## What the estate believed

`modules/governance-overlay/mistake-frequency.json` carries two entries dated
2026-04-21 recording that a prompt asserted GEX44 as live hardware while the
handoff of 2026-04-19/20 had it **firmware-broken, confirmed by Hetzner, with
the project pivoted to Runpod**. Those entries were correct on the day they were
written and are preserved unedited — this file supersedes, it does not overwrite,
because a record of what was believed is itself evidence.

## What is true now

Measured directly over `ssh gex44`, `BatchMode=yes`:

| | measured 2026-09-20 |
|---|---|
| reachable | **yes**, Ubuntu 24.04.3 LTS, kernel 6.8.0-134 |
| CPU | 20 cores, `vmx` on 40 threads |
| RAM | **59.9 GB available** of 64 GB, 16 GB swap |
| disk | 248 GB free, **86 % used** — admission-check territory |
| `/dev/kvm` | node **exists**, and is **not readable by `kobii`** |
| GL | `llvmpipe (LLVM 20.1.2)` — **software rendering, no GPU** |
| present | `Xvfb`, `ffmpeg`, `glxinfo`, `java`, `python3`, `pip3`, `curl`, **`dolphin-emu`** |
| absent | `adb`, `sdkmanager`, `unzip`, `aapt`, `docker`, any Android SDK |

## 1. The instrument lesson, which is the durable part

The first probe tested `test -e /dev/kvm` and reported `KVM_YES`. The second
tested `-r` and reported `kvm_ok=no`. **Both ran, both were correct about what
they asked, and only the second was about the question.** Existence is not
access. A capability that is present and unreachable reports as present to any
instrument that asks the easy question, and `-e` is the easy question.

Corollary already in the rules and confirmed again here: when two instruments
disagree, read the disagreement before picking a favourite.

## 2. The staleness lesson

A five-month-old infrastructure record read as current fact would have sent this
session to the wrong conclusion — it is what made "the RAM wall is unsolvable"
look true when the answer was a machine with 60 GB free. Infrastructure claims
decay faster than the doctrine written beside them, and nothing re-checks a
sentence. **An infrastructure record needs a measured-on date and a re-probe
before it is load-bearing**, and the probe is one `ssh` call.

## 3. What this correction does NOT void

- `knowledge_vault/core/BL-2026-05-22-gex44-nvidia.md` — the NVIDIA driver-
  mismatch class **stands**, and this session's `llvmpipe` reading independently
  corroborates it: no GPU is reachable from `kobii`, by either account.
- `apex-completion-standard.md:2267` — GPU Eyes having been empirically tested
  against gex44 **stands**; it is a claim about the past.
- The 19-entry `gex44_antipatterns` corpus and its `vault_index.json` route —
  untouched, and out of scope for a reachability correction.
- The Runpod pivot **happened**. Whether it should be reversed is an Owner
  decision this file does not make.

## 4. UKDL candidates from the same session

| level | candidate |
|---|---|
| TRAP | Existence is not access: `test -e` on a device node answers a different question than `-r`, and the easy question is the one that reports success. |
| TRAP | An infrastructure record without a measured-on date is read as current by every later session. Re-probe before it is load-bearing. |
| PROCESS | A capability contract whose costs are all `medium` scales posture by evidence strength: one trigger → RECOMMENDED, two → MANDATORY. Deliberate tuning, and the reason a single stray word cannot buy a DEEP tier. |
| PROCESS | Make an incumbent reachable with a contract before writing a module. `modules/osr` held the differential core with **zero** production callers; one contract file made it reachable and added no code. |
| HARD | A posture change belongs in a contract, never in `tier.py`. Its docstring says "this module is not a new decider", and an edit that raises posture there installs the second decider it exists to refuse. |

## Provenance

Every row in the table above came from a live `ssh gex44` probe in the session
of 2026-09-20, transferred as a UTF-8-no-BOM LF script through
`cmd /c "ssh ... bash -s < tmp"` after a PowerShell here-string interpolation ate
the remote `$d`/`$b` variables — the documented Windows→ssh quoting trap, pivoted
on the first failure rather than the third.
