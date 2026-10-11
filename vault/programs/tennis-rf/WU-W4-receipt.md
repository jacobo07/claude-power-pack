# W4 receipt

Status: DONE

**Disposition: REJECT for native PowerPC evidence.** REA 6.3.0 refuses both targets with a named
constraint, so no function-list, pseudocode or xref queries were run. Zero GEX44 jobs.

The worker (m-db420d46a3be, renewal of residual m-97b7d2e0db58) committed the work but wrote no
receipt. The coordinator filed this one after reading the refusal outputs.

- **Commit:** `9c15b44f` (claude-power-pack, feature/knowledge-acquisition).
- **Disposition file:** `vault/programs/tennis-rf/REA-DISPOSITION.md`. It holds the per-capability
  table, the pinning record, and an upstream issue text for a PowerPC big-endian / DOL lane
  (drafted, not filed).
- **Evidence:** `vault/programs/tennis-rf/evidence/rea/`.
  - `inspdol.out`: `target_unavailable`, "unsupported binary format" (SportsPackEP.dol).
  - `inspo.out`: `target_unavailable`, "unsupported ELF architecture" (DTK split
    auto_03_800071C0_text.o).
- **Ghidra 12.1.2:** REA accepted it as compatible 12.1.x. The provider is still unavailable,
  because `JAVA_HOME` is JDK 17 and REA needs 21+. The refusal comes earlier, in format detection,
  so this does not change the result.
- **Install:** `C:\Users\User\Apps\rea-6.3.0` was removed because REA is rejected and unused.
  Nothing was installed globally. The global npm is broken (`minipass-sized`); the failure is in
  `evidence/rea/npm-install-fail.log`.
