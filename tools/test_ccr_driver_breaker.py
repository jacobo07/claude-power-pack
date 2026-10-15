"""V-DRV-*: the GEX44 Stage 3 driver (drive3.sh v3) breaker fails closed, proven on the VERSIONED bytes.

The driver lives at vault/programs/ccr/stage3/driver/drive3.sh (byte-exact copy of
kobii@gex44:/home/kobii/missions/ccr-s3-data/drive3.sh, provenance in MANIFEST.json). This test reads it
as TEXT, extracts only spent() and over(), and sources just those two functions into real bash. The
driver's top level (rm -rf, cp -r, the model client launch, pkill) is never executed.

Exit codes: 0 pass, 1 fail, 2 INCONCLUSIVE (no usable bash). INCONCLUSIVE is never counted as a pass.
Last line of output: DRV_PASS=<passes>/<total>
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVER_DIR = ROOT / "vault" / "programs" / "ccr" / "stage3" / "driver"
DRIVER = DRIVER_DIR / "drive3.sh"
MANIFEST = DRIVER_DIR / "MANIFEST.json"
STOP = 4_500_000  # the driver's current UNIT_STOP; over() reads no global, the stop is an argument

passes = fails = 0


class Inconclusive(Exception):
    """The instrument could not run (no bash). Reported as INCONCLUSIVE, exit 2, never a pass."""


def _ok(gate: str, ev: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate: str, ev: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def posix(p: Path | str) -> str:
    return Path(p).as_posix()


def find_bash() -> str:
    """Real bash only. On Windows that is Git for Windows' bash; System32 holds the WSL launcher and is refused."""
    if os.name == "nt":
        cand = Path(r"C:\Program Files\Git\bin\bash.exe")
        found = str(cand) if cand.is_file() else ""
    else:
        found = shutil.which("bash") or ""
    if not found:
        raise Inconclusive("no bash found")
    if "system32" in found.lower():
        raise Inconclusive(f"refusing WSL launcher bash: {found}")
    probe = subprocess.run([found, "-c", "echo drv_bash_ok"], capture_output=True, timeout=60)
    if b"drv_bash_ok" not in probe.stdout:
        raise Inconclusive(f"bash did not run a trivial command: rc={probe.returncode}")
    return found


class ExtractError(Exception):
    pass


def extract(text: str) -> str:
    """spent() through its heredoc terminator PY and closing brace, plus the single-line over()."""
    lines = text.split("\n")
    s = next((i for i, l in enumerate(lines) if l.startswith("spent() {")), None)
    if s is None:
        raise ExtractError("spent() not found")
    py = next((i for i in range(s + 1, len(lines)) if lines[i] == "PY"), None)
    if py is None:
        raise ExtractError("heredoc terminator PY not found after spent()")
    close = next((i for i in range(py + 1, len(lines)) if lines[i] == "}"), None)
    if close is None:
        raise ExtractError("closing brace of spent() not found")
    o = next((l for l in lines if l.startswith("over() {") and "}" in l), None)
    if o is None:
        raise ExtractError("single-line over() not found")
    return "\n".join(lines[s:close + 1]) + "\n" + o


def _write(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))  # LF, no BOM


def run_bash(bash: str, funcs: str, snippet: str, fixture: Path, failing: bool = False) -> tuple[str, int]:
    """Source ONLY `funcs` in real bash with a python3 shim first on PATH, run `snippet`; return (stdout, rc)."""
    work = Path(tempfile.mkdtemp(prefix="drv-work-"))
    shim = work / "shim"
    shim.mkdir()
    py = shim / "python3"
    if failing:
        _write(py, "#!/usr/bin/env bash\nexit 1\n")
    else:
        _write(py, f'#!/usr/bin/env bash\nexec "{posix(sys.executable)}" "$@"\n')
    py.chmod(0o755)
    _write(work / "funcs.sh", funcs + "\n")
    _write(work / "run.sh", f'source "{posix(work / "funcs.sh")}"\n{snippet}\n')
    env = dict(os.environ)
    env["PATH"] = str(shim) + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env["D"] = posix(fixture)
    p = subprocess.run([bash, posix(work / "run.sh")], capture_output=True, env=env, timeout=120)
    shutil.rmtree(work, ignore_errors=True)
    return p.stdout.decode("utf-8", "replace"), p.returncode


def spent(bash: str, funcs: str, fixture: Path, units: str, failing: bool = False) -> str:
    out, _ = run_bash(bash, funcs, f'out=$(spent {units}); printf "%s" "$out"', fixture, failing)
    return out


