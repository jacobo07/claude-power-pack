# Apex Onboarding Standard

Sealed **2026-05-19** at the close of the Power Pack Globalization /
KERNEL vMAX-NULL-ERROR cycle. Mandatory baseline for any new
multi-file shippable that introduces — or modifies — the path a
fresh user takes from `git clone` to `S++`.

This standard sits orthogonal to the existing apex baselines: it does
**not** redefine concurrency (Axis A), async auditing (Axis B), or
feature-completion gates. It seals the *onboarding* axis specifically
— the contract that any first-time user, on any host, reaches the
S++ baseline in ≤ 5 minutes via one wrapper script and one
`/restart`, with zero hidden state.

## The five contracts

A globalization-class deliverable is **not** sealed until every
contract below holds with executed, real-input evidence (no mocks,
no dry-runs that never touch the system).

### 1. One wrapper, two surfaces (per-user vs per-project)

The repo ships **two** clearly-named installers; one is per-user
global, the other is per-project. They never alias each other.

| Surface         | Wrapper                              | Touches                                              |
|-----------------|--------------------------------------|------------------------------------------------------|
| Per-user global | `install-global.{ps1,sh}`            | `~/.claude/agents/`, `~/.claude/commands/`, never the project tree. |
| Per-project     | `install.{ps1,sh}`                   | `<project>/CLAUDE.md`, `<project>/.claude/`, never `~/.claude/`. |

