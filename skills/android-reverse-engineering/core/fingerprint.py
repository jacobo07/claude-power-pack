#!/usr/bin/env python3
"""fingerprint.py -- Triage an APK/XAPK/APKS/APKM before decompiling.

Cross-platform port of upstream ``scripts/fingerprint.sh``
(android-reverse-engineering-skill, Apache-2.0, (c) Simone Avogadro).
See ../NOTICE.md.

Why this port exists: the upstream script needs ``unzip``, ``strings`` and
POSIX ``grep``. None of those are present on a stock Windows host, which is
where this Power Pack runs, so Phase 0 -- the single highest-leverage step,
because it is what tells you NOT to spend an hour decompiling a Flutter app
-- was unreachable. Python's stdlib covers every primitive the script used,
so one implementation now serves Windows, Linux and macOS instead of two
that drift.

Framework, HTTP, DI, serialization and SDK detection are deliberately
identical to the bash original -- the same marker regexes in the same
priority order -- because a silent fork there would be a bug, not an
improvement.

Obfuscation detection is the ONE deliberate divergence, and the Kotlin flag
follows from it. Both are documented at their definitions below and in
../NOTICE.md. Read that before "restoring" upstream behaviour.

Usage:
    python fingerprint.py <file.apk|file.xapk> [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile

# DEX type descriptors look like "Lcom/foo/Bar;". Extract the inner
# slash-separated FQN so callers can match e.g. 'io/ktor/' directly.
# Applied to raw dex bytes: dex string data is ASCII/MUTF-8, so a byte-level
# scan is equivalent to `strings -n 8 | grep -oE` and is an order of
# magnitude faster than materialising every printable run first.
DEX_TYPE_RE = re.compile(rb"L[a-z][a-zA-Z0-9_]*(?:/[a-zA-Z0-9_$]+)+;")

SHORT_ROOT_RE = re.compile(r"^[a-z]{1,2}/")
NATIVE_LIB_RE = re.compile(r"^lib/[^/]+/[^/]+\.so$")


class Fingerprint:
    """Aggregated evidence for one package (base APK plus any splits)."""

    def __init__(self, listing: list[str], dex_types: set[str]) -> None:
        self.listing = listing
        self.dex_types = dex_types
        self._listing_blob = "\n".join(listing)
        self._dex_blob = "\n".join(sorted(dex_types))

    def has(self, pattern: str) -> bool:
        """True when *pattern* matches a zip entry path or a dex type name.

        Mirrors the bash ``has()`` helper, which grepped both corpora with a
        single ERE. Multiline mode keeps ``^``/``$`` anchored per entry.
        """
        rx = re.compile(pattern, re.MULTILINE)
        return bool(rx.search(self._listing_blob) or rx.search(self._dex_blob))

    # -- framework -----------------------------------------------------
    def framework(self) -> tuple[str, str]:
        """Return (framework, rationale). First match wins, as upstream."""
        if self.has(r"^lib/[^/]+/libflutter\.so$"):
            rationale = "lib/<abi>/libflutter.so present"
            if self.has(r"^lib/[^/]+/libapp\.so$"):
                rationale += "; libapp.so contains AOT-compiled Dart"
            return "Flutter", rationale

        rn_markers = [
            (r"^lib/[^/]+/libhermes\.so$", "libhermes.so"),
            (r"^lib/[^/]+/libreactnativejni\.so$", "libreactnativejni.so"),
            (r"^assets/index\.android\.bundle$", "assets/index.android.bundle"),
        ]
        rn_hits = [label for rx, label in rn_markers if self.has(rx)]
        if rn_hits:
            return "React Native", " ".join(rn_hits)

        if (
            self.has(r"^assets/www/index\.html$")
            or self.has(r"^assets/www/cordova\.js$")
            or self.has(r"^assets/public/index\.html$")
        ):
            return (
                "Cordova / Capacitor (WebView hybrid)",
                "assets/www/ or assets/public/ shell present",
            )

        if self.has(r"^lib/[^/]+/libmonodroid\.so$") or self.has(r"^assemblies/"):
            return (
                "Xamarin / .NET MAUI",
                "libmonodroid.so or assemblies/ present -- code is in .NET DLLs",
            )

        if self.has(r"^lib/[^/]+/libmaui\.so$"):
            return ".NET MAUI", "libmaui.so present"

        if self.has(r"^assets/flutter_assets/") and not self.has(
            r"^lib/[^/]+/libflutter\.so$"
        ):
            return (
                "Flutter (code-only split?)",
                "flutter_assets/ but no libflutter.so in this APK -- check splits",
            )

        if self.has(r"androidx\.compose"):
            return (
                "Native Android (Kotlin + Jetpack Compose)",
                "androidx.compose.* libraries detected",
            )
        if self.has(r"^META-INF/.*\.kotlin_module$"):
            return (
                "Native Android (Kotlin)",
                "kotlin_module metadata present, no Compose markers",
            )
        return (
            "Native Android (Java/Kotlin)",
            "no cross-platform framework markers found",
        )

    # -- stacks --------------------------------------------------------
    def _collect(self, table: list[tuple[str, str]]) -> list[str]:
        return [label for rx, label in table if self.has(rx)]

    def http_stack(self) -> list[str]:
        return self._collect([
            (r"retrofit2", "Retrofit"),
            (r"okhttp3", "OkHttp"),
            (r"io/ktor/", "Ktor"),
            (r"com/apollographql/", "Apollo (GraphQL)"),
            (r"com/android/volley", "Volley"),
        ])

    def di_stack(self) -> list[str]:
        di = self._collect([
            (r"dagger/hilt/", "Hilt"),
            (r"^META-INF/.*dagger.*", "Dagger"),
            (r"org/koin/", "Koin"),
        ])
        # Upstream only reports the generic marker when nothing specific hit.
        if not di and self.has(r"javax/inject/"):
            di.append("javax.inject")
        return di

    def serialization(self) -> list[str]:
        return self._collect([
            (r"kotlinx/serialization/", "kotlinx.serialization"),
            (r"com/google/gson/", "Gson"),
            (r"com/squareup/moshi/", "Moshi"),
            (r"com/fasterxml/jackson/", "Jackson"),
        ])

    def sdks(self) -> list[str]:
        return self._collect([
            (r"^assets/com/appsflyer/", "AppsFlyer"),
            (r"datadog\.buildId|com/datadog/", "Datadog"),
            (r"io/sentry/", "Sentry"),
            (r"com/google/firebase/", "Firebase"),
            (r"com/google/android/gms/", "Google Play Services"),
            (r"com/facebook/", "Facebook SDK"),
            (r"com/payu/", "PayU"),
            (r"com/stripe/", "Stripe"),
            (r"com/braintreepayments/", "Braintree"),
            (r"com/storyteller/", "Storyteller"),
            (r"zendesk/", "Zendesk"),
            (r"com/intercom/", "Intercom"),
            (r"com/segment/analytics", "Segment"),
            (r"com/amplitude/", "Amplitude"),
            (r"com/mixpanel/", "Mixpanel"),
            (r"com/onesignal/", "OneSignal"),
            (r"com/microsoft/clarity", "Microsoft Clarity"),
            (r"com/hotjar/", "Hotjar"),
            (r"com/instabug/", "Instabug"),
        ])

    # -- obfuscation ---------------------------------------------------
    #
    # DELIBERATE DIVERGENCE FROM UPSTREAM -- read this before "restoring"
    # the original behaviour.
    #
    # Upstream counts single/double-letter directories in the ZIP LISTING.
    # In any modern APK the classes are packed inside classes*.dex, so no
    # package ever appears as a zip path, and that count is 0 for every
    # app -- an instrument that cannot return the other answer. Measured
    # 2026-09-19 on two real APKs: both reported 0 listing-roots, i.e.
    # "LOW", while one of them is 122/133 single-letter dex packages (R8,
    # unmistakably obfuscated) and the other genuinely is not.
    #
    # This matters functionally rather than cosmetically: SKILL.md gates
    # Phase 3.5 (Kotlin name recovery) on Phase 0 reporting moderate/high
    # obfuscation, so under the upstream signal that gate never opens and
    # the skill's flagship R8 feature is unreachable.
    #
    # The dex-derived signal is therefore authoritative here, and the
    # upstream listing count is retained and reported beside it so the
    # divergence stays visible instead of silent.
    #
    # A count alone false-positives on small packages and a ratio alone is
    # satisfied by shrinking the denominator, so both must clear.
    def obfuscation(self) -> tuple[str, dict]:
        listing_roots = {
            m.group(0) for e in self.listing if (m := SHORT_ROOT_RE.match(e))
        }
        dex_roots = {t.split("/")[0] for t in self.dex_types}
        short_dex = {r for r in dex_roots if len(r) <= 2}
        total, short = len(dex_roots), len(short_dex)
        ratio = (short / total) if total else 0.0

        evidence = {
            "dex_root_packages": total,
            "short_dex_root_packages": short,
            "short_dex_ratio": round(ratio, 3),
            "listing_short_roots": len(listing_roots),
            "sample": sorted(short_dex)[:12],
        }

        if short >= 20 and ratio >= 0.40:
            verdict = f"HIGH ({short}/{total} single/double-letter dex packages)"
        elif short >= 8 and ratio >= 0.25:
            verdict = f"MODERATE ({short}/{total} short dex packages)"
        elif len(listing_roots) > 30:
            verdict = f"HIGH ({len(listing_roots)} short dirs in zip listing)"
        elif len(listing_roots) > 10:
            verdict = f"MODERATE ({len(listing_roots)} short dirs in zip listing)"
        else:
            verdict = f"LOW ({short}/{total} short dex packages)"
        return verdict, evidence

    def native_libs(self) -> list[str]:
        return sorted({e for e in self.listing if NATIVE_LIB_RE.match(e)})

    def buildconfig(self) -> str:
        if self.has(r"BuildConfig\.class$"):
            return "present (grep BuildConfig.java after decompile for base URLs / flavor)"
        return "not detected in zip listing (still worth grepping after decompile)"


def _read_apk(path: str) -> tuple[list[str], set[str]]:
    """Return (zip entry names, dex type names) for a single APK."""
    names: list[str] = []
    types: set[str] = set()
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            for entry in names:
                if not re.fullmatch(r"classes[0-9]*\.dex", entry):
                    continue
                try:
                    blob = zf.read(entry)
                except (KeyError, OSError, zipfile.BadZipFile, RuntimeError):
                    continue
                for m in DEX_TYPE_RE.finditer(blob):
                    types.add(m.group(0)[1:-1].decode("ascii", "replace"))
    except (zipfile.BadZipFile, OSError) as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
    return names, types


def collect(input_path: str) -> tuple[Fingerprint, list[str]]:
    """Resolve *input_path* to its APK members and aggregate their evidence."""
    lower = input_path.lower()
    apks: list[str] = []
    tmpdir = None

    if lower.endswith((".xapk", ".apks", ".apkm")):
        tmpdir = tempfile.mkdtemp(prefix="apkfp.")
        with zipfile.ZipFile(input_path) as zf:
            zf.extractall(tmpdir)
        # Upstream used `find -maxdepth 2`; match that depth bound.
        for root, _dirs, files in os.walk(tmpdir):
            depth = os.path.relpath(root, tmpdir).count(os.sep)
            if os.path.relpath(root, tmpdir) == ".":
                depth = -1
            if depth > 0:
                continue
            for f in files:
                if f.lower().endswith(".apk"):
                    apks.append(os.path.join(root, f))
    elif lower.endswith(".apk"):
        apks = [input_path]
    else:
        raise SystemExit(f"Unsupported input: {input_path}")

    if not apks:
        raise SystemExit(f"No APK members found inside {input_path}")

    listing: list[str] = []
    types: set[str] = set()
    for apk in sorted(apks):
        n, t = _read_apk(apk)
        listing.extend(n)
        types |= t

    return Fingerprint(listing, types), apks


RECOMMENDATIONS = [
    ("Flutter", [
        "Java decompilation will yield ~no app code. The Dart logic lives in",
        "libapp.so (AOT). Use tools designed for Flutter:",
        "  - reFlutter / Doldrums / blutter (extract Dart class structure)",
        "  - strings/rabin2 on libapp.so for endpoints & string constants",
    ]),
    ("React", [
        "Java code is just the RN host. Real app logic is in JS/Hermes:",
        "  - if Hermes: hbctool disasm assets/index.android.bundle",
        "  - if JSC:    js-beautify the bundle and grep for 'fetch('/'axios'",
    ]),
    ("Cordova", [
        "All app code is in assets/www/ (or assets/public/). Just unzip and",
        "inspect the HTML/JS -- no Java decompile needed.",
    ]),
    ("Xamarin", [
        "App logic is in .NET DLLs (assemblies/). Use ILSpy or dotPeek;",
        "jadx will only show the Mono host.",
    ]),
    (".NET", [
        "App logic is in .NET DLLs (assemblies/). Use ILSpy or dotPeek;",
        "jadx will only show the Mono host.",
    ]),
]


def recommendation(framework: str) -> list[str]:
    for prefix, lines in RECOMMENDATIONS:
        if framework.startswith(prefix):
            return lines
    return ["Proceed with Phase 2: decompile.ps1 / decompile.sh <file>"]


def build_report(path: str) -> dict:
    fp, apks = collect(path)
    framework, rationale = fp.framework()
    obf, obf_evidence = fp.obfuscation()
    # Read Kotlin off the dex evidence, not off the framework label. The
    # label's fallback branch happens to contain the word "Kotlin", which
    # would make the flag true by accident; and R8 can strip the
    # .kotlin_module files the framework branch keys on, so an obfuscated
    # Kotlin app -- precisely the Phase 3.5 case -- can lose that marker.
    kotlin = (
        fp.has(r"^kotlinx?/")
        or fp.has(r"^META-INF/.*\.kotlin_module$")
        or fp.has(r"androidx\.compose")
    )
    # Phase 3.5 is only worth running when R8 mangled the names AND the app
    # is Kotlin -- the recovery reads Kotlin metadata that R8 cannot strip.
    # Recovery is cheap and degrades to "0 names recovered", so this errs
    # toward recommending it: a false positive costs a minute, a false
    # negative costs the skill's whole deobfuscation capability.
    needs_recovery = kotlin and obf.startswith(("HIGH", "MODERATE"))
    return {
        "file": os.path.basename(path),
        "members": [os.path.basename(a) for a in apks],
        "framework": framework,
        "rationale": rationale,
        "obfuscation": obf,
        "obfuscation_evidence": obf_evidence,
        "kotlin": kotlin,
        "needs_kotlin_recovery": needs_recovery,
        "http_stack": fp.http_stack(),
        "di": fp.di_stack(),
        "serialization": fp.serialization(),
        "buildconfig": fp.buildconfig(),
        "sdks": fp.sdks(),
        "native_libs": fp.native_libs(),
        "entry_count": len(fp.listing),
        "dex_type_count": len(fp.dex_types),
        "recommendation": recommendation(framework),
    }


def render(r: dict) -> str:
    def joined(key: str) -> str:
        return ", ".join(r[key]) if r[key] else "none detected"

    out = [f"=== APK Fingerprint: {r['file']} ===", ""]
    if len(r["members"]) > 1:
        out.append(f"Members:          {len(r['members'])} APKs ({', '.join(r['members'])})")
    out += [
        f"Framework:        {r['framework']}",
        f"  Rationale:      {r['rationale']}",
        f"Obfuscation:      {r['obfuscation']}",
        "",
        f"HTTP stack:       {joined('http_stack')}",
        f"DI:               {joined('di')}",
        f"Serialization:    {joined('serialization')}",
        f"BuildConfig:      {r['buildconfig']}",
        "",
        f"Third-party SDKs: {joined('sdks')}",
        "",
        "Native libraries (consolidated across splits):",
    ]
    out += [f"  {lib}" for lib in r["native_libs"]] or ["  (none)"]
    ev = r["obfuscation_evidence"]
    out += [
        "",
        f"Scanned:          {r['entry_count']} zip entries, {r['dex_type_count']} dex type names",
        f"  Obf evidence:   {ev['short_dex_root_packages']}/{ev['dex_root_packages']} short dex "
        f"packages (ratio {ev['short_dex_ratio']}), "
        f"{ev['listing_short_roots']} short zip-listing roots",
        "",
        "Recommended next step:",
    ]
    out += [f"  {line}" for line in r["recommendation"]]
    if r["needs_kotlin_recovery"]:
        out += [
            "",
            "  Obfuscated Kotlin detected -- run Phase 3.5 before tracing call flows:",
            "    python core/recover_kotlin_names.py <output>/sources <output>/mapping",
        ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Triage an APK/XAPK before decompiling (Phase 0)."
    )
    ap.add_argument("input", help="path to .apk, .xapk, .apks or .apkm")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"File not found: {args.input}", file=sys.stderr)
        return 1

    report = build_report(args.input)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
