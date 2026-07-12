# DESIGN BASELINE AUDIT — 2026-07-12

Fase 0 (bloqueante) de la absorción `awesome-claude-design`. Evidencia empírica,
no inventario asumido. Aplica `feedback_reality_scan_before_corpus_build`: el
inventario propuesto por un plan es una HIPÓTESIS hasta verificarlo contra disco.

**Veredicto: 3 de los 5 sprints del plan proponen construir algo que YA EXISTE en
el PP, en forma más madura. El gap real es más estrecho y más profundo.**

---

## 1. Qué tiene el PP hoy para diseño

### 1.1 Skill de diseño (capa generativa, prosa)
- `~/.claude/skills/frontend-design/SKILL.md` — 43 líneas, licencia Anthropic
  (`LICENSE.txt` adyacente). **NO vive en el repo PP**: vive sólo bajo `~/.claude/`.
  Contiene el Anti-Slop en prosa (línea 36): prohíbe Inter/Roboto/Arial/system
  fonts, gradientes morados sobre blanco, layouts predecibles, componentes
  cookie-cutter. **No tiene**: familias estéticas nombradas, decision tree,
  remix recipes.
- Restricción dura: editarlo = escritura bajo `~/.claude/` → **HR-001**
  (el clasificador bloquea escrituras a config global del agente en auto-mode),
  y además es código vendorizado de terceros con licencia propia.

### 1.2 Doctrina de calidad web (capa normativa, prosa) — PP-owned
- `rules/web/design-quality.md` (ECC, MIT) — Anti-Template Policy: 8 patrones
  prohibidos, 10 cualidades requeridas (mínimo 4 por superficie), y **9
  "worthwhile style directions"**: Editorial/magazine, Neo-brutalism,
  Glassmorphism con profundidad real, Dark/light luxury, Bento, Scrollytelling,
  3D integration, Swiss/International, Retro-futurism.
- Esto es lo más cercano a "9 familias estéticas" que ya existe. **Pero**: sin
  swatch, sin tipo, sin cuándo-usarla, sin decision tree, sin arbitraje de tokens.
  Es una lista de nombres, no un vocabulario operable.

### 1.3 CDIO — Chief Design Intelligence Officer (capa evaluativa) — **LIVE**
Sellado en SCS C78 (`vault/knowledge_base/scs/scs_c78_cdio_active.md`).
- **Datasets**: `CDIO-00` kernel + `CDIO-01` visual + `CDIO-02` ux + `CDIO-03`
  trust/premium + `CDIO-04` conversion + `CDIO-05` review pipeline.
- **Código**: `modules/cdio/scorer.py` (251 líneas), `bus_bridge.py`, `telemetry.py`.
- **Agentes**: `cdio-core`, `cdio-reviewer`, `cdio-standards-librarian`.
- **Hook**: `hooks/cdio_visual_advisory.js`, registrado en `hooks/hook-dispatcher.js`
  (PreToolUse, advisory nivel-2, fail-open, nunca bloquea).
- **Tests**: `tools/test_cdio.py`.
- **Gate**: `PR-CDIO-REVIEW-GATE-001` — APPROVE requiere score ≥ 80 **y** cero
  críticos. El score lo computa código determinista, no la opinión del agente
  (`T-DESIGN-OPINION-VS-CRITERIA-001`).
- **Checks mecánicos ya implementados** en `scorer.py`: contraste WCAG 2.1 AA
  (4.5:1 body / 3:1 large), tap-target ≥ 44px, body font móvil ≥ 16px,
  niveles tipográficos ≤ 3, line-measure 45–75 chars, spacing múltiplo de 8px,
  exactamente 1 CTA primario above-the-fold.

**Consecuencia directa: el "Design Quality Gate" del Sprint 3 ya existe.**
Construir `tools/design_gate.py` sería un DUPLICADO ARQUITECTÓNICO — exactamente
lo que el motor D2A (`modules/duplicate_to_advantage/`) existe para detener.

### 1.4 DESIGN.md canónico (capa de tokens) — **YA EXISTE**
- `modules/design-md/DESIGN.md.template` + `commands/design-md.md` + `README.md`
  + wrappers. Front-matter YAML con `colors`, `typography`, `spacing`, `rounded`,
  `components` (tokens referenciables vía `{path.to.token}`), más secciones en
  prosa: Overview, Colors, Typography, Layout, Elevation, Shapes, Components,
  Do's and Don'ts.

**Consecuencia: el `DESIGN_MD_TEMPLATE.md` del Sprint 2 ya existe.**

### 1.5 Búsqueda de patrones de diseño
- `commands/cpp-design.md` + `tools/design_index.py` +
  `modules/karimo-harness/design_tools_dataset.json` — BM25 sobre 10 sistemas
  reales × 15 patrones, <250 ms.

---

## 2. GAPS REALES (lo que de verdad falta)

