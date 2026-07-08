# Testing Audit — KobiiSports Resort

> Global-Testing-Audit, 2026-07-08. Domain: Wii / videojuego (C/C++ homebrew on libogc +
> GX, built with devkitPPC; plus a Python ai-pipeline and a Unity sub-project). Repo:
> `.../Wii Projects/KobiiSports Resort/CursorProjects`. Verdict: the plan's hypothesis
> ("tests probables: ninguno") is **mostly right but not fully** — ad-hoc C test drivers
> exist, they just aren't independently runnable, and the one real unit surface (pure
> logic) is untested.

---

## AUDIT-A — Does a test suite exist?

Partially, in three disconnected forms:

1. **C test drivers** under `KobiSports_Fut/source/test/`: `jump1_test.c` (1.9 KB),
   `stress_test.c` (5.0 KB), `test_foundation.c` (9.5 KB), each with a `.h`. These are
   the closest thing to a Wii-side test suite.
2. **A C++ stats test** at `tools/caddie/test/test_kobii_mii_stats.cpp`, alongside two
   Python CI helpers (`run_at_canary_ci.py`, `run_stats_ci.py`) and a data generator
   (`gen_kobii_mii_dat.py`).
3. **A Python `ai-pipeline/tests/`** with `test_pipeline.py` (1 file), and a
   `uiux_wii_consistency/tests` dir. Plus a `KobiiSportsResort-Unity/docs/testing` (docs,
   not code). Total C/C++ source in-repo: 3,748 files; Python test files: 9.

Manifests: `Makefile` + `CMakeLists.txt` (+ several `Makefile.backup*` — a hygiene note
suggesting hand-edited build files). No unit-test framework (no Unity/Check/GoogleTest)
is wired; the C "tests" are hand-rolled drivers.

## AUDIT-B — Do the tests pass?

**Not independently runnable — this is the finding.** Inspecting `test_foundation.c`, its
`#include` list is `gx_state_manager.h`, `gx_profiler.h`, `gx_render_queue.h`,
`world_atmosphere.h`, `world_types.h`. These are engine/GX headers — the "test" links the
whole game subsystem, so it is an **integration smoke driver that runs on Wii hardware or
an emulator**, not an isolatable host-runnable unit test. Building it requires
`devkitPPC`. The environment has `C:\devkitPro` present but `DEVKITPPC` env unset, and per
STOP #1 I did not stand up the PPC toolchain (a heavyweight, side-effecting install).

So: the C test drivers were **not executed** (need devkitPPC + hardware/emulator); the
C++ caddie stats test was **not executed** (needs its build); the Python `ai-pipeline`
`test_pipeline.py` was **not run** in this pass (separate sub-project deps). Everything
here is recorded as *present in some form, not executed* — no green claim.

## AUDIT-C — What is not tested?

Nearly all pure, host-testable logic. A sports game has a large body of logic that has
*no* GX/hardware dependency: scoring rules, physics math (the `jump1` mechanic), stat
computation (`kobii_mii_stats`), state transitions, timing/rules enforcement. This is
exactly what *can* be unit-tested on a host with plain `gcc` and a minimal assert harness
— and almost none of it is isolated for that. `test_foundation.c` and `stress_test.c`
conflate logic with the render/atmosphere subsystem, so they can only run on-device.

The frame-budget contract (F6) — the defining quality bar for a Wii title — is
un-benchmarked in any host-runnable form, though the presence of `gx_profiler.h` suggests
on-device profiling exists.

## AUDIT-D — Failure taxonomy (F1–F8)

This is the most F-heavy repo in the stack, which is expected and honest for homebrew:

- **F1 (lógica sin test):** **Confirmed.** Pure game logic (scoring, jump physics, stats)
  has no isolated unit test. The logic is entangled with GX in the existing drivers.
- **F2 (integración sin contrato):** The C drivers *are* integration smoke tests, but
  they're not CI-runnable (need devkitPPC + emulator), so the integration contract is
  exercised manually at best.
- **F3 (edge cases):** Not observed. `stress_test.c` implies stress coverage but couldn't
  be run to confirm what it asserts.
- **F4 (regresión sin cobertura):** No regression-test culture observed for the C side.
- **F5 (producción sin monitor):** By construction — the game ships to hardware; no
  automated coverage runs in CI.
- **F6 (performance sin baseline):** **The signature Wii gap.** Frame budget is the whole
  game-feel contract; no host-runnable benchmark. On-device profiler exists but isn't a
  CI gate.
- **F7 (datos sin validación):** `.dat` generation (`gen_kobii_mii_dat.py`) exists;
  validation of malformed save/stat data not observed as tested.
- **F8 (seguridad sin test):** Not applicable in the usual sense — homebrew, no auth
  surface.

## AUDIT-E — Expandable frontiers

The realistic frontier for a Wii title is **not** "achieve SaaS-grade coverage" — it is
**extract the pure logic and test it on the host:**

