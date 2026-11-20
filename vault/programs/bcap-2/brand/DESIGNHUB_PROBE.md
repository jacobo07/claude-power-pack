# BI-27 DesignHub probe (read-only inventory, partial)

Source: github.com/yakew7/DesignHub @ 148e8c3ffa8ea82801b3cfb16ef91b4ca515d285 (the pin in the backlog). GitHub SPDX MIT, not archived. Git tree read 2026-11-20: 907 paths, not truncated.

## Inventory (paths only; no source file was read)
Next.js local-first studio. Relevant modules by blob count: lib/social 58, lib/svg 36, lib/mockups 24, lib/guidelines 24, lib/color 24, lib/brand 17, lib/brand-dna 12, lib/logo 9, packages/cli 12. Pages cover brand, brand-dna, logo, mockups, guidelines, export, accessibility.

## Decision (reasoned, not measured)
- Overlap with CCF: brand-dna, logo, mockups, guidelines and export map onto CCF Visual DNA, concept generation, BI-23 preview contexts and BI-26 release manifest. DesignHub is an application, so forking it would create the competing logo studio the backlog forbids.
- Candidates for technique comparison only: lib/mockups (context catalogue for BI-23) and lib/guidelines (brand-book structure for BI-24). Nothing was read, so no technique is claimed or ported.
- Licence is repo-level MIT; per-file headers, vendored assets and font/image licences in mockups were not checked, so code admission stays refused until that scan.

## Not done (BI-27 stays open)
No source read, no technique comparison, no measured benefit. Next unit: read lib/mockups and lib/guidelines index files, scan headers, compare against modules/ccf/brand_release.py context list.
