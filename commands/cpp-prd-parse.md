---
description: Parse a raw-text PRD into a deterministic PRD_BASELINE.json + BLUEPRINT.md before /ultra Q&A. Usage: /cpp-prd-parse <file|inline text>
---

# /cpp-prd-parse — KARIMO PRD Ingestion

Arguments: $ARGUMENTS

## Behavior

The argument is either a path to a PRD file or inline PRD text.

1. If `$ARGUMENTS` is empty, ask the Owner for a PRD path or inline text and STOP.
2. Resolve the parser:
   `python ~/.claude/skills/claude-power-pack/modules/karimo-harness/prd_parser.py`
3. If the argument is an existing file path, run with `--in <path>`.
   Otherwise pass the literal text with `--text "<...>"`.
4. Default outputs (override with `--out` / `--blueprint`):
   - `PRD_BASELINE.json` in the current working directory (source of truth)
   - `BLUEPRINT.md` alongside it (pure derivation of the baseline)
5. Echo `content_sha256` and the BLUEPRINT's "Implementation Seed Tasks"
   section so the Owner sees the extracted plan seed before Q&A.

## Contract

- The parser performs NO LLM calls — pure regex/heuristic state machine,
  fully deterministic. Identical input → identical `content_sha256`.
- `BLUEPRINT.md` is a pure function of `PRD_BASELINE.json`; never edit the
  blueprint by hand — regenerate from the baseline.
- Self-test any time with:
  `python …/prd_parser.py --in <prd> --check` (exit 0 = deterministic +
  pure-blueprint + schema-valid).

## Relationship to /ultra

`/ultra plan <target>` Phase 1 auto-invokes this parser when the target
spec contains a raw PRD (header `PRD:` or a `<prd>` block). The emitted
`BLUEPRINT.md` seeds the Phase 3 task list; the Q&A Pass still runs.
