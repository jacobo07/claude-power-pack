#!/usr/bin/env python3
"""Phase 0 -- identify the engine that actually runs a mobile game.

Reads RUNTIME LITERALS out of native binaries. It never reads symbol names,
because symbol names do not survive stripping: a symbol scan that comes back
empty cannot tell absence from invisibility, so it carries no information and
cannot return the other answer.

Three outcomes are load-bearing and none is promoted for tidiness:

  CONFIRMED     a literal that only this component emits was found
  ABSENT        the component emits literals that survive any build, and none
                are present
  INCONCLUSIVE  the component's literals come from assertions, which a build
                with assertions disabled does not emit -- so their absence is
                invisibility, not absence

Stdlib only. Runs before any decompiler is installed, which is the point.
"""
from __future__ import annotations

import json
import math
import os
import sys
import zipfile
from collections import Counter

ELF_MAGIC = b"\x7fELF"
MACHO_MAGICS = (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe")

# literal -> the component it is evidence for.
# assert_only marks a component whose markers are assertion strings: a release
# build compiled with assertions disabled emits none, so a miss is INCONCLUSIVE.
SIGNATURES = {
    "Unity": {
        "literals": [b"UnityEngine", b"il2cpp", b"mono/metadata", b"libunity"],
        "assert_only": False,
    },
    "Unreal Engine": {
        "literals": [b"UnrealEngine", b"FEngineLoop", b"UE4", b"pakchunk"],
        "assert_only": False,
    },
    "Cocos2d-x": {
        "literals": [b"cocos2d", b"CCDirector", b"2dxLua", b"setXXTEAKey"],
        "assert_only": False,
    },
    "Godot": {
        "literals": [b"GDScript", b"godot", b"OS_Android"],
        "assert_only": False,
    },
    "libGDX": {
        "literals": [b"com/badlogic/gdx", b"libgdx"],
        "assert_only": False,
    },
    "Lua 5.1": {
        "literals": [b"Lua 5.1", b"_LOADED", b"bad argument #", b"stack overflow"],
        "assert_only": False,
    },
    "LuaJIT": {"literals": [b"LuaJIT"], "assert_only": False},
    "zlib": {
        "literals": [b"inflate 1.", b"deflate 1.", b"incorrect header check"],
        "assert_only": False,
    },
    "Vorbis": {"literals": [b"Vorbis", b"vorbis"], "assert_only": False},
    "PVRTC textures": {"literals": [b"PVR!", b"PVRTC"], "assert_only": False},
    "Box2D": {
        "literals": [b"b2Assert", b"b2_maxPolygonVertices", b"Box2D"],
        "assert_only": True,
    },
    "Chipmunk": {
        "literals": [b"cpAssert", b"cpSpaceStep", b"Chipmunk"],
        "assert_only": True,
    },
    "Havok": {"literals": [b"hkBaseSystem", b"Havok"], "assert_only": False},
    "FMOD": {"literals": [b"FMOD", b"fmod_"], "assert_only": False},
    "Rovio Fusion": {"literals": [b"rovio", b"Rovio"], "assert_only": False},
}

# A TLS stack supplies AES, SHA and big-number code for its own reasons. Finding
# a crypto primitive in the image says nothing about what encrypts the assets.
# This is R-04, and it cost a retracted claim plus a 22.9M-candidate sweep.
TLS_CONFOUND = [b"/crypto/", b"X509", b"libcurl", b"ssl/s3_", b"SSL_CTX", b"OpenSSL"]

SCRIPT_EXTS = {".lua", ".js", ".py", ".gd", ".as", ".chunk", ".luac"}
DATA_EXTS = {".dat", ".json", ".xml", ".pak", ".pck", ".assets", ".bin", ".bundle"}
MAX_SCAN_BYTES = 64 * 1024 * 1024


def _entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def iter_members(path):
    """Yield (name, size, reader) for every member, from a zip or a directory."""
    if os.path.isdir(path):
        for dirpath, _dirs, files in os.walk(path):
            for fname in files:
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, path).replace("\\", "/")
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                yield rel, size, (lambda p=full: open(p, "rb").read())
        return
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            yield name, info.file_size, (lambda n=name: zipfile.ZipFile(path).read(n))


