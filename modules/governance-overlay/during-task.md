# Governance Overlay — During-Task Verification

> Loaded for DEEP and FORENSIC tiers. ~200 tokens. Checked after EACH file created or modified.

## Per-File Checks

After creating or modifying each file, verify:

### Wiring Check (Mistakes #1, #2, #6)
- **New file** → grep codebase for at least one import/require of this file
- **New export** → verify at least one call site exists
- **If no consumer found** → STOP and wire it before continuing to the next file
- A file without a consumer is not "done" — it's dead code

### Integration Check (Mistakes #4, #5, #7)
- **New event/listener** → verify the corresponding emit/dispatch call exists
- **New config getter** → verify something reads the value
- **Replacement/upgrade** → verify ALL old call sites have been updated (not just the first one found)
- Use `grep -r "old_function_name"` to find remaining references

### Data Flow Check (Mistakes #3, #15)
- **New state/data** → verify save/persist exists in the completion path
- **New counter/metric** → verify it tracks REAL state, not just the initial value
- A counter initialized to `items.length` that never updates is Mistake #15

### Pattern Check (Mistakes #8, #9)
- **Changed geometry/layout constants** → verify dependent ratios are still correct
- **About to build a utility** → grep first — does this utility already exist?
- **Using deprecated API** → check for the modern equivalent
