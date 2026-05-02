# NOTICE — Third-party attribution

This file is the rolling attribution log for any third-party software the Power-Pack adapts, wraps, or bundles. New entries are appended; existing entries are never edited (the upstream's license terms are immutable record).

## Format per entry

```
### <upstream name> — <SPDX license id>

- **Source:**    <git URL or homepage>
- **Snapshot:**  <commit hash or "not bundled, called via $PATH">
- **Adapter:**   lib/adapters/<file>.js
- **Added:**     <YYYY-MM-DD>
- **Gate verdict:** PERMISSIVE | WEAK_COPYLEFT | STRONG_COPYLEFT | PROPRIETARY | UNKNOWN
- **Obligation summary:** <one-line summary of what the human took on by adopting this>
```

## Entries

### auto-browser — MIT

- **Source:**    https://github.com/LvcidPsyche/auto-browser
- **Snapshot:**  not bundled, called via loopback HTTP on `127.0.0.1:8000` (REST + MCP) and `127.0.0.1:6080` (noVNC); pinned to release tag `v1.0.2` (published 2026-04-26)
- **Adapter:**   lib/adapters/auto_browser.js
- **Added:**     2026-04-27
- **Gate verdict:** PERMISSIVE
- **Obligation summary:** preserve upstream LICENSE in user's local clone (vendor/auto-browser/INSTALL.md instructs `git clone`); attribution in this NOTICE; no source redistribution from Power Pack repo. Empirical verification: `gh repo view LvcidPsyche/auto-browser` returned MCP-native browser control plane with reusable auth profiles, noVNC takeover, audit trails, and compliance templates (HIPAA/PCI-DSS/SOC2/GDPR).

### artifacts-builder — see `vendor/skills/artifacts-builder/LICENSE.txt`

- **Source:**    Anthropic-published skill (originally installed at `~/.claude/skills/artifacts-builder/`)
- **Snapshot:**  vendored 2026-05-02; SKILL.md.disabled re-activated as SKILL.md in vendor and source
- **Adapter:**   none (invoked directly via Skill tool: `Skill('artifacts-builder')`)
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE (see bundled LICENSE.txt for terms)
- **Obligation summary:** preserve upstream LICENSE.txt in vendored copy; do not redistribute beyond this Power Pack repo without checking upstream terms.

### brand-guidelines — see `vendor/skills/brand-guidelines/LICENSE.txt`

- **Source:**    Anthropic-published skill (originally installed at `~/.claude/skills/brand-guidelines/`)
- **Snapshot:**  vendored 2026-05-02; SKILL.md.disabled re-activated as SKILL.md
- **Adapter:**   none (invoked via Skill tool)
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE
- **Obligation summary:** apply Anthropic brand colors/typography; preserve LICENSE.txt.

### canvas-design — see `vendor/skills/canvas-design/LICENSE.txt`

- **Source:**    Anthropic-published skill (originally installed at `~/.claude/skills/canvas-design/`)
- **Snapshot:**  vendored 2026-05-02; SKILL.md.disabled re-activated as SKILL.md. NOTE: 5.6 MB due to bundled `canvas-fonts/` directory.
- **Adapter:**   none (invoked via Skill tool)
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE
- **Obligation summary:** preserve LICENSE.txt + font license terms within `canvas-fonts/`.

### building-ai-saas-products — see `vendor/skills/building-ai-saas-products/LICENSE.txt`

- **Source:**    Anthropic-published skill (originally installed at `~/.claude/skills/building-ai-saas-products/`)
- **Snapshot:**  vendored 2026-05-02; SKILL.md.disabled re-activated. Stripped redundant SKILL.zip + SKILL.md.backup from vendored copy (loose files preserved).
- **Adapter:**   none (invoked via Skill tool)
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE
- **Obligation summary:** preserve LICENSE.txt + bundled `governance/`, `intelligence/`, `knowledge/` payloads.

### frontend-design — `claude-plugins-official` marketplace

- **Source:**    Anthropic-published plugin: `frontend-design@claude-plugins-official` (cached at `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/frontend-design/`)
- **Snapshot:**  vendored 2026-05-02 (8 KB, SKILL.md only)
- **Adapter:**   none (active via plugin enable in `~/.claude/settings.json`)
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE (Anthropic plugins-official marketplace terms)
- **Obligation summary:** vendored copy is archival; runtime activation continues via plugin marketplace.

### ui-ux-pro-max — `ui-ux-pro-max-skill` marketplace

- **Source:**    Plugin: `ui-ux-pro-max@ui-ux-pro-max-skill` v2.0.1 (cached at `~/.claude/plugins/cache/ui-ux-pro-max-skill/ui-ux-pro-max/2.0.1/`)
- **Snapshot:**  vendored 2026-05-02 (18 KB, includes `data/` and `scripts/` subdirs)
- **Adapter:**   none (active via plugin enable). Recommends shadcn/ui MCP integration via `@21st-dev/magic` — config STAGED but NOT applied (awaiting user authorization, see BL-0028).
- **Added:**     2026-05-02 (BL-0027)
- **Gate verdict:** UPSTREAM_LICENSE
- **Obligation summary:** vendored copy is archival; runtime activation continues via plugin marketplace.