def over_rc(bash: str, funcs: str, value: str, stop: int = STOP) -> int:
    """rc of over '<value>' <stop> in real bash: 0 means TRIPPED (over the limit), non-zero means not tripped."""
    if not re.fullmatch(r"\d*|ERR", value):
        raise ValueError(f"unexpected value {value!r}")
    out, _ = run_bash(bash, funcs, f"over '{value}' {int(stop)}; echo \"rc=$?\"", Path(tempfile.gettempdir()))
    m = re.search(r"rc=(\d+)", out)
    if not m:
        raise Inconclusive(f"no rc marker from over: {out!r}")
    return int(m.group(1))


# ---- fixtures -------------------------------------------------------------------------------------------

def valid_line(mid: str, i: int = 0, cr: int = 0, cc: int = 0, o: int = 0) -> str:
    return json.dumps({"type": "assistant", "message": {"id": mid, "usage": {
        "input_tokens": i, "cache_read_input_tokens": cr, "cache_creation_input_tokens": cc, "output_tokens": o}}})


def fixture_dir(lines: list[str], unit: str = "U1") -> Path:
    d = Path(tempfile.mkdtemp(prefix="drv-fix-"))
    _write(d / f"run-{unit}.jsonl", "\n".join(lines) + ("\n" if lines else ""))
    return d


# ---- gates ----------------------------------------------------------------------------------------------

def gate_file_verbatim() -> None:
    g = "V-DRV-FILE-VERBATIM"
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data = DRIVER.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    cr = data.count(b"\r")
    try:
        datetime.fromisoformat(man["fetched_at"].replace("Z", "+00:00"))
        ts_ok = True
    except (KeyError, ValueError):
        ts_ok = False
    problems = []
    if sha != man.get("sha256"):
        problems.append(f"sha256 {sha} != manifest {man.get('sha256')}")
    if len(data) != man.get("bytes"):
        problems.append(f"bytes {len(data)} != manifest {man.get('bytes')}")
    if cr:
        problems.append(f"{cr} CR bytes")
    if man.get("sha256") != man.get("remote_sha256"):
        problems.append("manifest sha256 != remote_sha256")
    if not ts_ok:
        problems.append("fetched_at not ISO-8601")
    if problems:
        _fail(g, "; ".join(problems))
    else:
        _ok(g, f"{len(data)} bytes sha256={sha[:12]} == remote, 0 CR, fetched_at={man['fetched_at']}")


def gate_extract() -> str:
    g = "V-DRV-EXTRACT"
    try:
        funcs = extract(DRIVER.read_text(encoding="utf-8"))
    except ExtractError as e:
        _fail(g, str(e))
        raise
    _ok(g, f"spent() + over() extracted from the versioned file ({len(funcs.splitlines())} lines)")
    return funcs


def gate_over_err_trips(bash: str, funcs: str) -> None:
    g = "V-DRV-OVER-ERR-TRIPS"
    rc = over_rc(bash, funcs, "ERR")
    if rc == 0:
        _ok(g, "over ERR 4500000 -> rc 0 (tripped) in real bash")
    else:
        _fail(g, f"over ERR {STOP} returned rc {rc}, expected 0")


def gate_extract_is_pure(funcs: str, full_text: str) -> None:
    g = "V-DRV-EXTRACT-IS-PURE"
    banned = ["claude", "pkill", "rm -rf", "cp -r", "touch"]
    hits = [t for t in banned if t in funcs]
    control = [t for t in ("claude", "pkill") if t in full_text]  # the full driver has them, so the check is not vacuous
    if hits:
        _fail(g, f"sourced text contains {hits}")
    elif control != ["claude", "pkill"]:
        _fail(g, f"control failed: full driver lacks {sorted({'claude', 'pkill'} - set(control))}")
    else:
        _ok(g, f"no {banned} in the sourced text; full driver does contain claude+pkill (non-vacuous)")


HARNESS_SUM = 1010


def gate_harness_positive_control(bash: str, funcs: str) -> None:
    g = "V-DRV-HARNESS-POSITIVE-CONTROL"
    d = fixture_dir([
        valid_line("m1", 100, 200, 300, 400),
        valid_line("m1", 100, 200, 300, 400),  # duplicate id: counted once
        valid_line("m2", 1, 2, 3, 4),
    ])
    out = spent(bash, funcs, d, "U1")
    where, _ = run_bash(bash, funcs, "command -v python3", d)
    shim_used = "drv-work-" in where.replace("\\", "/") and where.strip().endswith("python3")
    if out == str(HARNESS_SUM) and shim_used:
        _ok(g, f"spent U1 -> {out} (duplicate id counted once); python3 resolves to the shim ({where.strip()})")
    else:
        _fail(g, f"spent -> {out!r} (want {HARNESS_SUM}); python3 resolves to {where.strip()!r}")


