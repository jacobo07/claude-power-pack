# NOTICE — Third-party attribution

This file is the rolling attribution log for any third-party software the Power-Pack adapts, wraps, or bundles. New entries are appended; existing entries are never edited (the upstream's license terms are immutable record).

## Format per entry

```
### <upstream name> — <SPDX license id>

- **Source:**    <git URL or homepage>
- **Snapshot:**  <commit hash or "not bundled, called via $PATH">
- **Adapter:**   lib/adapters/<file>.js
- **Added:**     <YYYY-MM-DD>
- **Gate verdict:** PERMISSIVE | WEAK_COPYLEFT | STRONG_COPYLEFT |
                    SOURCE_AVAILABLE_RESTRICTED | PROPRIETARY | UNKNOWN
- **Redistribution:** allowed | conditional | prohibited | unknown
- **Integration mode:** fork | adapter | gateway | passthrough | metadata-only
- **License file:** <exact filename inspected — LICENSE vs LICENSE.md is load-bearing>
- **Fingerprint:** <sha256 from license_gate.js; drift invalidates every derived artifact>
- **Confidence:** VERIFIED (full text read) | OBSERVED (badge/metadata only) | UNKNOWN
- **Exit plan:**  <how this dependency is removed if terms change>
- **Obligation summary:** <one-line summary of what the human took on by adopting this>
```

### Why `Redistribution` is a separate field

The SPDX id is not sufficient to decide whether something may ship in a distributed
registry. `react-bits` is honestly described as MIT and may not be redistributed. Any
installer or registry emitter branches on **`Redistribution`**, never on the license
name. Produce these fields with:

```
node lib/license_gate.js <path> --json                 # full verdict
node lib/license_gate.js <path> --strict               # exit 5 if prohibited
node lib/license_gate.js <path> --expect <fingerprint> # exit 4 on license drift
```

Entries are append-only. A license that **changes** gets a NEW dated entry recording the
drift — the superseded entry stays, because artifacts derived under the old terms were
derived under the old terms.

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

---

## CDICF upstreams — legal verdicts recorded 2026-08-06

Recorded at **audit time, before any clone**. Nothing below is bundled yet.

**Commits are pinned** (2026-08-06, GitHub API, authoritative). **Copyright holders and
canonicality are resolved** — every row is now VERIFIED from license *text*, never a badge.

**Fingerprints are deliberately withheld as `PENDING_CLONE`, with one labelled
exception.** The license bodies reaching this session pass through a markdown conversion
that can reflow whitespace. A sha256 of reflowed text would look authoritative, would not
match the repository bytes, and would fire `--expect` on the first real drift check —
manufacturing exactly the confident-but-wrong verdict this gate was hardened to stop.
A fingerprint is therefore measured at clone time against the pinned commit, or not at
all. The react-bits value is retained because it was already published in commit
`998d52c`; it keeps its "as fetched" label and is not to be used for drift until
re-measured.

### react-bits — MIT + Commons Clause Restriction v1.0

- **Source:**    https://github.com/DavidHDev/react-bits
- **Snapshot:**  `1320d40a8318ac7d4fe6690c7206ceda8cdd59bd` (branch `main`, committed
  2026-08-04T17:41:18Z; pinned 2026-08-06). No clone performed yet.
- **Adapter:**   planned — CPP Motion Gateway (install-from-upstream, zero copied files)
- **Added:**     2026-08-06
- **Gate verdict:** SOURCE_AVAILABLE_RESTRICTED
- **Redistribution:** **prohibited**
- **Integration mode:** gateway
- **License file:** `LICENSE.md` — plain `LICENSE` returns HTTP 404 on `main`
- **Fingerprint:** `f4cfa83966e6492054d3156cf70d3cf000b8f0a4d868517818963ec2ad1e9991`
  (sha256 of the license text **as fetched 2026-08-06**, not of a cloned working tree;
  re-measure against the pinned commit before relying on it for drift detection)
- **Confidence:** VERIFIED — full text read; GitHub badge string "MIT + Commons Clause"
- **Exit plan:**  Gateway only, so removal is deleting the adapter and the metadata rows;
  no CPP artifact embeds its code, so no consumer is broken by removal.
- **Obligation summary:** Copyright (c) 2026 David Haz. Usable inside a consuming
  application including commercially. MUST NOT be sold, sublicensed or redistributed
  "alone, in a bundle, or as a ported version" — porting and renaming are explicitly
  covered. It therefore MUST NOT enter the CPP registry in either the internal or the
  public distribution path (Owner decision, 2026-08-06). Provenance must never be stripped.

### shadcn/ui — MIT

- **Source:**    https://github.com/shadcn-ui/ui
- **Snapshot:**  `9846e22ce52c723554742860a0dbd3e5cf19b573` (branch `main`, committed
  2026-08-06T11:36:01Z; pinned 2026-08-06). No clone performed yet.
- **Adapter:**   planned — CPP Primitives namespace (registry protocol + primitives)
- **Added:**     2026-08-06
- **Gate verdict:** PERMISSIVE
- **Redistribution:** allowed
- **Integration mode:** fork
- **License file:** `LICENSE.md`
- **Fingerprint:** PENDING_CLONE — measure at the pinned commit (see section preamble).
- **Confidence:** VERIFIED — full license text read; holder taken from the text
- **Exit plan:**  Registry protocol is a format, not a runtime dependency; a fork can be
  frozen in place without upstream availability.
- **Obligation summary:** Copyright (c) 2023 **shadcn**. Preserve copyright + license text
  on redistribution. No appended clause.

### assistant-ui — MIT

- **Source:**    https://github.com/assistant-ui/assistant-ui
- **Snapshot:**  `bd4c0ad3d41a65d0a2caea921f82c6502011615a` (branch `main`, committed
  2026-08-06T12:33:03Z; pinned 2026-08-06). No clone performed yet.
- **Adapter:**   planned — CPP AI Interfaces namespace
- **Added:**     2026-08-06
- **Gate verdict:** PERMISSIVE
- **Redistribution:** allowed
- **Integration mode:** fork
- **License file:** `LICENSE`
- **Fingerprint:** PENDING_CLONE — measure at the pinned commit (see section preamble).
- **Confidence:** VERIFIED — full license text read; holder taken from the text
- **Exit plan:**  Runtime/adapter boundary is the upstream's own extension point; a
  replacement runtime can be substituted without touching component code.
- **Obligation summary:** Copyright (c) 2025 **AgentbaseAI Inc.** — the holder is the
  company, not the project name; attribution must name AgentbaseAI Inc.

### tailark/blocks — MIT

- **Source:**    https://github.com/tailark/blocks
- **Snapshot:**  `8139698115c1341bfd2e3e286c04bb4d8146f472` (branch `main`, committed
  2026-07-29T11:14:59Z; pinned 2026-08-06). No clone performed yet.
- **Adapter:**   planned — CPP Marketing namespace
- **Added:**     2026-08-06
- **Gate verdict:** PERMISSIVE
- **Redistribution:** allowed
- **Integration mode:** fork
- **License file:** `LICENCE.md` — **British spelling.** `LICENSE` and `LICENSE.md` both
  return HTTP 404 on `main`; only `LICENCE.md` exists. A probe for `LICENSE*` finds nothing.
- **Fingerprint:** PENDING_CLONE — measure at the pinned commit (see section preamble).
- **Confidence:** **VERIFIED (resolved 2026-08-06)** — full license text read from
  `LICENCE.md`. The earlier OBSERVED status came from a badge; the badge does not carry a
  holder, which is why it could not settle this row.
- **Exit plan:**  Blocks are copied source under a shadcn registry; once installed they
  carry no runtime dependency on the upstream.
- **Obligation summary:** Copyright (c) 2025 **Irung**. Preserve copyright + license text
  on redistribution. No appended clause. Distributed via shadcn registry
  (`@tailark-oss` namespace, Base UI and Radix variants).

### driver.js — MIT

- **Source:**    https://github.com/nilbuild/driver.js
- **Snapshot:**  `010fb13fe062d103bcdd2711be910d50a8383b61` (branch **`master`**, committed
  2026-07-18T16:01:04Z; pinned 2026-08-06). Note the default branch is `master`, not
  `main`. No clone performed yet.
- **Adapter:**   planned — CPP Onboarding namespace
- **Added:**     2026-08-06
- **Gate verdict:** PERMISSIVE
- **Redistribution:** allowed
- **Integration mode:** fork
- **License file:** **`license`** — lowercase, no extension. On a case-sensitive
  filesystem an exact-name probe for `LICENSE` misses it entirely; this upstream is what
  exposed that defect in `license_gate.js` (fixed 2026-08-06, `findLicenseFiles`).
- **Fingerprint:** PENDING_CLONE — measure at the pinned commit (see section preamble).
- **Confidence:** **VERIFIED (resolved 2026-08-06)** — canonicality settled by GitHub API.
  `api.github.com/repos/nilbuild/driver.js` and `api.github.com/repos/kamranahmedse/driver.js`
  return the **identical object**: `full_name: nilbuild/driver.js`, `fork: false`, no
  `parent`, no `source`, `created_at: 2018-03-11T19:52:13Z`, 26,544 stars. That is a
  transparent **rename redirect**, not a fork — one repository, one holder, no divergent
  copyright. Canonical path is `nilbuild/driver.js`; `kamranahmedse/driver.js` is a legacy
  alias that resolves to it.
- **Exit plan:**  Dependency-free TypeScript; the tour layer is optional by governance
  ("a tour must not compensate for bad UX"), so removal degrades nothing structural.
- **Obligation summary:** Copyright (c) **Kamran Ahmed** — the license states no year.
  Reproduce the notice verbatim including the absent year; do not supply one. No appended
  clause.
