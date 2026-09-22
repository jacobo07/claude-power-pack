"""Time a BARE pane's launcher to `& claude` (T-KCLAUDE-PASTE-WINDOW-001).

The companion instrument to tools/ngen_powershell.ps1: that script fixes the
machine, this one measures what the fix buys at the surface the Owner feels --
the window in which a pasted prompt has no reader.

It reuses Probe/PS1/POWERSHELL from tools/test_kclaude_paste_window.py rather
than re-implementing them, so it measures the same subject the gate pins: the
real launcher, a stub `claude` first on PATH, private TEMP and CLAUDE_STATE_DIR
(it never consumes another pane's restart flag nor writes the Owner's caches).

It prints EVERY reading, the median, and free RAM before and after. On this
host free memory has oscillated by gigabytes inside one turn, so a single
reading is not a measurement, and a median taken while the host drifts still
owes the reader its drift. Two readings taken at different loads are a
cross-load comparison and must be reported as one -- treating such a pair as
same-batch is what put this investigation's "+3 s of module autoload" at ~700 ms
once it was measured properly.

    python tools/time_kclaude_launcher.py [runs]      # default 5

Expect the first run to carry `sync:hook-registry` in its trace and the rest
not to: the registry verdict is cached by content. A bare pane that shows a
`prelaunch` step is a regression -- that is the gate's subject, not this one's.
"""
import importlib.util
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

GATE = Path(__file__).resolve().with_name("test_kclaude_paste_window.py")
REPO = Path(__file__).resolve().parent.parent
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 5

if not GATE.exists():
    print(f"HARNESS-FAILED: the gate this harness reuses is missing: {GATE}")
    raise SystemExit(2)

spec = importlib.util.spec_from_file_location("pastegate", GATE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def free_mb() -> int:
    """Free physical memory, or -1 when it could not be read.

    -1 is not zero: an unread value must not be reported as a starved host.
    """
    out = subprocess.run(
        [mod.POWERSHELL, "-NoProfile", "-Command",
         "[int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1KB)"],
        capture_output=True, text=True, timeout=60).stdout.strip()
    return int(out) if out.isdigit() else -1


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="kclaude-timing-"))
    probe = mod.Probe(root)

    print("free_mb_before=" + str(free_mb()))
    readings = []
    for i in range(RUNS):
        t0 = time.perf_counter()
        steps = probe.run(f"t{i}", [], REPO)
        ms = int((time.perf_counter() - t0) * 1000)
        readings.append(ms)
        print(f"run{i}={ms}ms steps={len(steps)} trace={','.join(steps) or '(none)'}")
    print("free_mb_after=" + str(free_mb()))

    calls = probe.stub_calls()
    print(f"stub_calls={calls} (control: one launch per run, expected {RUNS})")
    print("readings=" + "/".join(str(r) for r in readings))
    print("median=" + str(int(statistics.median(readings))) + "ms")

    # A timing run whose launches did not happen is not a slow launcher, it is
    # no launcher at all -- and both print a number.
    if calls != RUNS:
        print("TIMING=INSTRUMENT_FAILED (the stub was not invoked once per run)")
        return 2
    print("TIMING=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
