# PART F — FRONTEND/DESIGN LIEUTENANT (BL-0029)

The Power-Pack acts as **lieutenant** for 6 absorbed frontend/design skills. By default the user invokes only `claude-power-pack`; this part wakes when frontend/design triggers fire and dispatches to the right specialist.

**Trigger:** React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui, HTML, CSS, frontend, UI, UX, design, component, page, dashboard, landing page, brand, color palette, typography, font, layout, animation, accessibility, poster, artwork, canvas, SaaS UI, vibe coding.

---

## Decision Matrix — Which Skill For Which Task

| Task | Primary skill | Why this one wins |
|---|---|---|
| Build a React/HTML artifact (chat-window, dashboard tile, complex component) | `artifacts-builder` | Specializes in shadcn/ui-driven artifacts. Read `vendor/skills/artifacts-builder/instructions.md` before invoking via Skill tool. |
| Frontend with **distinctive aesthetics** (avoid AI-slop look) | `frontend-design` | Cite-or-die anti-generic aesthetic discipline. Plugin already enabled. |
| Apply Anthropic brand colors / typography to artifacts | `brand-guidelines` | Anthropic-published canonical brand kit. |
| Visual art, posters, PNG/PDF design, font-rich compositions | `canvas-design` | Bundles 20+ free-use fonts (`vendor/skills/canvas-design/canvas-fonts/`). |
| Full SaaS product end-to-end (frontend + backend + monetization) | `building-ai-saas-products` | Has dataset_registry, governance, intelligence/, knowledge/ pre-baked. |
| Pick a style + palette + font pairing + accessibility ruleset | `ui-ux-pro-max` | 50 styles × 21 palettes × 50 font pairings × 9 stacks. Plugin enabled. |
| Component search + ready-made shadcn snippets via MCP | 21st.dev `@21st-dev/magic` | Real-time component generation, **requires API key** (see Setup below). |
| Lint/diff/export `DESIGN.md` (Google Labs design-system spec) | `/cpp-design-md` | Already bundled at `commands/design-md.md`. |

---

## Best-Of-Each — Distilled Default Patterns

When the lieutenant fires and no specific skill has been invoked yet, apply these defaults inline. They are the highest-leverage rules from each absorbed skill.

### From `frontend-design` (anti-AI-slop discipline)
1. **Pick an extreme aesthetic before writing CSS** — brutalist, editorial, retro-futuristic, organic, art-deco, etc. Refuse the "Inter-on-white" middle ground.
2. **Reject the AI-generic palette**: NO purple-gradient-on-white, NO Inter/Roboto/Arial, NO Space Grotesk default.
3. **One well-orchestrated page-load animation > scattered micro-interactions.** Stagger reveals via `animation-delay`.
4. **Match implementation complexity to vision**: maximalist needs elaborate code; minimalism needs precision and restraint.

### From `ui-ux-pro-max` (priority-ordered rule pyramid)
Apply these in priority order; do NOT skip CRITICAL even for prototypes:
1. **CRITICAL Accessibility**: contrast ≥4.5:1, focus rings on interactive elements, aria-label for icon buttons, label/for on form inputs.
2. **CRITICAL Touch**: 44×44 px minimum touch targets, disable buttons during async, cursor-pointer on clickables.
3. **HIGH Performance**: WebP + srcset + lazy loading, respect `prefers-reduced-motion`, reserve space for async content (no CLS).
4. **HIGH Layout**: `width=device-width, initial-scale=1`, ≥16px body on mobile, define z-index scale (10/20/30/50), no horizontal scroll.
5. **MEDIUM Typography**: line-height 1.5–1.75 body, line-length 65–75ch, pair display + body fonts intentionally.
6. **MEDIUM Animation**: 150–300ms for micro-interactions, animate `transform`/`opacity` only.

### From `brand-guidelines` (when "Anthropic" mentioned)
Read `vendor/skills/brand-guidelines/instructions.md` for the canonical color hex codes + typography system. Default whenever the work is for/about Anthropic itself.

### From `canvas-design` (visual-art tasks)
Use the bundled fonts under `vendor/skills/canvas-design/canvas-fonts/` — they're OFL-licensed and pre-staged. Pair distinctive display fonts (Tektur, Silkscreen, YoungSerif) with refined body fonts (WorkSans, RedHatMono, SmoochSans). Skip Google Fonts CDN for offline work.

### From `artifacts-builder` (React/HTML artifact tasks)
Read `vendor/skills/artifacts-builder/instructions.md` first; it specifies the shadcn/ui import pattern + accepted component subset for Claude-rendered artifacts.

### From `building-ai-saas-products` (full SaaS scaffolds)
For full SaaS work, read `vendor/skills/building-ai-saas-products/intelligence/aisaas/Agent_Registry_AISAAS.md` and `Dataset_Doctrine_AISAAS.md` before scaffolding.

---

## Default Workflow (no specific skill named)

```
User says: "build me a [frontend thing]"
  ├─ Lieutenant fires (this part loads)
  ├─ Step 1 — pick an aesthetic via frontend-design discipline
  ├─ Step 2 — apply ui-ux-pro-max CRITICAL accessibility + touch rules
  ├─ Step 3 — for components: prefer 21st.dev MCP if API key present,
  │           else use artifacts-builder shadcn pattern
  ├─ Step 4 — verify implementation complexity matches vision
  └─ Step 5 — return to dormant
```

---

## 21st.dev MCP Setup (one-time, user action)

The lieutenant CAN call `@21st-dev/magic` MCP for component generation IF configured. Setup is **user-initiated** (BL-0028: scope-escalation guard prevents hooks from auto-writing API keys):

```bash
# After signing up at https://21st.dev/magic/console for an API key:
npx @21st-dev/cli@latest install cursor --api-key <YOUR_KEY>
```

OR manually edit `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "@21st-dev/magic": {
      "command": "npx",
      "args": ["-y", "@21st-dev/magic@latest"],
      "env": { "API_KEY": "<YOUR_KEY>" }
    }
  }
}
```

Tools exposed (after setup): `21st_magic_component_builder`, `21st_magic_component_inspiration`, `21st_magic_component_refiner`, `logo_search`. When present, prefer these over manual CSS scaffolding for stock components.

---

## Return to Dormant

After the frontend/design task ships, this part returns to sleep. The next session reloads it on demand based on triggers. Do NOT keep this loaded across unrelated tasks (token discipline per BL-0017 / OmniRAM-Sentinel doctrine).
