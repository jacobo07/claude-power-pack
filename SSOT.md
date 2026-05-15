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
| **Contract** (22-section sealing schema v1.2) | THIS repo | `tools/distiller/schema.json` | Sovereign Sealing v1.2 (6696 B) |
| **Trigger** (operational shim: `ingest` + `check` subcommands; delegates the LLM step to the running Claude Code agent against `parts/sleepy/distiller.md`) | THIS repo | `tools/distiller/run.py` | Phase D dispatcher |
| **Validator** (22-section gate) | THIS repo | `tools/distiller/validate.py` | enforced by the trigger |
| **Sleepy skill module** | THIS repo | `modules/distiller/` (`config.json`, `core.md`, `README.md`) | Skill metadata |
| **Engine** (2730 LOC: orchestrator / data_contracts / emitter / kernel / ingestor / CLI) | KobiiCraft workspace repo | `<workspace>/kobicraft_content_intelligence/distiller/` | KobiiDistillerOS v220000, commit `f3f4bc3` |

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
python -m pip install -e <workspace>/kobicraft_content_intelligence
python -c "from kobicraft_content_intelligence.distiller.core import orchestrator"
```

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
  `C:\Users\User\Desktop\Cursor Projects\Minecraft Projects\KobiiCraft Workspace\KobiiCraft Core Files\docs\SSOT_KOBII_DISTILLER.md`)
- **DNA-11000 Rule-097** lives in
  `<workspace>/docs/KOBII_PHILOSOPHY/STANDARDS.md`.

---

(More SSOT entries can be appended here as additional cross-repo subsystems
are inscribed. One table per subsystem; identical invariants apply.)
