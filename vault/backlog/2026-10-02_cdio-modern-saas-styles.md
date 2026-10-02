# Backlog — CDIO: tres estilos SaaS modernos (2026-10-02)

El Owner pidió añadir al backlog tres estilos tras cerrar CDIO-09 (Focused Monochrome UI) y
empezar por el primero. Salen de una propuesta hecha de memoria, no medida: ninguno entra en
CDIO como invariante hasta que se destile de referencias reales, con la misma regla que F10
(CDIO-06 sec. 9) — un rasgo entra solo si sobrevive a un cambio de marca, plataforma o dominio.

| # | Estilo | Encaje en CDIO | Estado | Qué falta |
|---|---|---|---|---|
| 1 | **Monocromo oscuro** (Linear dark, Vercel dark, Raycast) | Variante oscura de F1 en CDIO-06, gemela de la variante sin acento | **PARCIAL** — CDIO-06 sec. 10: reglas 1–4 vinculantes tras medir un banco de 6 webs elegido por el agente (Linear, Vercel docs y Resend como ejemplares; Raycast, PlanetScale y Zed como contraste) más InfinityOps `.theme-dark`. InfinityOps corregido en PR #472 | Reglas 5 (anillo de foco: la medición fue INCONCLUSIVE) y 6 (fondo de un modal en oscuro: sin modal en el banco). Repetir la medición del foco con Tab real en vez de foco programático |
| 2 | **Superficie conversacional de IA** (ChatGPT, Claude.ai, Perplexity) | Eje de interacción nuevo al estilo de CDIO-09 (comportamiento, no estética): CDIO-10 candidato | PENDIENTE | Referencias; prueba de novedad frente a CDIO-02/07/09 (HR-NOVELTY-001); criterios en la gramática de CDIO-08 |
| 3 | **Enterprise sistemático** (IBM Carbon, Salesforce Lightning, Atlassian) | Familia nueva candidata F11: back-office denso de escritorio, entre F4 y F10 | PENDIENTE | Prueba de novedad: demostrar que no es F4 con otra paleta; banco de referencias; tocar `scorer.py` (KNOWN_FAMILIES, sanción de fuente) y `test_cdio_f10.py` (frontera F11) |

## Por qué en este orden

1. Monocromo oscuro extiende lo recién cerrado y ya tiene un consumidor real: el tema oscuro
   opcional de InfinityOps, cuyas colisiones de contraste ya están medidas.
2. La superficie conversacional es el hueco más grande para productos de IA: hoy CDIO no tiene
   criterios para juzgarla.
3. Enterprise sistemático es la única familia nueva claramente justificada, y la más cara: cambia
   el scorer.

## Lo que este fichero no afirma

No está medido si algún dataset existente ya cubre en parte el 2 o el 3. El primer paso de cada
uno es esa comprobación, no la escritura.
