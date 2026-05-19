# SSOT — Claude Power Pack subsystem manifest

**Single Source of Truth** for cross-repo subsystems that live partly in this
Power Pack and partly elsewhere. Companion to the workspace manifest at
`<workspace>/docs/SSOT_KOBII_DISTILLER.md` (KobiiCraft Core Files repo).
Inscribed 2026-05-15 alongside DNA-11000 Rule-097.

---

## 1 — KobiiDistillerOS

The two halves are roles, not duplicates. There is no third instance.

| Role | Lives in | Path | Truth |
|---|---|---|---|
| **Schema contract** (22-section sealing JSON Schema v1.2) | THIS repo | `tools/distiller/schema.json` | Sovereign Sealing v1.2 (6696 B) |
| **Kernel contract** (Python-form constants, markers, helpers — declares itself "SSOT for the v1.2 distillation contract") | THIS repo | `kpp-distiller-kernel/kpp_distiller_kernel/` | own `pyproject.toml`, `pip install -e`-able; imported by the workspace engine's `prompt_madre.py` |
| **Trigger** (operational shim: `ingest` + `check` subcommands; delegates the LLM step to the running Claude Code agent against `parts/sleepy/distiller.md`) | THIS repo | `tools/distiller/run.py` | Phase D dispatcher |
| **Validator** (22-section gate) | THIS repo | `tools/distiller/validate.py` | enforced by the trigger |
| **Sleepy skill module** | THIS repo | `modules/distiller/` (`config.json`, `core.md`, `README.md`) | Skill metadata |
| **Engine** (2730 LOC: orchestrator / data_contracts / emitter / ingestor / CLI) | KobiiCraft workspace repo | `<workspace>/kobicraft_content_intelligence/distiller/` | KobiiDistillerOS v220000, commit `f3f4bc3` |

### Invariants (DNA-11000 Rule-097)

1. **The engine NEVER moves** out of the KobiiCraft workspace repo. Any
   tool here that needs it imports it.
2. **The contract NEVER duplicates.** `schema.json` lives only at
   `tools/distiller/schema.json` in THIS repo.
3. **Reciprocal manifests.** This file and the workspace
   `docs/SSOT_KOBII_DISTILLER.md` cite each other verbatim by absolute path.
4. **No symlinks.** Windows compatibility forbids them. Cross-repo
   importability uses `pip install -e` instead.

### Importability — `pip install -e` recipe

The workspace's `kobicraft_content_intelligence/pyproject.toml` (since
v270000) declares `distiller*` in `[tool.setuptools.packages.find].include`,
so any venv with access to the workspace path can do:

```bash
# 1. Engine subpackage (workspace) — exposes kobicraft_content_intelligence.distiller
python -m pip install -e <workspace>/kobicraft_content_intelligence
# 2. Kernel contract (THIS repo) — exposes kpp_distiller_kernel
python -m pip install -e ~/.claude/skills/claude-power-pack/kpp-distiller-kernel
# Verify deep import works:
python -c "from kobicraft_content_intelligence.distiller.core import orchestrator; print('OK')"
```

**Both installs are required** for the deep engine modules to import,
because `prompt_madre.py` re-exports constants from
`kpp_distiller_kernel.contract`. Verified end-to-end 2026-05-15 (v270000) —
`CORE_OK`. If you see `ModuleNotFoundError: No module named
'kpp_distiller_kernel'`, you skipped command 2.

Today the trigger (`tools/distiller/run.py`) does NOT import the engine
directly — it only does file-scaffolding and delegates the LLM step to the
running Claude Code agent. If a future PP tool needs the engine directly,
the recipe above is the way to wire it (never copy code).

### When you change something

| Change | Update |
|---|---|
| Schema `tools/distiller/schema.json` | Bump version here; touch this manifest if structure changes; ping the workspace SSOT if a contract field renames. |
| Trigger / validator (`run.py`, `ingest.py`, `validate.py`) | Edit here. No workspace change. |
| Sleepy skill module (`modules/distiller/`) | Edit here. |
| Engine code (`<workspace>/.../distiller/**`) | Commit in the workspace repo; the editable install propagates. No PP change. |

## Cross-link

- **Workspace companion manifest:** `<workspace>/docs/SSOT_KOBII_DISTILLER.md`
  (absolute on this dev host:
  `~\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files\docs\SSOT_KOBII_DISTILLER.md`)
- **DNA-11000 Rule-097** lives in
  `<workspace>/docs/KOBII_PHILOSOPHY/STANDARDS.md`.

---

## 1.1 — v230000.1 Owner Ratification (2026-05-15)

Mirror of the workspace manifest's reconciliation block (workspace path:
`<workspace>/docs/SSOT_KOBII_DISTILLER.md` → `## v230000.1 — Owner Ratification`).

The Owner ratified **Opt D Hybrid Kernel-Only** as the canonical architecture
name after two parallel sessions arrived independently at the same role split
under different vocabularies ("Hybrid Kernel-Only" / "roles-not-duplicates
DNA-11000 Rule-097"). The "Engine NEVER moves" invariant is **fully
compatible** with Opt D — engine stays in workspace, kernel-contract lives
here. No real conflict ever existed.

### Cert evidence (verified 2026-05-15, system Python 3.12.10)

| Gate | Result |
|---|---|
| `pip show kpp-distiller-kernel` | 0.1.0 editable at THIS repo `kpp-distiller-kernel/` |
| `pip show kobicraft-content-intelligence` | 0.1.0 editable at workspace `kobicraft_content_intelligence/` |
| Workspace `python scripts/check_kernel_drift.py` | **18/18 identities verified, 5 shims ≤ 60 lines** |
| Workspace `python -m pytest distiller/tests/ -v` | **12/12 passed** |
| Workspace `python scripts/e2e_distiller_golden_run.py` | **8/8 boundary contracts PASS** |

### Sealed commits

| Repo | Branch | Anchor commits |
|---|---|---|
| Power Pack (this) | `kdos/lazarus-v3-live-intelligence` | `e9b91f3` → `24b9028` → `8db600e` |
| Workspace | `kdos/v1.2-tandas-partes-fix` | `1f3315a` → `d5ba0f6` → `f1dd874` → `b505261` → `a0e2355` |

### Reconciliation vaccine

The false-collision episode is captured as 2-part vaccine
**VAC-ARCH-230000.1** in `vault/knowledge_base/governance_vaccines.md`.
Lesson: at session start, run `git fetch origin && git status` + read **full**
SSOT manifest content (not just headings/invariant titles) before declaring
any cross-repo architectural conflict.

---

(More SSOT entries can be appended here as additional cross-repo subsystems
are inscribed. One table per subsystem; identical invariants apply.)
