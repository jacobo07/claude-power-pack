# CPP Setup OS -- superior-to-official setup intelligence (SCS C40)

## SCS C40 -- CPP-Setup-OS: EXECUTE, don't just recommend (sealed 2026-06-07, BL-SETUP-OS-001)

**Standard.** A scanned repo yields profile -> ROI-ranked recommendations
-> a secure dry-run install plan with rollback. The official
`claude-code-setup` plugin only *recommends*; the PP Setup OS adds risk,
ROI, cost, secret-risk, rollback, validation, install-mode and a
"when-NOT-to-install" per recommendation, and it can EXECUTE safely.
Universal: free-text + stdlib, works in any repo.

**What shipped (Sprint 3, `tools/test_setup_os.py` 8/8 x 3 hermetic):**
- `modules/setup_os/scanner.py` (Pillar 1, `/scan-repo`) -- read-only
  ProjectProfile; every field carries a detection SOURCE
  (detected_from_file/config/command / inferred_from_structure / missing
  / unknown), so an inference is never a fact (dataset sec. 7.3).
- `modules/setup_os/roi_analyzer.py` (Pillar 2, `/analyze-roi`) -- ROI =
  impact/effort risk-damped; Secret Firewall pinned first; every rec has
  a "when NOT to install" (anti-over-recommendation, sec. 27).
- `modules/setup_os/secure_installer.py` (Pillar 4, `/setup-repo`) --
  DRY-RUN ONLY. Secret scan first -> CRITICAL hit blocks the plan (no raw
  value surfaced, HR-SECRET-002); every step ships a rollback; owner-side
  (global config) steps are never auto-applied (HR-001). `--apply` is
  refused by design (dry-run-first, sec. 13).
- `vault/knowledge_base/setup_os/` -- 4 PARTE files + MASTER + ROADMAP
  (pillars 1/2/4 built; 3/6/7 composed from existing PP modules; 5/8/9/10
  on the roadmap -- no silent caps).

**Method (lessons carried).** C28 (read source first -- built scanner to
the dataset's 35-field PROJECT_PROFILE + reality rule, not a guess).
Compose-don't-duplicate (Secret Firewall, Output Contracts, Backlog,
One-Shot already exist -- the installer/ROI compose them rather than
rebuild). Reality Contract (the installer NEVER auto-applies; dry-run +
rollback + Owner approval for global config).

Cross-ref C28 (read source / compose existing), C39 (SDD-OS -- the setup
recommendations are themselves tier-classifiable), HR-001 (Owner-side
global config), HR-SECRET-* (firewall-before-install).

Sealed BL-SETUP-OS-001 2026-06-07.
