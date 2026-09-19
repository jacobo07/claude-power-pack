---
name: android-reverse-engineering
description: Decompile Android APK, XAPK, JAR and AAR files with jadx or Fernflower/Vineflower, recover R8-obfuscated Kotlin class names, extract HTTP API endpoints (Retrofit, OkHttp, Ktor, Apollo, Volley), and trace call flows from UI down to the network layer. Use when the user wants to decompile, analyse or reverse engineer an Android package, find an app's API endpoints, or follow a call flow through decompiled code.
trigger: decompile APK|decompile XAPK|reverse engineer Android|extract API|analyze Android|analyse Android|jadx|fernflower|vineflower|follow call flow|decompile JAR|decompile AAR|Android reverse engineering|find API endpoints|APK teardown|deobfuscate Kotlin
---

# Android Reverse Engineering

Absorbed from [SimoneAvogadro/android-reverse-engineering-skill](https://github.com/SimoneAvogadro/android-reverse-engineering-skill)
(Apache-2.0, v1.5.0, commit `04fe39c`). **Read `NOTICE.md` before changing
anything under `scripts/` or `references/`** — those are verbatim upstream, and
the one deliberate behavioural divergence is documented there.

## Scope gate

Decompile packages you own, published packages you are authorised to analyse,
or artefacts under an engagement that permits it. If the target's provenance is
unclear, establish it before Phase 1 rather than after Phase 5 — this workflow
extracts credentials and endpoints, and that is not something to discover you
were not entitled to do.

## Prerequisites

| Tool | Required | Status on this host (2026-09-19) |
|---|---|---|
| Java JDK 17+ | yes | present — `C:\Users\User\Apps\jdk-17` |
| jadx | yes | **not installed** — install on first use |
| Vineflower / Fernflower | optional | not installed |
| dex2jar | optional | needed only for Fernflower on APK/DEX |
| Python 3.10+ | yes, for `core/` | present |

Phase 0 and Phase 3.5 need **only Python** — they run before any decompiler
exists, which is the point: the fingerprint is what tells you whether
installing jadx is worth doing at all.

Check and install:

```powershell
& "<skill>/scripts/check-deps.ps1"
& "<skill>/scripts/install-dep.ps1" jadx
```

```bash
bash <skill>/scripts/check-deps.sh
bash <skill>/scripts/install-dep.sh jadx
```

`check-deps` emits machine-readable `INSTALL_REQUIRED:<dep>` /
`INSTALL_OPTIONAL:<dep>` lines. Exit 1 means a required dep is missing. Do not
enter Phase 2 until required deps are OK. On Windows the install script tries
winget, then scoop, then choco, and otherwise downloads to
`%USERPROFILE%\.local\share\`; `check-deps.ps1` and `decompile.ps1` refresh PATH
from the user environment, so a newly installed tool is found without
restarting the terminal.

## Phase 0 — Fingerprint first. Always.

**Decompiling Java is close to useless for Flutter, React Native,
Cordova/Capacitor and Xamarin apps** — the real code is in `libapp.so`, a Hermes
bundle, `assets/www/`, or .NET assemblies. One command tells you which world you
are in, in seconds, before you spend an hour in the wrong one.

```powershell
python <skill>/core/fingerprint.py <file.apk|file.xapk> [--json]
```

Reports: framework (with the file marker that decided it), HTTP stack, DI and
serialisation, obfuscation level, consolidated native libraries across all
splits, notable third-party SDKs, and a **recommended next step that differs by
framework**. If it says Flutter / RN / Cordova / Xamarin, stop and switch
tooling — Phases 1–5 assume a native Java/Kotlin app.

`--json` emits the same findings machine-readably, including
`needs_kotlin_recovery`, which gates Phase 3.5.

> **Obfuscation reading diverges from upstream, deliberately.** Upstream counts
> short directory names in the zip listing, which is `0` for every modern APK
> because classes live inside `classes.dex`. `core/fingerprint.py` reads dex
> package names instead and reports the upstream count beside it. Rationale and
> measurements: `NOTICE.md`.

## Phase 1 — Dependencies

Covered above. Optional deps are worth installing when the first pass produces
warnings: Vineflower gives better output on complex Java, dex2jar is what lets
Fernflower touch an APK at all.

## Phase 2 — Decompile

```powershell
& "<skill>/scripts/decompile.ps1" [-Deobf] [-NoRes] [-Engine jadx|fernflower|both] [-o <dir>] <file>
```

```bash
bash <skill>/scripts/decompile.sh [--deobf] [--no-res] [--engine jadx|fernflower|both] [-o <dir>] <file>
```

| Situation | Engine |
|---|---|
| First pass on any APK | `jadx` — fastest, handles resources |
| JAR / AAR library | `fernflower` — better Java output |
| jadx output has warnings or broken code | `both`, then pick the better class |
| Complex lambdas, generics, streams | `fernflower` |
| Quick overview of a large APK | `jadx --no-res` |

**XAPK** bundles are extracted and every inner APK decompiled into its own
subdirectory. **Split/bundle wrappers** are detected automatically: when jadx
produces ≤10 Java files and inner APKs are present, `base.apk` is re-decompiled
into `<output>/base/`, and the real sources land in `<output>/base/sources/`.

With `--engine both`, output goes to `<output>/jadx/` and
`<output>/fernflower/` with a comparison summary.

## Phase 3 — Analyse structure

1. **`<output>/resources/AndroidManifest.xml`** — launcher Activity, all
   components, permissions (`INTERNET`, `ACCESS_NETWORK_STATE`), and the
   `android:name` application class.
2. **Package survey** under `<output>/sources/` — separate app code from
   vendored libraries; head for packages named `api`, `network`, `data`,
   `repository`, `service`, `retrofit`, `http`.
3. **Read every `BuildConfig.java`.** Almost never obfuscated, and frequently
   the highest-signal constants in the whole APK — base URLs, flavour, build
   type, third-party keys, feature flags. One per Gradle module, so expect
   several. Read all of them.
4. **Identify the architecture** — `Presenter` (MVP), `ViewModel` +
   `LiveData`/`StateFlow` (MVVM), `domain`/`data`/`presentation` (Clean). This
   tells you where the network calls will be.

## Phase 3.5 — Recover Kotlin names (obfuscated Kotlin only)

Run when Phase 0 reports `needs_kotlin_recovery`. R8 mangles JVM symbols but
cannot strip Kotlin metadata — the runtime needs it — so original FQNs leak
through `@DebugMetadata` and `@Metadata.d2`.

```powershell
python <skill>/core/recover_kotlin_names.py <output>/sources <output>/mapping
```

Then query the map instead of grepping blind — every hit is annotated with its
owning class's real name:

```powershell
python <skill>/core/lookup_name.py <output>/mapping --grep "\"/api/" <output>/sources
python <skill>/core/lookup_name.py <output>/mapping -o a.b.C
python <skill>/core/lookup_name.py <output>/mapping -p com.acme.data
```

Expect 30–50% of classes overall, and in practice most of the `*Repository` /
`*ViewModel` / `*UseCase` / `*Impl` classes you actually want. A recovery of
`0` is a real answer, not a failure: it means the app's own code carries no
Kotlin metadata (measured once on a Java/AdMob app where all 2,011
metadata-bearing files were vendor SDKs and correctly skipped).

Technique and limits: `references/kotlin-name-recovery.md`.

## Phase 4 — Trace call flows

1. Start at the launcher Activity or Application class from Phase 3.
2. `Application.onCreate()` usually builds the HTTP client, base URL and DI
   graph — read it first.
3. Follow `onCreate()` → view setup → click listener → ViewModel/Presenter →
   Repository → API interface → the HTTP call.
4. Map `@Module` classes when Dagger/Hilt is present, to learn which
   implementation backs which interface.
5. **When names are mangled, anchor on what R8 cannot rename**: string
   literals, Retrofit annotations and URLs are never obfuscated. With a Phase
   3.5 mapping in hand, use `lookup_name.py --grep` instead of raw grep.

Techniques and ready-made greps: `references/call-flow-analysis.md`.

## Phase 5 — Extract and document APIs

```powershell
& "<skill>/scripts/find-api-calls.ps1" <output>/sources [-Retrofit|-OkHttp|-Volley|-Urls|-Auth]
```

```bash
bash <skill>/scripts/find-api-calls.sh <output>/sources [--retrofit|--urls|--auth]
```

Document in **two tiers**. Going deep on every endpoint is prohibitively
expensive on an app with 100+ paths, and most do not warrant it.

**Tier 1 — flat inventory, always.** One line per endpoint; `?` for anything
you cannot determine. This answers "what does the backend look like" in one
screen.

| Host | Method | Path | Auth | Source file |
|---|---|---|---|---|
| `api.example.com` | GET | `/v1/users/profile` | Bearer | `com/example/api/UserApi.java` |

**Tier 2 — per-endpoint detail, only where it earns it**: the whole auth flow
(login, refresh, logout, OTP, registration), payment/checkout/order creation,
anything the user explicitly asked about, and anything that looked unusual
during the scan (custom signing, undocumented headers).

```markdown
### `METHOD /path`
- **Source**: `com.example.api.ApiService` (ApiService.java:42)
- **Base URL**: `https://api.example.com/v1`
- **Path / query params**: `id` (String) · `page` (int), `limit` (int)
- **Headers**: `Authorization: Bearer <token>`
- **Request body**: `{ "email": "string", "password": "string" }`
- **Response**: `ApiResponse<User>`
- **Called from**: `LoginActivity → LoginViewModel → UserRepository → ApiService`
```

Default to ≤10 Tier 2 entries unless asked for more. Tier 1 plus a Tier 2 deep
dive on auth and one or two key flows is what consumers of this work actually
want.

Library-specific patterns and the full template:
`references/api-extraction-patterns.md`.

## Deliverables

1. Decompiled source in the output directory
2. Architecture summary — structure, main packages, pattern
3. API documentation — Tier 1 inventory, Tier 2 where warranted
4. Call flow map — UI to network for auth and the main features
5. Any credential or key found, reported as a finding rather than pasted into
   chat verbatim (HR-SECRET-002: route through redaction)

## Done-gate

```powershell
python tools/test_android_re.py   # from the Power Pack repo root
```

Exit 0. Drives Phase 0 and Phase 3.5 from both poles on synthetic APKs, plus
attribution and executability checks. It does **not** prove the decompile
wrapper works — that needs jadx installed, and the first real decompile is its
first test.

## References

- `references/setup-guide.md` — installing Java, jadx, Vineflower, dex2jar
- `references/jadx-usage.md` — jadx CLI
- `references/fernflower-usage.md` — Fernflower/Vineflower CLI and APK workflow
- `references/api-extraction-patterns.md` — per-library search patterns
- `references/call-flow-analysis.md` — call-flow tracing techniques
- `references/kotlin-name-recovery.md` — the R8 metadata technique
- `references/third_party_hosts.txt` — known third-party hosts, to filter noise
- `upstream/` — the original SKILL.md and `/decompile` command, for diffing