### G1 — El Anti-Slop es PROSA, nunca CÓDIGO. Ningún gate puede FALLAR por slop.
`modules/cdio/scorer.py` tiene **251 líneas y cero checks de tipografía, paleta o
gradiente**. Los 7 checks mecánicos son de accesibilidad y jerarquía. La regla
"nunca Inter/Roboto/Arial como única fuente" y "nunca gradiente morado sobre
blanco" existe en 2 archivos de prosa y en **0 líneas ejecutables**.

Aplica `feedback_zero_cannot_fall` + la doctrina "un gate debe ser OBSERVADO
rehusando": un gate que nunca puede emitir FAIL por slop no es un gate anti-slop.
Hoy el PP **no puede fallar** un output por slop visual. Ese es el gap central.

### G2 — La plantilla canónica del PP emite el slop que su propio skill prohíbe. (DEFECTO)
`modules/design-md/DESIGN.md.template`:
- línea 27: `body-md.fontFamily: Inter`
- línea 32: `label-sm.fontFamily: Inter`
- línea 11: `tertiary: "#3B82F6"` (azul genérico de framework)

El `frontend-design` SKILL.md línea 36 prohíbe Inter explícitamente. La plantilla
canónica de tokens del PP la usa como fuente de body y de labels. **Auto-contradicción
en el baseline**: cualquier proyecto que herede la plantilla nace en slop, y ningún
gate lo detecta (por G1). Éste es el hallazgo de mayor valor del audit.

### G3 — CDIO es EVALUATIVO; falta el eje GENERATIVO.
CDIO juzga una superficie contra umbrales (¿contrasta?, ¿jerarquiza?, ¿convierte?),
pero **no tiene vocabulario de familia estética**: no responde "¿qué familia debe
usar este producto y por qué?". Y `DESIGN.md.template` **no tiene campo
`aesthetic_family`** en su front-matter → ningún gate puede exigir "familia declarada".
Esto hace irrealizable, hoy, la regla `PR-DESIGN-FAMILY-BEFORE-BUILD-001` del plan.

### G4 — Cobertura DESIGN.md en proyectos del Owner: **NO VERIFICADA**.
El plan asume proyectos con UI (CostaLuz, KobiiCraft…). No escaneado aún.
No se declara nada al respecto hasta medirlo.

### G5 — Prompt packs ausentes.
`brand-to-design-md`, `audit-live-site`, `3-designer-debate`, `remix-two-brands`:
no existen en el PP en ninguna forma.

---

## 3. BLOQUEO DE PREMISA (HR-PREMISE-001)

El plan afirma: *"FUENTE: … ya leído en esta sesión — no re-fetch necesario"*.
**Falso en esta sesión**: el contenido de `awesome-claude-design` NO está en
contexto. Del prompt tengo los NOMBRES de las 9 familias y de los prompt packs,
pero **no** sus especificaciones (swatch, tipo, cuándo-usarla) ni las 7 remix
recipes ni su lógica de arbitraje.

Construir el Sprint 1 sin fetch = inventar contenido y atribuirlo a la fuente.
Eso es fabricación, no absorción. Requiere decisión del Owner (ver §5).

---

## 4. RESUMEN — plan propuesto vs realidad

| Sprint del plan | Realidad medida | Acción correcta |
|---|---|---|
| S1 — elevar `frontend-design/SKILL.md` | Vive bajo `~/.claude/`, licencia Anthropic, HR-001 bloquea escritura | **NO editarlo**. Crear el eje generativo PP-owned (`CDIO-06`) |
| S2 — crear `DESIGN_MD_TEMPLATE.md` | Ya existe (`modules/design-md/DESIGN.md.template`) | **NO crear otra**. Des-slopear la existente + añadir `aesthetic_family` |
| S3 — crear `tools/design_gate.py` | Ya existe (`modules/cdio/scorer.py` + hook + agente + gate sellado) | **NO duplicar** (D2A). **EXTENDER** el scorer con checks anti-slop |
| S4 — prompt packs | Ausentes (gap real) | Construir (requiere fuente) |
| S5 — UKDL | — | Construir, con reglas corregidas a la realidad |

---

## 5. DECISIONES QUE REQUIEREN AL OWNER

1. **Gate**: ¿extender `modules/cdio/scorer.py` con checks anti-slop (recomendado,
   evita duplicado arquitectónico) o construir `design_gate.py` aparte como decía
   el plan?
2. **Fuente**: ¿hacer fetch de `awesome-claude-design` para las 9 familias y las 7
   remix recipes fielmente, o derivar las familias de las 9 style directions que el
   PP ya tiene en `rules/web/design-quality.md` (cero dependencia externa)?
3. **Alcance DESIGN.md**: escanear proyectos del Owner y decidir cuáles reciben
   DESIGN.md (G4 sin medir).

Estado: **STOP #1 — esperando decisión del Owner. Cero archivos mutados.**
