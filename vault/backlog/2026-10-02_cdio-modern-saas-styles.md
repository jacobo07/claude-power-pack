# Backlog — CDIO: tres estilos SaaS modernos (2026-10-02)

El Owner pidió añadir al backlog tres estilos tras cerrar CDIO-09 (Focused Monochrome UI) y
empezar por el primero. Salen de una propuesta hecha de memoria, no medida: ninguno entra en
CDIO como invariante hasta que se destile de referencias reales, con la misma regla que F10
(CDIO-06 sec. 9) — un rasgo entra solo si sobrevive a un cambio de marca, plataforma o dominio.

| # | Estilo | Encaje en CDIO | Estado | Qué falta |
|---|---|---|---|---|
| 1 | **Monocromo oscuro** (Linear dark, Vercel dark, Raycast) | Variante oscura de F1 en CDIO-06, gemela de la variante sin acento | **PARCIAL** — CDIO-06 sec. 10: reglas 1–4 vinculantes tras medir un banco de 6 webs elegido por el agente (Linear, Vercel docs y Resend como ejemplares; Raycast, PlanetScale y Zed como contraste) más InfinityOps `.theme-dark`. InfinityOps corregido en PR #472, fusionado el 2026-10-02 (`014b874f`) tras renderizar el head fusionado en GEX44 | Reglas 5 (anillo de foco: la medición fue INCONCLUSIVE) y 6 (fondo de un modal en oscuro: sin modal en el banco). Repetir la medición del foco con Tab real en vez de foco programático |
| 2 | **Superficie conversacional de IA** (ChatGPT, Claude.ai, Perplexity) | Eje de interacción nuevo al estilo de CDIO-09 (comportamiento, no estética): CDIO-10 candidato | PENDIENTE | Referencias; prueba de novedad frente a CDIO-02/07/09 (HR-NOVELTY-001); criterios en la gramática de CDIO-08 |
| 3 | **Enterprise sistemático** (IBM Carbon, Salesforce Lightning, Atlassian) | Familia nueva candidata F11: back-office denso de escritorio, entre F4 y F10 | PENDIENTE | Prueba de novedad: demostrar que no es F4 con otra paleta; banco de referencias; tocar `scorer.py` (KNOWN_FAMILIES, sanción de fuente) y `test_cdio_f10.py` (frontera F11) |

## Por qué en este orden

1. Monocromo oscuro extiende lo recién cerrado y ya tiene un consumidor real: el tema oscuro
   opcional de InfinityOps, cuyas colisiones de contraste ya están medidas.
2. La superficie conversacional es el hueco más grande para productos de IA: hoy CDIO no tiene
   criterios para juzgarla.
3. Enterprise sistemático es la única familia nueva claramente justificada, y la más cara: cambia
   el scorer.

## Comprobación de novedad y de acceso (2026-10-02, primera pasada)

**2 · Superficie conversacional.** CDIO no tiene nada propio: `chat|stream|assistant|LLM|
citation|regenerat` en `vault/knowledge_base/cdio/` da dos coincidencias incidentales
(CDIO-04:183, CDIO-08:50). Fuera de CDIO, `vendor/skills/building-ai-saas-products/knowledge/`
habla de memoria de agentes, logs y precios, no de la superficie. Lo genérico ya tiene dueño:
CDIO-07 §1 (`feedback_latency_ms`, `progress_threshold_ms`, `waiting`, `error_posture`) y la
regla global *generated-content-needs-an-evidence-gate* (veracidad de lo generado). Lo que
quedaría para un CDIO-10 es lo propio del chat: texto que llega en streaming, detener/
interrumpir, anclaje del scroll durante el streaming, el composer como acción primaria,
regenerar/editar, procedencia visible de las afirmaciones y anuncio a lector de pantalla del
texto en streaming. Aún sin las 13 preguntas de HR-NOVELTY-001.

**Acceso al banco (sonda headless desde GEX44, IP de centro de datos):** ChatGPT, Perplexity,
Claude.ai y Mistral devuelven **403** con el reto de Cloudflare ("Just a moment..."); solo
HuggingChat carga (200, composer presente). Un solo referente no es un banco: el 2 está
**BLOQUEADO por acceso**, no por diseño. Ojo: el detector `challenge` de la sonda leyó `false`
en los cuatro 403; la prueba es el status y el título, no ese campo.

