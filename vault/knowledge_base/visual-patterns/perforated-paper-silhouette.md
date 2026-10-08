---
id: VP-026
name: Perforated Paper Silhouette (ticket y sello con tilt condicionado)
type: pattern
domain: visual-patterns
status: active
provenance: REF-KITCHEN-001
evidence_level: research
---

# VP-026 — Perforated Paper Silhouette

## Eje

Superficie (D4) — silueta de papel troquelado (entrada, sello postal).

## Tecnica (sin codigo)

La forma se recorta con `clip-path: polygon()` generado a partir de parametros,
no con una imagen. Dos variantes de REF-KITCHEN-001 (OBSERVED):

**A. Ticket.** Cuerpo y talon en una rejilla (talon ~24 % de alto); muescas en
la linea de corte (tamano por variable CSS) y una linea discontinua decorativa,
oculta a tecnologias de apoyo. Sombra con dos `drop-shadow` (la sombra de caja
no sigue el recorte). Raiz `article` con etiqueta.

**B. Sello.** Perforaciones en los cuatro lados; profundidad y numero de dientes
**acotados** (profundidad 0..10, 4..32 horizontales, 4..40 verticales) para que
ningun valor produzca una forma rota. Admite imagen, texto o contenido
arbitrario; si se marca como decorativo, la etiqueta se omite.

**Tilt opcional (solo A).** Inclinacion maxima ~6 grados, perspectiva ~1100,
escala 1.018, 220 ms. Se activa **solo** si se cumplen a la vez
`(hover: hover)`, `(pointer: fine)` y `(prefers-reduced-motion: no-preference)`;
en servidor queda desactivado; en tactil se mantiene `touch-action: pan-y` para
no bloquear el scroll vertical.

## Cuando usar

- Entradas, invitaciones, pases, coleccionables, recompensas: objetos que en la
  realidad son papel.

## Cuando NO usar

- Tarjetas genericas de contenido: la metafora de papel sin objeto real detras
  es decoracion.
- Contenido que debe llegar al borde: el recorte come las esquinas y las muescas.
- Tilt en superficies con texto largo o formularios: inclinar texto dificulta la
  lectura.
- Si hay que imprimir o exportar: `clip-path` no se conserva en todos los
  motores de impresion.

## Movimiento reducido

El tilt no se activa (condicion de la media query). La silueta es estatica.

## Soporte de navegador

`clip-path: polygon()` y `filter: drop-shadow()` universales. Media queries de
capacidad de puntero universales.

## Contraste y WCAG

El texto sobre el color del papel debe cumplir 4.5:1 (la fuente usa tinta casi
negra sobre naranja; medir el par real). La linea de corte es decoracion.

## Coste de mantenimiento

Bajo: una funcion pura que genera el poligono.

## Evidence

Investigacion: REF-KITCHEN-001 componentes 9 y 10.

## Fuentes

- https://www.dqnamo.com/experiments/ticket
- https://www.dqnamo.com/experiments/stamp
  (solo principios; sin licencia declarada).
