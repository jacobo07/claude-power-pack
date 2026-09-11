"""SQI-03 — the Environment Qualifier. Qualification precedes interpretation.

A result from an unqualified environment is a result whose meaning has not been
established. The qualifier runs the short-circuiting sequence named in GATES -- that list
is the only place the count lives, because a number written into prose beside a list goes
stale while still reading as a measured fact; the first gate that fails sets
the state, records the blocker VERBATIM, and renders every downstream gate UNKNOWN --
never skipped, never assumed, never passed by omission (SQI-03 3.9). An omitted gate
reads as an absent concern; an UNKNOWN gate reads as an open question, and the difference
between those readings is the difference between an estate that closes its gaps and one
that cannot see them.

The default state is UNKNOWN (3.10). QUALIFIED is earned by affirmative observation with
the command and its output retained -- never by the absence of a complaint. No state may
be assigned by reasoning (4.10): an agent that concludes an environment is qualified
because it can see no reason it would not be has produced a hypothesis, and a hypothesis
cannot license the one state that unlocks product attribution.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Exhaustive by construction (SQI-03 4.1). A binary would be cheaper and catastrophic:
# it collapses conditions that license entirely different actions, and once collapsed at
# the point of measurement no downstream consumer can recover the distinction.
QUALIFIED = "QUALIFIED"
PARTIALLY_QUALIFIED = "PARTIALLY_QUALIFIED"
BLOCKED = "BLOCKED"
HARDWARE_REQUIRED = "HARDWARE_REQUIRED"
UNSUPPORTED = "UNSUPPORTED"  # a policy decision; an agent may NEVER assign it (4.6)
UNKNOWN = "UNKNOWN"

GATES = [
    "host_census",
    "toolchain_presence",
    "toolchain_version",
    "dependency_resolvability",
    "build_reachability",
    "service_availability",
    "harness_containment",
    "host_capacity",
]

# The verdict ceiling each state imposes (SQI-03 4.9). This is a ceiling, not an
# assignment: QUALIFIED licenses any verdict the evidence supports and is the ONLY state
# that licenses attributing a failure to the product.
VERDICT_CEILING = {
    QUALIFIED: "any",
    PARTIALLY_QUALIFIED: "per-surface; UNVERIFIED or BLOCKED for the unobserved",
    BLOCKED: "BLOCKED",
    HARDWARE_REQUIRED: "UNVERIFIED",
    UNSUPPORTED: "WAIVED-WITH-LIABILITY",
    UNKNOWN: "UNVERIFIED",
}


@dataclass
class GateResult:
    gate: str
    passed: bool | None  # None == UNKNOWN. Never coerce to False.
    observed: str
    command: str | None = None
    blocker: str | None = None  # verbatim, never paraphrased


@dataclass
class EnvironmentRecord:
    state: str
    gates: list[GateResult]
    host: dict
    toolchains: dict
    lock_state: dict
    blockers: list[str]
    verdict_ceiling: str = UNKNOWN
    env_hash: str = UNKNOWN
    error: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["gates"] = [asdict(g) for g in self.gates]
        return d


def _run(argv: list[str], cwd: Path, timeout: int = 30) -> tuple[int, str]:
    """Never raises. A tool that cannot be invoked is an observation, not an exception."""
    try:
        p = subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True,
            timeout=timeout, errors="replace",
        )
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()
    except FileNotFoundError:
        return 127, f"executable not found: {argv[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {' '.join(argv)}"
    except OSError as exc:
        return 126, f"{exc}"


@dataclass
class Workload:
    """What a caller is about to ask of the host, in the caller's own terms.

    Declared, never inferred. This module cannot know whether it is being asked about a
    single unit test or an eighty-row parallel sweep, and the identical headroom is
    generous for the first and fatal for the second. A gate that guessed would be wrong
    in whichever direction the guess was cheap.
    """

    name: str
    peak_mb_per_unit: int          # peak RSS of ONE unit of work, measured or estimated
    units_in_flight: int = 1       # parallelism; 1 for a serial run
    reserve_mb: int = 1024         # what the rest of the machine still needs to live on

    @property
    def required_mb(self) -> int:
        return self.peak_mb_per_unit * max(1, self.units_in_flight) + self.reserve_mb


# A factor over the DECLARED requirement, not a fraction of the host. Sized so that a run
# whose own footprint is small is not refused by a busy machine, and one whose footprint
# is large is not admitted by a roomy one. The incident host sat at 6.8% free; that number
# is evidence about one afternoon, and canonising it would gate every future workload on
# the shape of a single failure.
CAPACITY_MARGIN = 1.5


def _avail_psutil() -> int | None:
    try:
        import psutil  # noqa: PLC0415 -- optional dependency, probed not required
        return int(psutil.virtual_memory().available // (1024 * 1024))
    except Exception:
        return None


def _avail_windows() -> int | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes  # noqa: PLC0415

        class _MemStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        st = _MemStatus()
        st.dwLength = ctypes.sizeof(_MemStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st)):
            return int(st.ullAvailPhys // (1024 * 1024))
        return None
    except Exception:
        return None


def _avail_posix() -> int | None:
    try:
        pages = os.sysconf("SC_AVPHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
        return int(pages * size // (1024 * 1024))
    except (ValueError, AttributeError, OSError):
        return None


def available_mb() -> int | None:
    """Physical memory a new process could actually obtain, in MB.

    None means "could not look", never "looked and found nothing" -- the same distinction
    modules/execution_env draws for git. Three probes because the first is an optional
    dependency and the estate must not acquire one to be able to refuse a run.
    """
    for probe in (_avail_psutil, _avail_windows, _avail_posix):
        got = probe()
        if got is not None:
            return got
    return None


def capacity_probe(workload: Workload | None,
                   observed_mb: int | None = None) -> GateResult:
    """Can this host sustain this workload long enough for its result to mean anything?

    Three outcomes, and the middle one is the point. A run the host can certainly carry
    and a run the host will certainly kill are easy; the interesting state is the one
    where it may complete or may be killed, and reporting that as either a pass or a
    failure is how a killed sweep came to be narrated as a verdict.

    ``observed_mb`` exists so a caller can pass a reading it already took -- and so the
    red branch can be driven without waiting for a real machine to run out of memory.
    """
    avail = available_mb() if observed_mb is None else observed_mb

    if workload is None:
        return GateResult(
            "host_capacity", None,
            "no workload declared; capacity is not evaluable in the abstract",
        )
    if avail is None:
        return GateResult(
            "host_capacity", None,
            f"host memory not measurable on {sys.platform}; "
            f"{workload.name} would require {workload.required_mb} MB",
            blocker=f"host capacity unmeasurable for {workload.name}",
        )

    need = workload.required_mb
    observed = (
        f"{workload.name}: {avail} MB available, {need} MB required "
        f"({workload.peak_mb_per_unit} MB x {max(1, workload.units_in_flight)} in flight "
        f"+ {workload.reserve_mb} MB reserve)"
    )
    probe_cmd = "available_mb() [psutil|GlobalMemoryStatusEx|sysconf]"

    if avail < need:
        return GateResult(
            "host_capacity", False, observed, command=probe_cmd,
            blocker=f"insufficient host memory: {avail} MB available, "
                    f"{need} MB required for {workload.name}",
        )
    if avail < need * CAPACITY_MARGIN:
        return GateResult(
            "host_capacity", None,
            observed + f" -- inside the x{CAPACITY_MARGIN} margin; this run may "
                       "complete or may be killed, and which one happens is not a "
                       "fact about the subject",
            command=probe_cmd,
            blocker=f"host capacity marginal for {workload.name}: {avail} MB "
                    f"against {need} MB required",
        )
    return GateResult("host_capacity", True, observed, command=probe_cmd)


def qualify(cwd: str | Path, profile=None,
            workload: Workload | None = None) -> EnvironmentRecord:
    """Qualify the host for this repository. Fail-open: any gate that cannot be evaluated
    is UNKNOWN, and an UNKNOWN gate is a hard ceiling on interpretation -- never a pass."""
    root = Path(cwd).resolve()
    gates: list[GateResult] = []
    blockers: list[str] = []

    # ---- Gate 1: host census -------------------------------------------------------
    host = {
        "platform": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "cwd": str(root),
    }
    gates.append(
        GateResult("host_census", True, f"{host['platform']} {host['release']} / py{host['python']}")
    )

    # ---- Gate 2: toolchain presence ------------------------------------------------
    langs = [c.language for c in profile.language_contexts] if profile else ["python"]
    toolchains: dict = {}
    missing: list[str] = []
    probes = {
        "python": [sys.executable, "--version"],
        "elixir": ["mix", "--version"],
        "java": ["java", "-version"],
        "javascript": ["node", "--version"],
        "c": ["gcc", "--version"],
    }
    for lang in langs:
        argv = probes.get(lang)
        if not argv:
            toolchains[lang] = UNKNOWN
            continue
        if shutil.which(argv[0]) is None and not os.path.isabs(argv[0]):
            toolchains[lang] = "ABSENT"
            missing.append(lang)
            continue
        rc, out = _run(argv, root, timeout=20)
        toolchains[lang] = out.splitlines()[0] if (rc == 0 and out) else "ABSENT"
        if toolchains[lang] == "ABSENT":
            missing.append(lang)

    present = [l for l in langs if toolchains.get(l) not in ("ABSENT", UNKNOWN)]
    if not present:
        blocker = f"no toolchain present for any detected language: {langs}"
        blockers.append(blocker)
        gates.append(GateResult("toolchain_presence", False, "none present",
                                blocker=blocker))
        gates.extend(GateResult(g, None, "not evaluated (short-circuit)") for g in GATES[2:])
        return EnvironmentRecord(
            state=BLOCKED, gates=gates, host=host, toolchains=toolchains,
            lock_state={}, blockers=blockers, verdict_ceiling=VERDICT_CEILING[BLOCKED],
        )

    gates.append(
        GateResult("toolchain_presence", True, f"present: {present}; absent: {missing}",
                   command="|".join(probes[l][0] for l in present if l in probes))
    )

    # ---- Gate 3: toolchain version compatibility -----------------------------------
    # A build that fails before a single test is collected is an ENVIRONMENT finding
    # routed to BLOCKED, never a product finding routed to FAILED (SQI-01 4.4). An
    # engineer dispatched to repair correct code will succeed in changing it until the
    # broken environment stops complaining, and every test will be green.
    gates.append(
        GateResult("toolchain_version", True,
                   "; ".join(f"{k}={v}" for k, v in toolchains.items() if v != "ABSENT"))
    )

    # ---- Gate 4: dependency resolvability ------------------------------------------
    lock_state = {c.language: c.lock_state for c in profile.language_contexts} if profile else {}
    unlocked = [l for l, s in lock_state.items() if s == "UNLOCKED"]
    if unlocked:
        # This is the Elixir case from the founding audit: a manifest declaring the usual
        # dependency set, no resolved lock, and 149 test files across two repositories
        # rendered unverifiable -- not failing, unverifiable.
        gates.append(
            GateResult("dependency_resolvability", None,
                       f"manifest present with no resolved lock: {unlocked}",
                       blocker=f"unlocked dependency set: {unlocked}")
        )
    else:
        gates.append(GateResult("dependency_resolvability", True,
                                f"lock states: {lock_state or 'no lock convention'}"))

    # ---- Gate 5: build reachability ------------------------------------------------
    # Read-only: we do not build. We observe whether the runner can be *invoked*. The
    # reconciliation engine performs the collection and reports the real blocker.
    if "python" in present:
        rc, out = _run([sys.executable, "-m", "pytest", "--version"], root, timeout=30)
        if rc == 0:
            gates.append(GateResult("build_reachability", True, out.splitlines()[0],
                                    command="python -m pytest --version"))
        else:
            blockers.append(out)
            gates.append(GateResult("build_reachability", False, "runner not invocable",
                                    command="python -m pytest --version", blocker=out))
    else:
        gates.append(GateResult("build_reachability", None,
                                "no python context; build reachability not probed here"))

    # ---- Gate 6: service availability ----------------------------------------------
    # No repository in this estate declares a required external service for its Python
    # suite. An absent declaration is recorded as an absent declaration, not as a pass.
    gates.append(GateResult("service_availability", None,
                            "no external service contract declared; not evaluated"))

    # ---- Gate 7: harness containment -----------------------------------------------
    # Fires INDEPENDENTLY of test outcome (SQI-03 3.8): on the run where the pollution
    # does not collide with a sibling, nothing fails, and an outcome-driven detector sees
    # a clean pass while the environment silently degrades for the next one. Evaluating
    # this properly requires a differential filesystem observation around a real run,
    # which this read-only pass does not perform. It is UNKNOWN, and says so.
    gates.append(GateResult("harness_containment", None,
                            "requires a differential observation around a run; not performed"))

    # ---- Gate 8: host capacity -----------------------------------------------------
    # Added 2026-09-11 after an 82-row sweep was killed by the OS at 2181 MB free of
    # 32061 MB and the killed run was first narrated as still running. Gates 1-7 could
    # all pass on that host: the toolchain was present, the runner was invocable, the
    # locks resolved. Nothing in this module could see the only condition that mattered.
    #
    # Deliberately NOT a percentage of the host. The same 8% headroom is ample for one
    # unit test and fatal for a parallel sweep, so the requirement is declared by the
    # caller and the gate compares against it. A workload nobody declared is UNKNOWN,
    # never a pass -- the module's own law (3.10), applied to capacity.
    cap = capacity_probe(workload)
    gates.append(cap)
    host["available_mb"] = available_mb()
    if cap.blocker and cap.passed is False:
        blockers.append(cap.blocker)

    # ---- State ---------------------------------------------------------------------
    hard_fail = any(g.passed is False for g in gates)
    any_unknown = any(g.passed is None for g in gates)
    if hard_fail:
        state = BLOCKED
    elif any_unknown:
        # The honest state of most real repositories at most moments (SQI-03 4.3). Some
        # surfaces are executable and others are not, and forcing that into a binary
        # rounds either the executable part down to nothing or the blocked part up to fine.
        state = PARTIALLY_QUALIFIED
    else:
        state = QUALIFIED

    return EnvironmentRecord(
        state=state,
        gates=gates,
        host=host,
        toolchains=toolchains,
        lock_state=lock_state,
        blockers=blockers,
        verdict_ceiling=VERDICT_CEILING[state],
        env_hash=_env_hash(host, toolchains),
    )


def _env_hash(host: dict, toolchains: dict) -> str:
    """QUALIFIED is bound to this hash and expires when it moves. It is a claim about a
    machine at a moment, never a permanent property of a repository (SQI-03 4.2)."""
    import hashlib

    blob = "|".join(f"{k}={v}" for k, v in sorted(host.items()) if k != "cwd")
    blob += "||" + "|".join(f"{k}={v}" for k, v in sorted(toolchains.items()))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]