def is_native_binary(name: str, head: bytes) -> bool:
    if head.startswith(ELF_MAGIC) or head.startswith(MACHO_MAGICS):
        return True
    return name.endswith(".so") or name.endswith(".dylib")


def scan_binary(data: bytes) -> dict:
    hits = {}
    for engine, spec in SIGNATURES.items():
        found = {}
        for lit in spec["literals"]:
            n = data.count(lit)
            if n:
                found[lit.decode("latin-1")] = n
        if found:
            hits[engine] = found
    tls = {}
    for lit in TLS_CONFOUND:
        n = data.count(lit)
        if n:
            tls[lit.decode("latin-1")] = n
    return {"engines": hits, "tls": tls}


def fingerprint(path: str) -> dict:
    ext_hist = Counter()
    binaries = {}
    script_candidates = []
    total_entries = 0
    dex_count = 0

    for name, size, reader in iter_members(path):
        total_entries += 1
        ext = os.path.splitext(name)[1].lower()
        ext_hist[ext] += 1
        if ext == ".dex":
            dex_count += 1
        if size > MAX_SCAN_BYTES or size == 0:
            continue
        want_sample = (ext in SCRIPT_EXTS or ext in DATA_EXTS) and size <= 1024 * 1024
        if not (name.endswith((".so", ".dylib")) or want_sample):
            # Still worth one read to catch a native binary under any name.
            if size > 4 * 1024 * 1024:
                continue
        try:
            data = reader()
        except (OSError, KeyError, zipfile.BadZipFile):
            continue
        if is_native_binary(name, data[:4]):
            binaries[name] = {"bytes": len(data), **scan_binary(data)}
        elif want_sample and len(script_candidates) < 64:
            script_candidates.append(
                {"name": name, "size": size, "entropy": round(_entropy(data[:8192]), 3)}
            )

    verdicts = {}
    for engine, spec in SIGNATURES.items():
        per_binary = {b: info["engines"].get(engine) for b, info in binaries.items()}
        present = [b for b, v in per_binary.items() if v]
        if present:
            verdicts[engine] = {
                "verdict": "CONFIRMED",
                "in_binaries": present,
                "agrees_across_binaries": len(present) == len(binaries) and len(binaries) > 1,
                "evidence": {b: per_binary[b] for b in present},
            }
        elif not binaries:
            verdicts[engine] = {"verdict": "UNKNOWN", "why": "no native binary was read"}
        elif spec["assert_only"]:
            verdicts[engine] = {
                "verdict": "INCONCLUSIVE",
                "why": "markers are assertion strings; a build with assertions "
                       "disabled emits none, so this instrument cannot tell "
                       "absent from invisible",
            }
        else:
            verdicts[engine] = {"verdict": "ABSENT", "why": "no runtime literal present"}

    tls_present = {b: info["tls"] for b, info in binaries.items() if info["tls"]}
    return {
        "input": path,
        "entries": total_entries,
        "extensions": dict(ext_hist.most_common(20)),
        "native_binaries": {b: info["bytes"] for b, info in binaries.items()},
        "verdicts": verdicts,
        "tls_stack_present": tls_present,
        "script_candidates": script_candidates[:16],
        "dex_count": dex_count,
        "routing": route(verdicts, binaries, ext_hist, dex_count),
    }