1. Refactor scoring/physics/stats math into functions with zero GX/hardware includes.
2. Add a minimal host C test (plain `gcc`, no devkitPPC) with `assert()` on those pure
   functions — jump arc boundaries, score edge cases, stat computation. This is a small,
   high-value F1 fix that runs in seconds in CI with no toolchain.
3. Keep the GX-linked drivers as on-device integration/frame-budget checks (F6), run on
   an emulator in a heavier CI lane or manually before release.

The Python `ai-pipeline` and `caddie` stats tools are already host-testable and should be
run + baselined as a quick win independent of the Wii toolchain.

## Verdict and completion criterion

**Density: baja (ad-hoc C drivers + 9 Python files, none independently CI-runnable).
Health: UNVERIFIED (needs devkitPPC / sub-project deps). Defining gaps: F1 pure-logic +
F6 frame budget.**

The plan's hypothesis was substantially correct: formal testing is near-absent, as is
standard for homebrew. The refinement: some ad-hoc drivers exist, but they're
hardware-coupled, so the *host-testable pure logic* — the part that can fail silently and
cheaply be pinned — is the real opportunity.

**DONE for KobiiSports testing** = the pure game-logic functions (scoring, jump physics,
stats) are extracted from GX dependencies and covered by a host `gcc` assert harness that
runs in CI without devkitPPC; the Python `ai-pipeline`/`caddie` tests run with a recorded
baseline; and (stretch) the GX drivers run on an emulator lane as frame-budget/integration
checks. The done-gate is intentionally scoped to host-runnable logic — chasing on-device
100% coverage would be the wrong standard for the domain.

---

## Part II — Evidence appendix, test-debt inventory, and remediation detail

### II.1 Reproduced evidence (the hardware coupling)

The C "test" drivers under `KobiSports_Fut/source/test/`:

```
jump1_test.c        (1869 bytes)   jump1_test.h        (90 bytes)
stress_test.c       (4981 bytes)   stress_test.h       (1199 bytes)
test_foundation.c   (9479 bytes)   test_foundation.h   (841 bytes)
```

`test_foundation.c` include list (the coupling that makes it non-host-runnable):

```
#include "gx_state_manager.h"
#include "gx_profiler.h"
#include "gx_render_queue.h"
#include "world_atmosphere.h"
#include "world_types.h"
```

`gx_*` are the GX graphics pipeline headers (Wii GPU); `world_*` are engine state. A file
that includes these cannot compile on a host without the devkitPPC/libogc toolchain and
the GX headers — it is bound to the Wii target. Toolchain probe:

```
DEVKITPPC env: (unset)
C:\devkitPro exists: True
```

devkitPro is installed but `DEVKITPPC` is not exported, and standing up the full PPC
cross-compile + an emulator is a heavyweight side-effecting setup outside the agreed
AUDIT-B scope. So the C drivers were not executed — recorded as *hardware-coupled, not
host-runnable*, never as failed.

### II.2 The homebrew testing reality (honest domain framing)

Wii homebrew has no standard unit-test culture. There is no `libogc`-blessed test runner;
projects that test at all do so by running on hardware or in an emulator (Dolphin) and
observing behaviour. The plan's hypothesis ("tests probables: ninguno") is therefore
substantially correct as a *domain* statement. The refinement the audit adds is precision:
ad-hoc drivers DO exist (`jump1_test`, `stress_test`, `test_foundation`), but they are
integration smoke tests bound to the render pipeline, not isolatable unit tests — so the
*host-testable pure logic*, the part that can regress silently and cheaply be pinned, is
the real and addressable gap.

### II.3 What is host-testable but untested (the F1 opportunity)

A sports title carries a large body of hardware-independent logic:

| logic surface | example | host-testable? | currently tested? |
|---|---|---|---|
| jump/physics math | `jump1` arc, apex, landing | yes (pure math) | no (coupled to GX in driver) |
| scoring rules | point award, win condition | yes | no |
| Mii stat computation | `test_kobii_mii_stats.cpp` exists | yes | not run (needs build) |
| state transitions | match phase FSM | yes | no |
| frame budget | GX render timing | **no** (needs hardware/profiler) | on-device only |

Five of six surfaces are pure logic that could run under a host `gcc` + `assert()` harness
in seconds, with no devkitPPC. Only the frame-budget row genuinely requires hardware. The
existing `test_foundation.c` conflates the pure logic with the GX subsystem, forcing the
whole thing onto the Wii target unnecessarily.

### II.4 The three test forms, disentangled

1. **C drivers** (`source/test/*.c`) — hardware-coupled integration smoke. Keep as
   on-device/emulator checks; do not try to host-run them.
2. **C++ stats test** (`tools/caddie/test/test_kobii_mii_stats.cpp` + `run_stats_ci.py`,
   `run_at_canary_ci.py`) — closer to host-runnable; there is even CI-runner Python
   scaffolding (`run_*_ci.py`). This is the nearest thing to a real unit test and the
   quickest win to actually execute.