**3 · Enterprise sistemático.** Frente a F4 (CDIO-06:70, "charts are the hero", paleta
categórica saturada) y F10 (CDIO-06:111, una tarea por pantalla, móvil primero), Carbon/
Lightning/Atlassian son flujos de registro de escritorio (formularios, tablas, procesos) sobre
fondo neutro con un solo acento de marca y modos de densidad: el hueco es plausible, no probado.
Coste en código: `modules/cdio/scorer.py:341` fija `KNOWN_FAMILIES` en F1..F10 y :342 la
sanción de fuente. **Acceso:** las cuatro referencias cargan (200) con tablas e inputs reales
(Carbon docs y Storybook, Lightning, Atlassian): el banco es medible ya.

### Banco enterprise medido (2026-10-03, GEX44, Chromium headless, 1440×900, tema claro)

Siete marcas: Carbon (IBM), Lightning (Salesforce, `lightning-datatable` "Basic Data Table"),
Atlassian (dynamic table), Fluent 2 (Microsoft), Primer (GitHub), UI5 (SAP), Ant Design. Se mide
el componente de demostración pública de cada sistema, **no el producto** (Jira, IBM Cloud y
Salesforce están tras login): es un sustituto declarado. Se midió la tabla, no el documento
que la rodea; tres pasadas anteriores midieron la tabla de API de la página por error y se
descartaron.

| sistema | fila (px) | cabecera (px) | texto | tinta / contraste | peso cabecera | tinte cabecera | zebra | divisor |
|---|---|---|---|---|---|---|---|---|
| Carbon | 48 | 48 | 14px | #525252 · 7.1 | 600 | 1.32 | no | #c6c6c6 · 1.55 |
| Lightning | 36.5 | — | 13px | #5c5c5c · 6.69 | — | — | no | — |
| Atlassian | 45 | 34 | 14px | #292a2e · 14.34 | 653 | 1.00 | 2 fondos | — |
| Fluent 2 | 45 | 32.5 | 14px | #242424 · 14.87 | 400 | 1.00 | no | #e0e0e0 · 1.26 |
| Primer | 37 | 38 | 12px | #1f2328 · 15.8 | 600 | 1.06 | no | #d1d9e0 · 1.43 |
| UI5 | 32 | 34 | 14px | #131e29 · 16.86 | 400 | 1.08 | 2 fondos | #a8b2bd · 2.15 |
| Ant | 55 | 55 | 14px | #1f1f1f · 16.48 | 600 | 1.04 | no | #f0f0f0 · 1.14 |

"—" = no medido (el instrumento no lo vio), nunca "ausente". Huecos conocidos: cabecera y
divisores de Lightning; padding de Atlassian (vive en un elemento interior); la fuente de UI5
(su tipografía "72" no cargó en el playground: el campo dice Times New Roman y no vale);
controles y acento (las historias aisladas casi no traen botones ni inputs).

**Lo que sobrevive a 7 marcas:** fondo blanco o casi blanco (#fff–#f5f6f7) en 7/7; texto de
cuerpo 12–14px (13–14 en 6/7) con contraste de tinta muy alto (6.7–16.9:1); cabecera nunca en
mayúsculas, distinguida por peso (600–653 en 4/7) y/o un tinte tenue (1.04–1.32:1); sin zebra
en 5/7; divisor de 1px a 1.14–2.15:1 donde se midió (5/7); tipografía de marca o del sistema.
**No sobrevive:** la altura de fila (32–55px, mediana 45) — la densidad varía por sistema,
coherente con que todos la ofrecen como modo; el modo en sí no se midió.

**Consecuencia para la prueba de novedad.** El banco separa este estilo de F4 por paleta (F4 es
#181818 con paleta categórica saturada) y de F10 por estructura (tablas de 805–1408px con
muchas columnas, no una tarea por pantalla). Pero por paleta queda cerca de F1 (fondo blanco,
contención): su identidad es **estructural**, no estética. Eso apunta a un eje estructural al
estilo de CDIO-09 más que a una familia estética F11. Decisión pendiente del Owner.

## Lo que este fichero no afirma

No está medido si algún dataset existente ya cubre en parte el 2 o el 3. El primer paso de cada
uno es esa comprobación, no la escritura.
