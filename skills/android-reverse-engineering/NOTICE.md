# NOTICE — Absorbed source

This skill is an absorption of a third-party work into the Claude Power Pack.

| | |
|---|---|
| **Upstream** | [SimoneAvogadro/android-reverse-engineering-skill](https://github.com/SimoneAvogadro/android-reverse-engineering-skill) |
| **Author** | Simone Avogadro |
| **License** | Apache License 2.0 (full text in `LICENSE`) |
| **Version absorbed** | v1.5.0 |
| **Commit pinned** | `04fe39c7dcc8efa0ce39a331862fb76407d2d9dd` (2026-09-08) |
| **Absorbed** | 2026-09-19 |

Apache-2.0 §4 requires that derivative works retain attribution and state
what was changed. This file is that statement.

## Verbatim, unmodified

- `references/*` — all six reference documents plus `third_party_hosts.txt`
- `scripts/*.sh` — all seven bash scripts
- `scripts/find-api-calls.ps1` — unmodified
- `upstream/SKILL.upstream.md` — the original SKILL.md, kept for diffing
- `upstream/decompile-command.md` — the original `/decompile` command
- `LICENSE`

## Patched — PowerShell 5.1 native-stderr abort (4 sites, 3 files)

Upstream marks the PowerShell scripts "experimental". On Windows PowerShell
5.1 they abort, and the failure is not subtle:

    java.exe : openjdk version "17.0.19" 2026-04-21
    + CategoryInfo : NotSpecified: (...) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError

PS 5.1 wraps a native executable's stderr writes in an `ErrorRecord`, and
every one of these scripts sets `$ErrorActionPreference = 'Stop'`, so the
wrapped record **throws**. `java -version` writes to stderr, so
`check-deps.ps1` died at line 27 — before checking jadx, and before printing
any of the `INSTALL_REQUIRED:` lines the workflow parses. Reproduced on this
host 2026-09-19; it only appears to work when Java is *absent*, because then
the branch is skipped.

| File | Site | Fix |
|---|---|---|
| `check-deps.ps1` | java version probe | let `cmd` merge the streams |
| `install-dep.ps1` | java version probe (×2) | let `cmd` merge the streams |
| `decompile.ps1` | dex2jar invocation | scoped `ErrorActionPreference='Continue'` |

After the fix `check-deps.ps1` completes and emits `INSTALL_REQUIRED:jadx`,
exiting 1 for the correct reason. Each patched site carries an inline comment
pointing here. The `dex2jar` one is reasoned-but-unrun: no dex2jar is
installed, and the construct is identical to the one reproduced.

## Added by the Power Pack

`core/` — three cross-platform Python entry points. The upstream project
ships bash for every phase and PowerShell for only four of the seven
scripts, so on a stock Windows host **Phase 0 (fingerprint) and Phase 3.5
(Kotlin name recovery) could not run at all**: they depend on `unzip`,
`strings` and POSIX `grep`, none of which this host has. Two of the three
were already Python embedded in a bash heredoc, so this is mostly
extraction rather than a rewrite.

| File | Origin | Nature |
|---|---|---|
| `core/fingerprint.py` | `scripts/fingerprint.sh` | Port. `zipfile` replaces `unzip`; a byte-level regex over dex replaces `strings \| grep`. |
| `core/recover_kotlin_names.py` | `scripts/recover-kotlin-names.sh` | Extraction of the embedded Python. Mining logic unchanged; `.kt` added alongside `.java`. |
| `core/lookup_name.py` | `scripts/lookup-name.sh` | Extraction of the embedded Python. `--grep` searches in-process instead of shelling out to POSIX `grep`. |

`tools/test_android_re.py` (in the Power Pack `tools/` tree) — the done-gate.

## Behavioural divergence from upstream — one, deliberate

**Obfuscation detection.** Upstream counts single/double-letter directories
in the **zip listing**. In any modern APK the classes are packed inside
`classes*.dex`, so no package ever appears as a zip path and that count is
`0` for every app — an instrument that cannot return the other answer.

Measured 2026-09-19 against two real APKs on this host: both reported `0`
listing-roots, i.e. `LOW`, while one of them is **122 of 133 single-letter
dex packages** (unmistakably R8-obfuscated) and the other genuinely is not.

This is load-bearing rather than cosmetic: upstream's own SKILL.md gates
Phase 3.5 on *"Phase 0 reported moderate / high obfuscation"*, so under the
upstream signal that gate never opens and the project's flagship R8
recovery feature is unreachable.

`core/fingerprint.py` therefore derives the verdict from dex package names
(a count floor **and** a ratio must both clear, so neither a small package
nor a shrunken denominator can trip it), and reports the upstream listing
count beside it so the divergence stays visible rather than silent. The
`.sh` and `.ps1` scripts are untouched and retain upstream behaviour.

The Kotlin flag was likewise moved onto dex evidence: the upstream branch
keys on `.kotlin_module` files, which R8 can strip — so an obfuscated
Kotlin app, exactly the Phase 3.5 case, can lose the marker that would have
sent it to Phase 3.5.

## Not verified here

No end-to-end decompile has been run in this estate: `jadx` is not
installed on this host, by decision at absorption time (install on first
use). `java` is present at `C:\Users\User\Apps\jdk-17`. The wrapper
scripts `decompile.*`, `check-deps.*` and `install-dep.*` are therefore
absorbed **unexercised** — upstream marks the PowerShell ones
"experimental" — and the first real decompile is their first test.