The wrapper banner prints the surface identity ("PER-USER GLOBAL
installer (NOT per-project!)" — verbatim) so an Owner who runs the
wrong one notices before any mutation. The decision table lives in
`docs/INSTALL-GLOBAL.md`, not in the wrapper output, so the wrapper
stays short.

### 2. Mirror-Sync-Direction is asymmetric (loose → PP only)

Hooks live in `~/.claude/hooks/<file>.js`. The auto-mode classifier
hard-denies any agent-driven write into that directory, regardless
of how broad a per-path glob the Owner has authorized. This is not a
gate to route around; it is the sealed boundary between
"agent-replicable canonical" and "Owner-installed instrumentation."

Consequence for the installer:
* The installer **never** ships hooks. It PRINTS a copy checklist
  (`cp <repo>/hooks/<name> ~/.claude/hooks/<name>`) and the matching
  `settings_merger.py register-*` invocations the Owner pastes once.
* The A1/A2 sync direction is **loose → PP only**: when a hook
  drifts ahead of the canonical, the canonical is updated by reading
  the loose; the reverse direction (PP → loose) is hand-copied per
  the printed checklist.
* `tools/_inventory/hooks.json` is intentionally empty
  (`count: 0`) — listing a hook in inventory would imply
  installer-driven shipping, which the boundary forbids.

(Source: MEMORY entry
`feedback_mirror_sync_direction_and_hooks_dir_deny.md`, 2026-05-19.)

### 3. Installer PRINTS rather than writes capability grants

The auto-mode classifier denies the agent **adding the code that
adds rules** to `permissions.allow`, even when the Owner has
previously authorized a specific rule. Two distinct authorizations
that do not compose:

1. *"You may add THIS rule."* — specific grant.
2. *"You may add the CODE that adds rules."* — meta-grant.

(1) does **not** imply (2). The classifier reads the *content* of
the edit and refuses meta-capability additions to security-relevant
tooling.

Consequence:
* `tools/install_global_core.py` never calls a hypothetical
  `register-permission` subcommand. It calls only the
  already-authorized `register-sessionstart` / `register-stop` /
  `register-userprompt` / `register-pretool` subcommands.
* It PRINTS the exact `permissions.allow` rules the Owner pastes
  manually, via `_print_permissions_checklist()`. The Owner is
  always the writer of last resort for capability grants.

(Source: session_lessons.md "Lesson — Classifier blocks adding the
CAPABILITY…", 2026-05-19, Globalization B1.)

### 4. Clean-machine verification is Path A (real HOME redirect)

Onboarding is sealed iff `tools/e2e_clean_install.py` (or its
equivalent) exits 0 with three gates green:

1. **Dry-run non-destructive** — `--dry-run` against a sandboxed
   HOME leaves the sandbox empty.
2. **Apply populates the tree** — a real apply drops at least one
   agent and one command into the sandbox HOME, confirming that
   `Path.home()` respects the `USERPROFILE` / `HOME` redirect.
3. **Idempotent re-apply** — a second apply reports ≥ 1
   `unchanged` and zero `installed` / `updated` / `error` (SHA-skip
   working). `missing-source` is allowed to be non-zero — it is
   inventory-residue, independent of idempotency.

`HOME / USERPROFILE / APPDATA / LOCALAPPDATA / CLAUDE_CONFIG_DIR`
are all set together so any nested subprocess
(`settings_merger.py`, `node`) is sandboxed identically.

If a host fails Path A (`Path.home()` bypasses the env via Win32
token), the plan-authorized Path B fallback applies: a verified
`--dry-run` + an idempotent second-run on the real install + an S++
verifier pass, all three logged as the evidence file.

(Source: vault/audits/clean_install_2026-05-19T15-41-52Z.json — the
canonical evidence file from this cycle.)

### 5. Verification is real subprocess composition, not assertion

The onboarding verifier (`tools/verify_spp.py`) is the umbrella that
composes every sub-verifier as a real subprocess row. No row is a
fabricated boolean. If a sub-verifier is missing, the row surfaces
as `MISSING` (red) — never silently skipped.

Strict rows (each must exit 0):
* `mirror-parity` — `tools/verify_global_mirrors.py`.
* `drift-report` — `tools/drift_report.py`.
* `paths+secrets` — `tools/normalize_paths.py --check`.
* `rtk-fusion` — `tools/verify_rtk_fusion.py`.
* `intent-lock` — `modules/harness/intent_lock.js --self-test`.
* `l3-engine` — `tools/test_l3_intent.js`.

Advisory rows (allowed to fail without failing the gate):
* `programmatic-budget` — `tools/verify_full_install.py`, scoped
  to RTK + JIT + pricing; a missing `budget.json` or stale pricing
  is an Owner-side concern, not an S++ gate failure on a fresh
  install.

`tools/verify_spp.py` exit 0 = S++ baseline reached for this host.
Re-run individual rows with `--row <name>` for targeted diagnosis.

## Operational lessons sealed into this standard

Each lesson below cites its session-lessons-md entry; the standard
itself does not re-litigate the reasoning.

* **Chunked-write doctrine for deep-session large files** —
  `session_lessons.md` 2026-05-19, "Internal-error generalises from
  Edit to Write". Any new file expected > 150 lines after > 30
  turns in-session is written as a small scaffold first +
  follow-up Edit, never as one large Write. Probe (`ls` / `Read` /
  `wc -l`) before any retry — never blind-retry a Write that
  returned internal-error.

* **rc=1 from missing-source is not an installer bug** —
  `install_global_core.py:442-443`. The installer's strict rc
  composes `error + missing-source + nc_fail + hr_failures`;
  verifiers that consume the installer must decouple
  sandbox-viability ("did files land?") from rc, and read
  `counters` directly from the sidecar at
  `~/.claude/.pp-install-report.<iso>.json` (key: `counters`, not
  `rows`).

* **Backup retention is a contract** — 5 sets at
  `~/.claude/.pp-backups/<iso>/`, older ones pruned in-place at
  install time. Restore is a one-line `cp` against that directory
  layout; there is no `pp-restore` CLI by design (the directory
  layout *is* the contract).

## Cross-references

* `vault/standards/feature-completion-standard.md` — hooks &
  harnesses gate; this onboarding standard inherits its
  "real-input evidence" rule.
* `vault/standards/mirror-parity-law.md` — the canonical mirror
  set; this onboarding standard treats `tools/_inventory/*.json`
  as the curated allow-list derived from it.
* `~/.claude/knowledge_vault/core/apex-completion-standard.md` —
  Axes A (Intent-Lock) and B (Async-Audit); this onboarding standard
  is the third axis (Onboarding).
* `vault/knowledge_base/apex_baseline_doctrine.md` — Apex
  completeness mandate; this standard is the operational
  consequence for the onboarding surface specifically.
* `docs/INSTALL-GLOBAL.md` — the 5-minute new-user walkthrough.
  Any change to it must be reflected here, and vice versa.

## Sealed evidence (this cycle)

| Artifact | Commit | What it proves |
|----------|--------|----------------|
| `tools/install_global_core.py` | (B1) | Installer logic; SHA-skip idempotent; backups; PRINTS, never writes. |
| `install-global.{ps1,sh}` | (B1) | Identity banner; env-scrub; wrapper invocation. |
| `tools/verify_spp.py` | `4e80ca0` | S++ umbrella verifier; 6 strict + 1 advisory rows. |
| `docs/INSTALL-GLOBAL.md` | `8cb6a5f` | 5-min new-user walkthrough; decision table. |
| `tools/e2e_clean_install.py` | `d5e6323` | Path-A HOME-redirect E2E; all three gates green. |
| `vault/audits/clean_install_2026-05-19T15-41-52Z.json` | `d5e6323` | Sealed evidence: dry-run safe, apply populates (1+9), 10 unchanged on re-apply. |
