# Governance Overlay — Pre-Task Gate

> Loaded for STANDARD, DEEP, and FORENSIC tiers. ~150 tokens.

## 1. CLASSIFY Complexity

Before writing any code:
- Count files that will be created or modified
- Identify cross-module dependencies (does change A require change B?)
- Check if this touches shared utilities, types, or config

## 2. LOAD Project Governance

Check and read (if they exist):
- `/governance/domain/PROJECT_DOMAIN_RULES.md` — project-specific constraints
- `/governance/domain/PROJECT_DATA_MODEL.md` — data entities and relationships
- `CLAUDE.md` — project-level behavioral rules
- Domain rules can ONLY add restrictions — they never weaken universal rules

Authority hierarchy: **CONSTITUTION (00-03) > GOVERNANCE (04-09) > OPERATIONAL (10-19) > DOMAIN (PROJECT_*)**

## 3. IDENTIFY Existing Patterns

Before creating anything new:
- Grep for existing implementations of similar functionality — **never rebuild what exists** (Mistake #9)
- Verify no duplicate file/module exists with similar name
- Map the call chain UPWARD from the entry point — understand who calls what before modifying (Mistake #14)
- Check for established naming conventions, file organization patterns

## 4. SET Verification Scope

Determine for this specific project:
- Which quality gates apply? (TypeScript? Python? Both?)
- What test framework is configured? (`jest`, `pytest`, `vitest`?)
- What linter runs? (`eslint`, `ruff`, `mypy`?)
- What's the commit convention?
- Are there pre-commit hooks?
