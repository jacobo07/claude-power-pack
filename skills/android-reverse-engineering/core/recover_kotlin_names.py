#!/usr/bin/env python3
"""recover_kotlin_names.py -- Rebuild an (obfuscated -> real) class-name map
from Kotlin metadata left in decompiled sources.

Extracted from upstream ``scripts/recover-kotlin-names.sh``
(android-reverse-engineering-skill, Apache-2.0, (c) Simone Avogadro), whose
body was already Python embedded in a bash heredoc. See ../NOTICE.md.

Lifting it out of the heredoc is what makes Phase 3.5 reachable on Windows,
where the bash wrapper cannot run -- and it costs nothing on POSIX, where
the same file is invoked directly. The mining logic is unchanged.

R8 obfuscates JVM symbols but cannot strip the Kotlin metadata strings --
the Kotlin runtime (reflection, coroutines) needs them at runtime. Two
annotations carry the original FQN:

  * @DebugMetadata(c = "<full.qualified.Name>", f = "<File.kt>", ...)
    emitted for almost every ``suspend`` function (every coroutine
    SuspendLambda).

  * @Metadata(... d2 = {"...L<pkg/Class>;..."} ...) listing internal class
    refs of the file.

Typical recovery on a real-world app: 30-50 % of classes regain their real
names -- usually 100 % of the *Repository / *ViewModel / *UseCase / *Impl
classes you actually want to read.

Usage:
    python recover_kotlin_names.py <decompiled-sources-dir> [output-dir]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict

# @DebugMetadata(c = "com.foo.Bar$Inner$1", ...)
RE_DEBUG = re.compile(r'@DebugMetadata\([^)]*?c\s*=\s*"([^"]+)"', re.S)
# @Metadata(... d2 = { "...Lcom/foo/Bar;..." ...} )
RE_DTWO = re.compile(r"@Metadata\([^)]*?d2\s*=\s*\{([^}]*)\}", re.S)
# Additive fallback, Power Pack addition -- see ../NOTICE.md.
#
# The pattern above scans from "@Metadata(" to "d2" with [^)]*?, so a single
# ')' anywhere in the d1 payload before d2 kills the match -- and d1 carries
# JVM signature fragments, where ')' is ordinary. Measured 2026-09-19 on a
# real jadx tree of 21,486 files: 102 carried "@Metadata(", 84 matched the
# strict pattern, and 14 were lost to exactly this.
#
# Be precise about the size of the win, because the two numbers differ: those
# 14 lost MATCHES became exactly +1 recovered NAME (38 -> 39). Most of them
# carry only kotlin./java./android descriptors in d2 and so yield nothing
# usable either way. This is a marginal gain kept because it is free, not the
# 14% it would look like if matches were the metric that mattered.
#
# It is tried ONLY after the strict pattern misses, so every file upstream
# recovered is still recovered by the identical expression and no previously
# matching file can change its answer.
RE_DTWO_RELAXED = re.compile(r"@Metadata\(.*?d2\s*=\s*\{([^}]*)\}", re.S)
RE_LCLASS = re.compile(r"L([A-Za-z][\w/$]+);")
# jadx sometimes emits this comment for renamed classes
RE_RENAMED = re.compile(r"/\*\s*renamed from:\s*([\w.$]+)\s*\*/")

# Skip third-party / framework trees -- their names are already real.
SKIP_PREFIXES = (
    "kotlin.", "kotlinx.", "androidx.", "android.", "java.", "javax.",
    "com.google.", "com.facebook.", "com.appsflyer.", "com.datadog.",
    "io.ktor.", "io.sentry.", "io.realm.", "okhttp3.", "okio.",
    "com.squareup.", "com.bumptech.", "com.airbnb.", "com.payu.",
    "com.storyteller.", "zendesk.", "io.intercom.", "com.microsoft.",
    "com.tinder.", "com.hotjar.", "com.amplitude.", "com.segment.",
    "com.mixpanel.", "com.onesignal.", "com.stripe.", "com.braintreepayments.",
    "retrofit2.", "dagger.", "javax.inject.", "org.jetbrains.",
)

SOURCE_SUFFIXES = (".java", ".kt")


def recover(src: str) -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
    """Walk *src* and return (mapping, file_of_obf, counts_by_technique)."""
    mapping: dict[str, str] = {}
    file_real: dict[str, str] = {}
    counts: dict[str, int] = defaultdict(int)

    for dp, _dirs, files in os.walk(src):
        for f in files:
            if not f.endswith(SOURCE_SUFFIXES):
                continue
            path = os.path.join(dp, f)
            rel = os.path.relpath(path, src)
            obf = os.path.splitext(rel)[0].replace(os.sep, ".")
            if obf.startswith(SKIP_PREFIXES):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue

            real = None

            m = RE_DEBUG.search(text)
            if m:
                real = m.group(1).split("$", 1)[0]
                counts["debug_meta"] += 1

            if not real:
                for rx, technique in ((RE_DTWO, "d2"), (RE_DTWO_RELAXED, "d2_relaxed")):
                    m = rx.search(text)
                    if not m:
                        continue
                    for lm in RE_LCLASS.finditer(m.group(1)):
                        cand = lm.group(1).replace("/", ".").split("$", 1)[0]
                        if "." in cand and not cand.startswith(
                            ("kotlin.", "java.", "android")
                        ):
                            real = cand
                            counts[technique] += 1
                            break
                    if real:
                        break

            if not real:
                m = RE_RENAMED.search(text)
                if m:
                    real = m.group(1)
                    counts["renamed"] += 1

            if real:
                mapping[obf] = real
                file_real[obf] = path

    return mapping, file_real, dict(counts)


def write_outputs(
    out: str, mapping: dict[str, str], file_real: dict[str, str]
) -> dict[str, list]:
    os.makedirs(os.path.join(out, "by_package"), exist_ok=True)

    with open(os.path.join(out, "mapping.tsv"), "w", encoding="utf-8") as f:
        f.write("obf_fqn\treal_fqn\tfile\n")
        for k in sorted(mapping):
            f.write(f"{k}\t{mapping[k]}\t{file_real[k]}\n")

    with open(os.path.join(out, "mapping.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)

    by_pkg: dict[str, list] = defaultdict(list)
    for obf, real in mapping.items():
        pkg = real.rsplit(".", 1)[0] if "." in real else "(default)"
        by_pkg[pkg].append((real, obf, file_real[obf]))

    for pkg, rows in by_pkg.items():
        safe = os.path.basename(pkg).replace(".", "_") or "default"
        with open(
            os.path.join(out, "by_package", f"{safe}.txt"), "w", encoding="utf-8"
        ) as f:
            for real, obf, p in sorted(rows):
                f.write(f"{real}\t{obf}\t{p}\n")

    return by_pkg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Recover original Kotlin class names from R8 output (Phase 3.5)."
    )
    ap.add_argument("sources", help="decompiled sources directory")
    ap.add_argument(
        "output",
        nargs="?",
        default=None,
        help="output dir (default: <sources>/../mapping)",
    )
    args = ap.parse_args(argv)

    src = args.sources
    if not os.path.isdir(src):
        print(f"not a directory: {src}", file=sys.stderr)
        return 1
    out = args.output or os.path.join(os.path.dirname(os.path.abspath(src)), "mapping")

    mapping, file_real, counts = recover(src)
    by_pkg = write_outputs(out, mapping, file_real)

    print(f"Recovered {len(mapping)} class names")
    for k, v in sorted(counts.items()):
        print(f"  via {k}: {v}")
    print(f"Real packages: {len(by_pkg)}")
    print(f"Wrote {out}/mapping.tsv, mapping.json, by_package/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
