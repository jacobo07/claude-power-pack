#!/usr/bin/env python3
"""Done-gate for the absorbed android-reverse-engineering skill.

Run from the Power Pack repo root:

    python tools/test_android_re.py

Exit 0 = absorption is sound. Every gate that can be driven is driven from
both poles: a detector that always answers "clean" and one that always
answers "obfuscated" must both fail here, or the gate measures nothing.

Fixtures are synthetic APKs assembled in a temp dir. They are built from the
byte shapes the parser actually consumes (a zip carrying a classes.dex whose
payload holds DEX type descriptors), never from the parser's own output, and
each family has a positive and a negative member so no constant-answer
implementation can pass.

The Kotlin-metadata fixtures carry the annotation SHAPE observed in real jadx
output rather than real third-party decompiled code, which is not ours to
commit. The shape was validated separately against a real 21,486-file jadx
tree on 2026-09-19 (102 files carrying @Metadata(, 84 strict matches, 39
recovered names); that corpus lives outside the repo, so the optional gates
below run only when it is present and report UNMEASURED when it is not.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "android-reverse-engineering")
CORE = os.path.join(SKILL, "core")
sys.path.insert(0, CORE)

import fingerprint as FP  # noqa: E402
import lookup_name as LN  # noqa: E402
import recover_kotlin_names as RK  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []
UNMEASURED: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    PASSES.append(gate)
    print(f"  OK   {gate}: {evidence}")


def _fail(gate: str, diagnostic: str) -> None:
    FAILS.append(gate)
    print(f"  FAIL {gate}: {diagnostic}")


def _unmeasured(gate: str, why: str) -> None:
    UNMEASURED.append(gate)
    print(f"  ----  {gate}: UNMEASURED -- {why}")


def _check(gate: str, condition: bool, evidence: str, diagnostic: str) -> None:
    _ok(gate, evidence) if condition else _fail(gate, diagnostic)


# ----------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------
def _dex(types: list[str]) -> bytes:
    """A byte blob shaped like the dex string table the scanner reads."""
    head = b"dex\n035\x00" + b"\x00" * 24
    body = b"".join(b"\x00" + f"L{t};".encode("ascii") for t in types)
    return head + body


def make_apk(path: str, entries: dict[str, bytes], types: list[str]) -> str:
    with zipfile.ZipFile(path, "w") as zf:
        for name, blob in entries.items():
            zf.writestr(name, blob)
        zf.writestr("classes.dex", _dex(types))
    return path


def obfuscated_types() -> list[str]:
    # 30 single/double-letter roots against 3 real ones -> unmistakably R8.
    roots = [chr(c) for c in range(ord("a"), ord("a") + 26)] + ["a0", "b1", "c2", "d3"]
    out = [f"{r}/{r}{i}" for i, r in enumerate(roots)]
    out += ["kotlin/coroutines/Continuation", "com/example/app/Main", "okhttp3/OkHttpClient"]
    return out


def clean_types() -> list[str]:
    return [
        "com/example/app/MainActivity",
        "com/example/app/data/UserRepository",
        "com/example/app/net/ApiService",
        "kotlin/coroutines/Continuation",
        "retrofit2/Retrofit",
        "okhttp3/OkHttpClient",
        "androidx/lifecycle/ViewModel",
    ]


# ----------------------------------------------------------------------
# gates
# ----------------------------------------------------------------------
def gate_attribution() -> None:
    notice = os.path.join(SKILL, "NOTICE.md")
    lic = os.path.join(SKILL, "LICENSE")
    _check(
        "V-ARE-LICENSE-PRESENT",
        os.path.isfile(lic) and "Apache License" in open(lic, encoding="utf-8").read(),
        "LICENSE carries the Apache-2.0 text",
        "LICENSE missing or not Apache-2.0",
    )
    if not os.path.isfile(notice):
        _fail("V-ARE-ATTRIBUTION", "NOTICE.md absent")
        return
    text = open(notice, encoding="utf-8").read()
    has_commit = bool(re.search(r"\b[0-9a-f]{40}\b", text))
    _check(
        "V-ARE-ATTRIBUTION",
        "SimoneAvogadro" in text and "Apache" in text and has_commit,
        "NOTICE.md names upstream, license and a pinned 40-char commit",
        "NOTICE.md must name upstream author, license and the pinned commit",
    )
    _check(
        "V-ARE-DIVERGENCE-DECLARED",
        "divergence" in text.lower() and "obfuscation" in text.lower(),
        "the obfuscation divergence is declared in NOTICE.md",
        "a behavioural divergence from upstream is not declared",
    )


def gate_upstream_intact() -> None:
    """Absorption completeness: the verbatim halves must still be there."""
    expected_scripts = [
        "check-deps.sh", "check-deps.ps1", "decompile.sh", "decompile.ps1",
        "find-api-calls.sh", "find-api-calls.ps1", "install-dep.sh",
        "install-dep.ps1", "fingerprint.sh", "lookup-name.sh",
        "recover-kotlin-names.sh",
    ]
    missing = [
        s for s in expected_scripts
        if not os.path.isfile(os.path.join(SKILL, "scripts", s))
        or os.path.getsize(os.path.join(SKILL, "scripts", s)) == 0
    ]
    _check(
        "V-ARE-UPSTREAM-SCRIPTS",
        not missing,
        f"all {len(expected_scripts)} upstream scripts present and non-empty",
        f"missing or empty: {missing}",
    )

    refs = os.path.join(SKILL, "references")
    n_refs = len([f for f in os.listdir(refs)]) if os.path.isdir(refs) else 0
    _check(
        "V-ARE-UPSTREAM-REFERENCES",
        n_refs >= 7,
        f"{n_refs} reference documents absorbed",
        f"expected >=7 reference files, found {n_refs}",
    )


def gate_core_executable() -> None:
    """A documented capability must actually run -- drive each entry point."""
    for name in ("fingerprint.py", "recover_kotlin_names.py", "lookup_name.py"):
        path = os.path.join(CORE, name)
        if not os.path.isfile(path):
            _fail("V-ARE-CORE-EXEC", f"{name} does not exist")
            continue
        proc = subprocess.run(
            [sys.executable, path, "--help"], capture_output=True, text=True
        )
        _check(
            f"V-ARE-CORE-EXEC[{name}]",
            proc.returncode == 0 and "usage" in proc.stdout.lower(),
            "runs and prints usage",
            f"exit={proc.returncode} stderr={proc.stderr.strip()[:160]}",
        )


def gate_skill_doc_paths() -> None:
    """Every core/*.py path SKILL.md promises must exist on disk."""
    skill_md = os.path.join(SKILL, "SKILL.md")
    if not os.path.isfile(skill_md):
        _fail("V-ARE-DOC-EXEC", "SKILL.md absent")
        return
    text = open(skill_md, encoding="utf-8").read()
    named = set(re.findall(r"core[/\\]([A-Za-z_]+\.py)", text))
    if not named:
        _fail("V-ARE-DOC-EXEC", "SKILL.md names no core/*.py entry point")
        return
    missing = [n for n in named if not os.path.isfile(os.path.join(CORE, n))]
    _check(
        "V-ARE-DOC-EXEC",
        not missing,
        f"all {len(named)} core entry points named in SKILL.md exist",
        f"SKILL.md documents non-existent: {missing}",
    )


def gate_fingerprint(tmp: str) -> None:
    # -- positive control: obfuscated
    apk = make_apk(
        os.path.join(tmp, "obf.apk"),
        {"AndroidManifest.xml": b"\x03\x00\x08\x00", "res/x.png": b"\x89PNG"},
        obfuscated_types(),
    )
    r = FP.build_report(apk)
    _check(
        "V-ARE-FP-OBFUSCATED",
        r["obfuscation"].startswith("HIGH"),
        f"reads {r['obfuscation']}",
        f"expected HIGH, got {r['obfuscation']} (evidence {r['obfuscation_evidence']})",
    )
    _check(
        "V-ARE-FP-RECOVERY-GATE",
        r["needs_kotlin_recovery"] is True,
        "obfuscated Kotlin routes to Phase 3.5",
        "obfuscated Kotlin app did NOT trigger the Phase 3.5 recommendation",
    )

    # -- negative control: clean. Same code path, opposite verdict.
    apk = make_apk(
        os.path.join(tmp, "clean.apk"),
        {"AndroidManifest.xml": b"\x03\x00\x08\x00"},
        clean_types(),
    )
    r2 = FP.build_report(apk)
    _check(
        "V-ARE-FP-CLEAN",
        r2["obfuscation"].startswith("LOW"),
        f"reads {r2['obfuscation']}",
        f"expected LOW, got {r2['obfuscation']}",
    )
    _check(
        "V-ARE-FP-RECOVERY-GATE-OFF",
        r2["needs_kotlin_recovery"] is False,
        "clean app does not trigger Phase 3.5",
        "a non-obfuscated app was sent to Phase 3.5",
    )
    _check(
        "V-ARE-FP-HTTP-STACK",
        "Retrofit" in r2["http_stack"] and "OkHttp" in r2["http_stack"],
        f"detects {r2['http_stack']} from dex descriptors",
        f"expected Retrofit+OkHttp, got {r2['http_stack']}",
    )

    # -- framework routing: a Flutter app must be diverted away from jadx
    apk = make_apk(
        os.path.join(tmp, "flutter.apk"),
        {
            "lib/arm64-v8a/libflutter.so": b"\x7fELF",
            "lib/arm64-v8a/libapp.so": b"\x7fELF",
        },
        clean_types(),
    )
    r3 = FP.build_report(apk)
    rec = " ".join(r3["recommendation"]).lower()
    _check(
        "V-ARE-FP-FLUTTER",
        r3["framework"] == "Flutter" and "libapp.so" in r3["rationale"],
        f"{r3['framework']} -- {r3['rationale']}",
        f"expected Flutter, got {r3['framework']}",
    )
    _check(
        "V-ARE-FP-FLUTTER-DIVERT",
        "dart" in rec or "blutter" in rec,
        "Flutter apps are routed to Dart tooling, not jadx",
        f"Flutter recommendation did not divert away from jadx: {rec[:120]}",
    )
    _check(
        "V-ARE-FP-NATIVE-LIBS",
        len(r3["native_libs"]) == 2,
        f"{len(r3['native_libs'])} native libs consolidated",
        f"expected 2 native libs, got {r3['native_libs']}",
    )

    # -- XAPK: evidence must be aggregated ACROSS members, since split
    #    bundles put .so files in config.<abi>.apk rather than base.apk.
    base = make_apk(os.path.join(tmp, "base.apk"), {"AndroidManifest.xml": b"x"}, clean_types())
    split = make_apk(
        os.path.join(tmp, "config.arm64_v8a.apk"),
        {"lib/arm64-v8a/libnative.so": b"\x7fELF"},
        [],
    )
    xapk = os.path.join(tmp, "bundle.xapk")
    with zipfile.ZipFile(xapk, "w") as zf:
        zf.write(base, "base.apk")
        zf.write(split, "config.arm64_v8a.apk")
        zf.writestr("manifest.json", json.dumps({"package_name": "com.example.app"}))
    r4 = FP.build_report(xapk)
    _check(
        "V-ARE-FP-XAPK-SPLITS",
        len(r4["members"]) == 2 and any("libnative.so" in n for n in r4["native_libs"]),
        f"{len(r4['members'])} members, native lib found in the split",
        f"split aggregation failed: members={r4['members']} libs={r4['native_libs']}",
    )
    _check(
        "V-ARE-FP-XAPK-STACK",
        "Retrofit" in r4["http_stack"],
        "dex evidence from base.apk survives bundle aggregation",
        f"expected Retrofit from base member, got {r4['http_stack']}",
    )


# Annotation shapes as emitted by jadx. The d1 payload of the second one
# carries a ')', which is what defeats the strict upstream pattern.
META_PLAIN = (
    '@Metadata(d1 = {"\\u0000\\u0010\\n\\u0002\\b\\u0003"}, '
    'd2 = {"Lcom/acme/data/UserRepository;", "", "load", "()V"}, mv = {1, 8, 0})\n'
)
META_PAREN = (
    '@Metadata(d1 = {"\\u0000 (Ljava/lang/String;)V\\u0002"}, '
    'd2 = {"Lcom/acme/net/AuthApi;", "", "login", "()V"}, mv = {1, 8, 0})\n'
)
DEBUG_META = (
    '@DebugMetadata(f = "CheckoutViewModel.kt", l = {42}, '
    'm = "invokeSuspend", c = "com.acme.checkout.CheckoutViewModel$submit$1")\n'
)


def _write_src(root: str, rel: str, body: str) -> None:
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("package x;\n" + body + "public final class C {}\n")


def gate_recovery(tmp: str) -> str:
    src = os.path.join(tmp, "sources")
    _write_src(src, os.path.join("a", "b", "C.java"), META_PLAIN)
    _write_src(src, os.path.join("a", "b", "D.java"), META_PAREN)
    _write_src(src, os.path.join("a", "b", "E.java"), DEBUG_META)
    # Third-party tree: real names already, must be skipped.
    _write_src(src, os.path.join("com", "google", "gms", "F.java"), META_PLAIN)
    _write_src(src, os.path.join("a", "b", "G.java"), "// nothing to mine\n")

    out = os.path.join(tmp, "mapping")
    mapping, file_real, counts = RK.recover(src)
    RK.write_outputs(out, mapping, file_real)

    _check(
        "V-ARE-RECOVER-D2",
        mapping.get("a.b.C") == "com.acme.data.UserRepository",
        "d2 descriptor resolves to the real FQN",
        f"expected com.acme.data.UserRepository, got {mapping.get('a.b.C')!r}",
    )
    _check(
        "V-ARE-RECOVER-DEBUGMETA",
        mapping.get("a.b.E") == "com.acme.checkout.CheckoutViewModel",
        "@DebugMetadata resolves and the $lambda suffix is stripped",
        f"expected com.acme.checkout.CheckoutViewModel, got {mapping.get('a.b.E')!r}",
    )
    _check(
        "V-ARE-RECOVER-PAREN-FALLBACK",
        mapping.get("a.b.D") == "com.acme.net.AuthApi"
        and counts.get("d2_relaxed", 0) == 1,
        "a ')' in d1 no longer loses the class (additive fallback fired once)",
        f"expected com.acme.net.AuthApi via d2_relaxed, got {mapping.get('a.b.D')!r} counts={counts}",
    )
    _check(
        "V-ARE-RECOVER-SKIPS-VENDOR",
        "com.google.gms.F" not in mapping,
        "third-party tree correctly skipped",
        "a com.google.* class was mined as if it were app code",
    )
    _check(
        "V-ARE-RECOVER-NO-FALSE-HIT",
        "a.b.G" not in mapping,
        "a file with no metadata yields no mapping",
        "invented a mapping for a file carrying no metadata",
    )
    _check(
        "V-ARE-RECOVER-ARTIFACTS",
        os.path.isfile(os.path.join(out, "mapping.json"))
        and os.path.isfile(os.path.join(out, "mapping.tsv"))
        and os.path.isdir(os.path.join(out, "by_package")),
        "mapping.json, mapping.tsv and by_package/ written",
        "expected output artifacts are missing",
    )
    return src


def gate_lookup(tmp: str, src: str) -> None:
    out = os.path.join(tmp, "mapping")
    mapping, reverse = LN.load(out)

    buf = io.StringIO()
    stdout, sys.stdout = sys.stdout, buf
    try:
        LN.by_obf(mapping, reverse, "a.b.C")
        LN.grep_annotated(mapping, r"UserRepository", src)
    finally:
        sys.stdout = stdout
    text = buf.getvalue()

    _check(
        "V-ARE-LOOKUP-RESOLVE",
        "a.b.C  ->  com.acme.data.UserRepository" in text,
        "obfuscated FQN resolves to the real name",
        f"resolution line absent from output: {text[:160]!r}",
    )
    _check(
        "V-ARE-LOOKUP-GREP-ANNOTATES",
        "// com.acme.data.UserRepository" in text,
        "grep hits are annotated with the owning real class",
        "grep output carried no real-name annotation",
    )

    buf = io.StringIO()
    stdout, sys.stdout = sys.stdout, buf
    try:
        LN.grep_annotated(mapping, r"ThisStringAppearsNowhere", src)
    finally:
        sys.stdout = stdout
    _check(
        "V-ARE-LOOKUP-GREP-EMPTY",
        buf.getvalue().strip() == "",
        "a pattern with no hits prints nothing",
        "grep invented output for a pattern that matches nothing",
    )


def gate_real_corpus() -> None:
    """Optional: drive the miner against a real jadx tree if one is present.

    Absence is reported as UNMEASURED, never as a pass -- an optional gate
    that silently counts as green is how an absent capability looks healthy.
    """
    corpus = os.path.join(
        os.path.expanduser("~"), "Desktop", "Cursor Projects",
        "Computer Personal Ops", "editor-apk-fix", "workspace",
        "decompiled", "sources",
    )
    if not os.path.isdir(corpus):
        _unmeasured(
            "V-ARE-REAL-CORPUS",
            "no real decompiled tree on this host; run after a real decompile",
        )
        return
    # Bounded: this only has to prove the miner has real input, not count it.
    # An unbounded walk of a 21k-file tree made every run of this gate take
    # minutes, which in turn made the mutation drill take twenty.
    want = 5
    n_meta = 0
    for dp, _d, files in os.walk(corpus):
        for f in files:
            if not f.endswith(".java"):
                continue
            try:
                with open(os.path.join(dp, f), encoding="utf-8", errors="replace") as fh:
                    if "@Metadata(" in fh.read():
                        n_meta += 1
            except OSError:
                pass
            if n_meta >= want:
                break
        if n_meta >= want:
            break
    _check(
        "V-ARE-REAL-CORPUS",
        n_meta >= want,
        f"found {n_meta} real files carrying @Metadata( -- miner has real input",
        f"real corpus present but only {n_meta} files carry @Metadata",
    )


def gate_powershell_bridge() -> None:
    """Exercise the upstream PowerShell entry point the workflow starts with.

    check-deps.ps1 aborted on PowerShell 5.1 for anyone who had Java
    installed, because PS wraps a native exe's stderr in an ErrorRecord and
    the script runs under $ErrorActionPreference='Stop'. It is patched (see
    the skill's NOTICE.md); this pins the fix, because a regression there
    makes the very first step of the workflow unusable.

    Asserts on the machine-readable contract the workflow parses, not on
    exit code: exit 1 is CORRECT when a required dependency is missing.
    """
    if os.name != "nt":
        _unmeasured("V-ARE-PS-BRIDGE", "not a Windows host")
        return
    script = os.path.join(SKILL, "scripts", "check-deps.ps1")
    if not os.path.isfile(script):
        _fail("V-ARE-PS-BRIDGE", "check-deps.ps1 absent")
        return
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", script],
        capture_output=True, text=True,
    )
    blob = proc.stdout + proc.stderr
    _check(
        "V-ARE-PS-BRIDGE-NO-ABORT",
        "NativeCommandError" not in blob,
        "runs without the PS 5.1 native-stderr abort",
        "check-deps.ps1 aborted with NativeCommandError -- the 5.1 fix regressed",
    )
    _check(
        "V-ARE-PS-BRIDGE-CONTRACT",
        "INSTALL_REQUIRED:" in blob or "All dependencies are installed" in blob,
        "emits the machine-readable dependency contract",
        f"no INSTALL_* contract line in output: {blob.strip()[:200]!r}",
    )


def main() -> int:
    print("=== V-ARE: android-reverse-engineering absorption gate ===\n")
    tmp = tempfile.mkdtemp(prefix="v-are.")
    try:
        print("[attribution]")
        gate_attribution()
        print("\n[absorption completeness]")
        gate_upstream_intact()
        print("\n[executability]")
        gate_core_executable()
        gate_skill_doc_paths()
        print("\n[phase 0 -- fingerprint]")
        gate_fingerprint(tmp)
        print("\n[phase 3.5 -- kotlin recovery]")
        src = gate_recovery(tmp)
        print("\n[phase 3.5 -- lookup]")
        gate_lookup(tmp, src)
        print("\n[powershell bridge]")
        gate_powershell_bridge()
        print("\n[real input]")
        gate_real_corpus()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(PASSES) + len(FAILS)
    print(
        f"\nARE_PASS={len(PASSES)}/{total}  "
        f"unmeasured={len(UNMEASURED)}  threshold={total}/{total}"
    )
    if FAILS:
        print("FAILED GATES: " + ", ".join(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