3. **Python `ai-pipeline/tests/test_pipeline.py`** (+ `uiux_wii_consistency/tests`) —
   fully host-runnable, independent of the Wii toolchain. Not run in this pass only
   because it is a separate sub-project with its own deps; it should be baselined as a
   trivial quick win.

### II.5 Test-debt inventory (F-heavy, as expected for homebrew)

| F-class | state | note |
|---|---|---|
| F1 pure logic | active | scoring/physics/stats not isolated for host test |
| F2 integration | manual only | C drivers need hardware/emulator, no CI |
| F3 edge cases | unknown | `stress_test.c` implies stress intent, unrun |
| F4 regression | none observed | no regression-test culture on C side |
| F5 production monitor | by construction | ships to hardware, no CI coverage |
| F6 frame budget | on-device profiler only | `gx_profiler.h` exists; not a CI gate |
| F7 data validation | partial | `.dat` generation exists; malformed-input untested |
| F8 security | n/a | homebrew, no auth surface |

### II.6 Concrete remediation (scoped to the domain, not SaaS-grade)

1. Extract pure logic (jump/physics math, scoring, stat computation, state FSM) into
   functions in headers that include **no** `gx_*`/`world_*` dependencies.
2. Add a host C test target (plain `gcc`, no devkitPPC) with `assert()` on those pure
   functions — jump arc boundaries, score edge cases, win-condition transitions. Runs in
   seconds in CI, no toolchain.
3. Execute `tools/caddie/test/test_kobii_mii_stats.cpp` via its existing `run_stats_ci.py`
   scaffolding and baseline it.
4. Run `ai-pipeline/tests/test_pipeline.py` and `uiux_wii_consistency/tests` (host Python)
   and baseline them.
5. Keep the GX drivers as an emulator/on-device integration + frame-budget (F6) lane, run
   before release rather than per-commit.
6. Hygiene: consolidate the multiple `Makefile.backup*` files (a hand-edited-build-file
   smell) into a single source of truth.

### II.7 What "good" looks like for KobiiSports Resort

"Good" is explicitly *not* SaaS-grade coverage — it is the right standard for the domain:
the pure game logic (scoring, physics, stats, state) runs under a fast host assert harness
in CI with no Wii toolchain; the Python and caddie tools run with baselines; and the
hardware-coupled GX drivers remain an emulator/on-device lane for integration and
frame-budget checks. The single highest-value move is decoupling the pure logic from GX so
it can be tested at all — an F1 fix that costs a refactor, not a test-framework adoption.
Chasing on-device 100% would be the wrong bar; pinning the silently-failing pure logic is
the right one.

---

## Part III — Standard cross-walk, done-gate checklist, and the stack lesson

### III.1 Cross-walk to the V-gates ×3 hermetic standard

- **AAA structure:** Partial and hardware-bound. The C drivers have an implicit
  arrange/act but their "assert" is on-device behaviour, not a host assertion. Extracting
  pure logic enables real AAA host tests.
- **Observed-evidence V-gates:** Not achievable on the C side today — no host-runnable
  output. The `run_*_ci.py` scaffolding around the caddie stats test is the nearest thing
  to a producible verdict and the quickest to activate.
- **Hermeticity ×3:** N/A for hardware-coupled drivers; pure-logic host tests would be
  trivially hermetic (no I/O, no GX). The Python `ai-pipeline` tests should be checked for
  the global-write pattern GEO-audit exhibited.

### III.2 Done-gate checklist (scoped to the domain)

- [ ] pure game logic (jump/physics/scoring/state) extracted from `gx_*`/`world_*` deps
- [ ] host `gcc` assert harness runs those in CI (no devkitPPC), recorded baseline
- [ ] `test_kobii_mii_stats.cpp` executed via `run_stats_ci.py`, baselined
- [ ] `ai-pipeline/tests` + `uiux_wii_consistency/tests` run (host Python), baselined
- [ ] GX drivers on an emulator/on-device lane as integration + frame-budget (F6) checks
- [ ] `Makefile.backup*` consolidated to one source of truth

### III.3 The lesson KobiiSports teaches the stack

KobiiSports teaches that **the right testing standard is domain-relative, and coupling is
the enemy of testability.** A Wii title cannot and should not be held to SaaS coverage
targets — but that does not excuse leaving the *host-testable* pure logic untested. The
defect here is architectural: scoring, physics, and stat math are entangled with the GX
render pipeline in the existing drivers, forcing everything onto the hardware target and
making the cheap, fast, hermetic host tests impossible. The generalizable rule: **decouple
pure logic from hardware/framework dependencies so it can be tested at all** — testability
is a design property, not a test-writing effort. The plan's hypothesis ("ninguno") was
right about formal frameworks but the audit's refinement matters: the gap is not "no test
culture exists," it is "the logic worth testing is trapped behind a GX dependency." Freeing
it is an F1 fix that costs a refactor, and it is the only move that turns an untestable
codebase into a testable one.