def string_stream_probe(bash: str, funcs: str) -> tuple[str, bool]:
    """3,000,000 valid + a string-valued `message` line + 2,000,000 valid. Returns (spent output, tripped)."""
    d = fixture_dir([
        valid_line("m1", 1_000_000, 1_500_000, 400_000, 100_000),
        json.dumps({"type": "assistant", "message": "error text"}),
        valid_line("m3", 500_000, 1_000_000, 400_000, 100_000),
    ])
    out = spent(bash, funcs, d, "U1")
    return out, over_rc(bash, funcs, out) == 0


def gate_string_message_measured(bash: str, funcs: str) -> None:
    g = "V-DRV-STRING-MESSAGE-MEASURED"
    out, tripped = string_stream_probe(bash, funcs)
    if out == "5000000" and tripped:
        _ok(g, f"string-message line skipped, stream measured {out}, over({out}, {STOP}) tripped")
    else:
        _fail(g, f"measured {out!r} tripped={tripped}; want 5000000 and tripped")


def err_trips(bash: str, funcs: str) -> bool:
    return over_rc(bash, funcs, "ERR") == 0


def empty_trips(bash: str, funcs: str) -> bool:
    return over_rc(bash, funcs, "") == 0


def gate_over_empty_trips(bash: str, funcs: str) -> None:
    g = "V-DRV-OVER-EMPTY-TRIPS"
    if empty_trips(bash, funcs):
        _ok(g, "over '' 4500000 -> rc 0 (tripped)")
    else:
        _fail(g, "an empty measurement did NOT trip over()")


def gate_over_numeric_controls(bash: str, funcs: str) -> None:
    g = "V-DRV-OVER-NUMERIC-CONTROLS"
    zero, below, at = over_rc(bash, funcs, "0"), over_rc(bash, funcs, str(STOP - 1)), over_rc(bash, funcs, str(STOP))
    if zero != 0 and below != 0 and at == 0:
        _ok(g, f"0 -> rc {zero}, {STOP - 1} -> rc {below} (not tripped); {STOP} -> rc {at} (boundary tripped)")
    else:
        _fail(g, f"0 -> rc {zero}, {STOP - 1} -> rc {below} (want != 0); {STOP} -> rc {at} (want 0)")