def route(verdicts, binaries, ext_hist, dex_count) -> dict:
    """Decide whether Java decompilation is worth anything on this corpus."""
    native_engines = [
        e for e, v in verdicts.items()
        if v["verdict"] == "CONFIRMED"
        and e in ("Unity", "Unreal Engine", "Cocos2d-x", "Godot", "Rovio Fusion",
                  "Lua 5.1", "LuaJIT")
    ]
    script_files = sum(n for ext, n in ext_hist.items() if ext in SCRIPT_EXTS)
    # Order matters. A pure-Java app legitimately carries NO native binary, so
    # testing "no binaries -> UNKNOWN" first swallows exactly the case that
    # should route away to the Java skill.
    if native_engines:
        return {
            "decision": "NATIVE_ENGINE",
            "engines": native_engines,
            "why": "the game runs in a native engine; Java/Kotlin decompilation "
                   "yields a launcher and little else",
            "next": "continue with Phase 1 (inventory) then Phase 2 (access) of "
                    "mobile-game-wii-port; do not spend time in jadx",
            "script_files": script_files,
        }
    if dex_count:
        unidentified = sorted(binaries)
        return {
            "decision": "JAVA_KOTLIN",
            "why": "dex is present and no native game engine was identified"
                   + (f"; {len(unidentified)} native binary/binaries matched no "
                      f"known engine and may be a helper library"
                      if unidentified else ""),
            "next": "this corpus belongs to the android-reverse-engineering "
                    "skill, not to this one",
            "unidentified_binaries": unidentified,
        }
    if not binaries:
        return {
            "decision": "UNKNOWN",
            "why": "no native binary and no dex were read, so the engine "
                   "question is unanswered",
            "next": "confirm the input really is the game package",
        }
    return {
        "decision": "UNKNOWN",
        "why": "a native binary is present but matched no known engine",
        "next": "widen the literal table, or read the loader's error strings",
    }


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__.strip())
        print("\nusage: fingerprint_game.py <apk|zip|directory> [--json]")
        return 0
    path = argv[1]
    if not os.path.exists(path):
        print(f"UNREADABLE_INPUT: {path} does not exist", file=sys.stderr)
        return 2
    try:
        result = fingerprint(path)
    except (zipfile.BadZipFile, OSError) as exc:
        print(f"UNREADABLE_INPUT: {exc}", file=sys.stderr)
        return 2

    if "--json" in argv:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    r = result
    print(f"=== Phase 0 fingerprint: {r['input']} ===")
    print(f"entries={r['entries']}  native binaries={len(r['native_binaries'])}")
    for name, size in r["native_binaries"].items():
        print(f"  {name}  {size:,} B")
    print("\n-- engines --")
    for engine, v in sorted(r["verdicts"].items()):
        if v["verdict"] == "CONFIRMED":
            agree = " (agrees across binaries)" if v.get("agrees_across_binaries") else ""
            sample = next(iter(v["evidence"].values()))
            lits = ", ".join(f"{k} x{n}" for k, n in list(sample.items())[:3])
            print(f"  CONFIRMED     {engine}{agree} -- {lits}")
    for engine, v in sorted(r["verdicts"].items()):
        if v["verdict"] == "INCONCLUSIVE":
            print(f"  INCONCLUSIVE  {engine} -- {v['why']}")
    absent = [e for e, v in r["verdicts"].items() if v["verdict"] == "ABSENT"]
    if absent:
        print(f"  ABSENT        {', '.join(sorted(absent))}")

    if r["tls_stack_present"]:
        print("\n-- R-04 warning --")
        print("  A TLS stack is linked in. It supplies AES, SHA and big-number")
        print("  code for its own reasons, so a crypto primitive found in this")
        print("  image is NOT evidence about what encrypts the assets.")
        for b, lits in r["tls_stack_present"].items():
            print(f"    {b}: {', '.join(f'{k} x{n}' for k, n in list(lits.items())[:4])}")

    rt = r["routing"]
    print(f"\n-- routing: {rt['decision']} --")
    print(f"  {rt['why']}")
    print(f"  next: {rt['next']}")
    if r["script_candidates"]:
        high = [c for c in r["script_candidates"] if c["entropy"] > 7.5]
        print(f"\n  script/data candidates sampled: {len(r['script_candidates'])}"
              f", of which {len(high)} score entropy > 7.5 bits/byte")
        if high:
            print("  high entropy is consistent with ciphertext AND with")
            print("  compression; Phase 2 separates them. It is not a verdict.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
