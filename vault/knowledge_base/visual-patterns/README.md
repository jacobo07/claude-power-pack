# Visual Patterns — Knowledge Base Index

Entradas de patrones de branding/CSS reutilizables, verificados contra
fuentes reales (no inventadas). Cada entrada documenta cuando usar el patron
Y cuando NO usarlo — un patron sin limitaciones documentadas no es un
patron, es publicidad (ver HR-VP-01).

Origen: investigacion web de 2026-07-30, 14 patrones distribuidos en 4 ejes,
mas [[text-bevel-effect]] (VP-001, ya implementado en produccion antes de la
investigacion). Solapamiento verificado contra `CDIO-06-aesthetic-families.md`
(vault/knowledge_base/cdio/): CDIO-06 juzga a que familia estetica pertenece
una superficie (evaluativo); esta carpeta documenta COMO implementar un
efecto concreto (patron). No son redundantes.

## Hard Rules (dominio: visual-patterns)

### HR-VP-01 — Toda entrada tiene "Cuando NO usar"
TRIGGER: Antes de registrar cualquier patron visual nuevo en este directorio.
STOP: Si el campo "Cuando NO usar" esta vacio o es generico ("usar con
cuidado"), el patron no esta completo. Un patron sin limitaciones
documentadas es publicidad, no conocimiento reutilizable.
EVIDENCIA: Owner, 2026-07-30 — instruccion explicita al registrar los 14
patrones de branding.

### HR-VP-02 — Soporte de navegador documentado antes de usar
TRIGGER: Antes de que cualquier agente recomiende `backdrop-filter`,
`animation-timeline`, `font-variation-settings`, `-webkit-text-stroke`, o
cualquier propiedad con gaps conocidos de Safari/Firefox.
STOP: Leer el campo "Soporte de navegador" de la entrada correspondiente y
declarar el fallback explicito ANTES de implementar — no asumir soporte
universal por defecto.
EVIDENCIA: gaps reales verificados en la investigacion — Safari no soporta
`animation-timeline: view()` ni el auto-switch de favicon adaptativo;
Firefox soporta scroll-driven animations solo detras de un flag.

### HR-VP-03 — Coste de contraste documentado para patrones de texto
TRIGGER: Antes de aplicar cualquier patron del eje A (relleno-texto) sobre
un fondo variable o no controlado.
STOP: Verificar el contraste en el punto MAS CLARO/EXTREMO del efecto
(gradiente, foil, imagen), no en un promedio visual — gradient/bevel/
metallic/glow/holografico pueden fallar WCAG AA en fragmentos del texto
aunque "se vean bien" en conjunto.
EVIDENCIA: patron recurrente detectado en la investigacion — todo efecto de
relleno de texto vía `background-clip:text` reparte el color de forma no
uniforme sobre las letras.

## Indice de patrones

| ID | Patron | Eje | Estado |
|---|---|---|---|
| VP-001 | [[text-bevel-effect]] — Text Bevel Effect | A2 relleno-texto | Implementado (`infinity_ui/components/SocialBrand.tsx`) |
| VP-002 | [[gradient-text]] — Gradient Text (patron padre) | A1 relleno-texto | Investigacion |
| VP-003 | [[metallic-chrome-text]] — Metallic/Chrome Text | A3 relleno-texto | Investigacion |
| VP-004 | [[gradient-stroke-text]] — Gradient Stroke Text | A4 relleno-texto | Investigacion |
| VP-005 | [[glow-neon-text]] — Glow/Neon Text | A5 relleno-texto | Investigacion |
| VP-006 | [[image-video-filled-text]] — Image/Video-Filled Text | A6 relleno-texto | Investigacion |
| VP-007 | [[holographic-iridescent-foil-text]] — Holographic/Iridescent Foil Text | A7 relleno-texto | Investigacion |
| VP-008 | [[duotone-image-overlay]] — Duotone Image Overlay | A8 relleno-texto | Investigacion |
| VP-009 | [[variable-font-animation]] — Variable Font Weight/Width Animation | B1 movimiento | Investigacion |
| VP-010 | [[scroll-driven-reveal]] — Scroll-Driven Reveal (zero-JS) | B2 movimiento | Investigacion |
| VP-011 | [[animated-grainy-texture]] — Animated Grainy Texture | B3 movimiento | Investigacion |
| VP-012 | [[oklch-color-mix-tokens]] — OKLCH + color-mix() Dynamic Brand Tinting | C1 color-tokens | Investigacion |
| VP-013 | [[adaptive-svg-favicon]] — Adaptive SVG Favicon | C2 color-tokens | Investigacion |
| VP-014 | [[glassmorphism-brand-card]] — Glassmorphism Brand Card | D1 superficie-textura | Investigacion |
| VP-015 | [[grainy-gradient-background]] — Grainy Gradient Background | D2 superficie-textura | Investigacion |

"Investigacion" = patron verificado con fuentes reales, sin implementacion
propia todavia en un proyecto del Owner. Actualizar el campo Evidence de la
entrada correspondiente en cuanto se implemente por primera vez.

## Discoverable via /cpp-design

Registrado como `manual_entries` en
`modules/karimo-harness/refresh_sources.json` para que
`tools/design_index.py --search` (usado por `/cpp-design`) los devuelva
junto a los 150 patrones de UI baked. Requiere `--refresh` tras un clon
nuevo — ver el contrato de opt-in documentado en ese mismo archivo.