def gate_crashed_measurement_is_err(bash: str, funcs: str) -> None:
    g = "V-DRV-CRASHED-MEASUREMENT-IS-ERR"
    bad = json.dumps({"type": "assistant", "message": {"id": "m1", "usage": {
        "input_tokens": "not-a-number", "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "output_tokens": 0}}})
    out = spent(bash, funcs, fixture_dir([valid_line("m0", 10), bad]), "U1")
    rc = over_rc(bash, funcs, out) if re.fullmatch(r"\d*|ERR", out) else -1
    if out == "ERR" and rc == 0:
        _ok(g, "non-numeric usage value -> spent prints ERR -> over tripped")
    else:
        _fail(g, f"spent -> {out!r}, over rc {rc}; want ERR and rc 0")


def gate_failed_interpreter_is_err(bash: str, funcs: str) -> None:
    g = "V-DRV-FAILED-INTERPRETER-IS-ERR"
    d = fixture_dir([valid_line("m1", 10)])
    out = spent(bash, funcs, d, "U1", failing=True)
    rc = over_rc(bash, funcs, out) if re.fullmatch(r"\d*|ERR", out) else -1
    if out == "ERR" and rc == 0:
        _ok(g, "python3 exits 1 -> spent prints ERR -> over tripped")
    else:
        _fail(g, f"spent -> {out!r}, over rc {rc}; want ERR and rc 0")


OUTPUT_DOMAIN_VARIANTS: dict[str, list[str]] = {
    "string usage field": [json.dumps({"type": "assistant", "message": {"id": "a", "usage": "abc"}})],
    "null usage": [json.dumps({"type": "assistant", "message": {"id": "a", "usage": None}})],
    "usage as a list": [json.dumps({"type": "assistant", "message": {"id": "a", "usage": [1, 2]}})],
    "line that is not JSON": ["this is not json {", valid_line("a", 7)],
    "message as a list": [json.dumps({"type": "assistant", "message": [1, 2]})],
    "empty file": [],
    "usage value is a string": [json.dumps({"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": "x"}}})],
    "usage value is a list": [json.dumps({"type": "assistant", "message": {"id": "a", "usage": {"input_tokens": [1]}}})],
}


def gate_output_domain(bash: str, funcs: str) -> None:
    g = "V-DRV-OUTPUT-DOMAIN"
    bad = []
    seen = {}
    for name, lines in OUTPUT_DOMAIN_VARIANTS.items():
        out = spent(bash, funcs, fixture_dir(lines), "U1")
        seen[name] = out
        if not re.fullmatch(r"\d+|ERR", out):
            bad.append(f"{name}: output {out!r} outside ^(\\d+|ERR)$")
            continue
        want_trip = out == "ERR" or int(out) >= STOP
        got_trip = over_rc(bash, funcs, out) == 0
        if want_trip != got_trip:
            bad.append(f"{name}: output {out!r} over tripped={got_trip}, want {want_trip}")
    if bad:
        _fail(g, "; ".join(bad))
    else:
        _ok(g, f"{len(seen)} corruption variants all in ^(\\d+|ERR)$ and over() agrees: {seen}")


def mutate(text: str, old: str, new: str) -> str:
    if old not in text:
        raise AssertionError(f"mutation target not found: {old!r}")
    out = text.replace(old, new, 1)
    if out == text:
        raise AssertionError(f"mutation did not change the text: {old!r}")
    return out


OVER_LINE_RE = re.compile(r"^over\(\) \{.*$", re.M)


def gate_mutant_drops_err(bash: str, funcs: str) -> None:
    g = "V-DRV-MUTANT-OVER-DROPS-ERR"
    try:
        mut = mutate(funcs, '[ "$1" = ERR ] || ', "")
    except AssertionError as e:
        _fail(g, str(e))
        return
    real, mutant = err_trips(bash, funcs), err_trips(bash, mut)
    if real and not mutant:
        _ok(g, "mutant (ERR clause removed) fails the ERR predicate: mutant detected; real text passes it")
    else:
        _fail(g, f"real tripped={real}, mutant tripped={mutant}; want True/False")


def gate_mutant_drops_empty(bash: str, funcs: str) -> None:
    g = "V-DRV-MUTANT-OVER-DROPS-EMPTY"
    try:
        mut = mutate(funcs, '[ -z "$1" ] || ', "")
    except AssertionError as e:
        _fail(g, str(e))
        return
    real, mutant = empty_trips(bash, funcs), empty_trips(bash, mut)
    if real and not mutant:
        _ok(g, "mutant (empty clause removed) fails the empty predicate: mutant detected; real text passes it")
    else:
        _fail(g, f"real tripped={real}, mutant tripped={mutant}; want True/False")


def gate_mutant_a4_shape(bash: str, funcs: str) -> None:
    g = "V-DRV-MUTANT-A4-SHAPE"
    try:
        mut = mutate(funcs, "|| echo ERR", "")
        mut = mutate(mut, "not isinstance(m, dict) or ", "")
        m = OVER_LINE_RE.search(mut)
        if not m:
            raise AssertionError("over() line not found in mutant")
        mut = mutate(mut, m.group(0), 'over() { [ "$1" -ge "$2" ]; }')
    except AssertionError as e:
        _fail(g, str(e))
        return
    out, tripped = string_stream_probe(bash, mut)
    if out == "" and not tripped:
        _ok(g, "A4 shape reproduced: string-message stream -> empty measurement, over() NOT tripped (fail-open); mutant detected")
    else:
        _fail(g, f"mutant measured {out!r} tripped={tripped}; want empty and not tripped")


def info_characterization(bash: str, funcs: str) -> None:
    """Printed as INFO, not counted. OPEN residual: a missing or misnamed stream measures 0, never ERR."""
    none = spent(bash, funcs, fixture_dir([]), "NOSUCHUNIT")
    allstr = spent(bash, funcs, fixture_dir([json.dumps({"type": "assistant", "message": "x"})] * 3), "U1")
    print(f"INFO missing-stream unit -> spent prints {none!r} (over trips: {over_rc(bash, funcs, none) == 0})")
    print(f"INFO all-string-message stream -> spent prints {allstr!r} (over trips: {over_rc(bash, funcs, allstr) == 0})")
    if none == "0":
        print("INFO OPEN residual: a unit whose stream file is missing or misnamed measures 0 (not ERR) and is never over the stop")

def main() -> int:
    try:
        bash = find_bash()
    except Inconclusive as e:
        print(f"INCONCLUSIVE: {e}")
        print("DRV_PASS=0/0 (INCONCLUSIVE, not a pass)")
        return 2
    try:
        gate_file_verbatim()
        funcs = gate_extract()
        gate_over_err_trips(bash, funcs)
        gate_extract_is_pure(funcs, DRIVER.read_text(encoding="utf-8"))
        gate_harness_positive_control(bash, funcs)
        gate_string_message_measured(bash, funcs)
        gate_over_empty_trips(bash, funcs)
        gate_over_numeric_controls(bash, funcs)
        gate_crashed_measurement_is_err(bash, funcs)
        gate_failed_interpreter_is_err(bash, funcs)
        gate_output_domain(bash, funcs)
        gate_mutant_drops_err(bash, funcs)
        gate_mutant_drops_empty(bash, funcs)
        gate_mutant_a4_shape(bash, funcs)
        info_characterization(bash, funcs)
    except ExtractError:
        pass
    except Inconclusive as e:
        print(f"INCONCLUSIVE: {e}")
        print("DRV_PASS=0/0 (INCONCLUSIVE, not a pass)")
        return 2
    print(f"DRV_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 and passes > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
