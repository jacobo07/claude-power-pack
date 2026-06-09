# T-PATH-HARDCODE-001 — hardcoded repo-root paths break cross-host/cross-repo

**Sealed:** 2026-06-09 (BL-PATH-AUDIT-001). Triggered by Owner question
"¿Cursor Projects o Repos-Github?" — a suspicion that the PP assumed the
wrong repo root.

## The trap

A PP tool hardcodes an absolute repo-root path — wrong *user*, wrong
*root*, or both. It works on the authoring host (or never, if the user
prefix is stale) and is dead everywhere else. Worst form: a default
`argparse` value, because it activates silently with zero CLI args.

## What the 2026-06-09 audit found

The Owner's premise (systemic Cursor-Projects-vs-Repos-Github mismatch)
was **DISPROVEN**. Every operational surface was already correct:

- **setup_os profiles (3/3):** `repo_path.value` exists on disk —
  `Desktop\Cursor Projects\{CostaLuz Lawyers, Minecraft Projects\KobiiCraft
  Workspace\KobiiCraft Core Files}`, `Apps\whisprflow-apk`.
- **session_snapshot.json:** all 9 panes / 3 unique cwds exist
  (KobiiCraft Core Files, claude-power-pack, GEO-audit).
- **tasks.json:** all in real `Cursor Projects\*\.vscode\`.
- **restore_panes.ps1:** dynamic (`$HOME`-based, reads absolute snapshot
  cwds) — no hardcoded root.
- **scanners** (`dataset_enricher`, `chatgpt_distiller`, token-optimizer
  trio): all dynamic `Path.home()/"Desktop"/"Cursor Projects"`.

**The one real defect:** `tools/topology_apply.py` `--search-roots`
default was `["C:/Users/kobig/Desktop/Repos-GitHub", "C:/Users/kobig",
"C:/Users/kobig/Documents"]` — wrong user (`kobig`, the VPS account; this
host is `User`, `C:\Users\kobig` does not exist) AND wrong root
(`Repos-GitHub`, which holds only knowledge-vault clones, not active dev
repos). The tool is **ORPHAN** (no callers — only its own allowlist row
in `normalize_paths.py`), so the bug was latent, zero blast radius.

## The answer

**Cursor Projects.** `C:\Users\User\Desktop\Cursor Projects\` is the
Owner's active dev-repo root (+ `Apps\` for tooling repos like
whisprflow-apk / mcp-video-analyzer). `Repos-GitHub` is reference vaults
only.

## Fix (dynamic always)

- `topology_apply.py`: default search-roots →
  `str(Path.home()/"Desktop"/"Cursor Projects")`, `…/"Apps"`,
  `str(Path.home())`.
- `sovereign_miner.py`: the whole `C:\Users\User\…` constant block →
  `os.path.join(os.path.expanduser("~"), …)` (roots unchanged, now
  host-portable).

## Recognizer

Grep PP `*.{py,js,ps1}` for `Repos-Git`, `C:/Users/`, `C:\Users\`,
`Desktop\\`. A literal user prefix or `Repos-GitHub` repo-root in code
(not a host-config constant that is genuinely host-specific) is the trap.
Prefer `Path.home()` / `os.path.expanduser("~")`. **Audit the premise of
a path-mismatch report before mass-migrating — the mismatch is usually
narrower than feared** (here: 1 orphan default, not a systemic problem).
Sister of `feedback_audit_disproves_owner_premise`.
