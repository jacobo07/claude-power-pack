---
id: VP-025
name: Scroll Overflow Fade (fundido proporcional al contenido restante)
type: pattern
domain: visual-patterns
status: active
provenance: REF-KITCHEN-001
evidence_level: research
---

# VP-025 — Scroll Overflow Fade

## Eje

Superficie (D3) — indicador de desbordamiento en una lista con scroll.

## Tecnica (sin codigo)

Dos degradados (arriba y abajo) del color de fondo a transparente cubren los
bordes de la lista. La altura de cada uno **es la distancia de scroll que queda
en ese lado**, con un tope (76 px en la fuente). Contrato observado en
REF-KITCHEN-001 (OBSERVED):

1. **Sin desbordamiento, sin fundido**: ambas alturas son 0.
2. **En un extremo, ese fundido es 0**: al final de la lista no se insinua
   contenido que no existe.
3. **Cambia de forma continua** al hacer scroll, no solo al llegar a los bordes.
4. **Las capas no capturan el puntero** (los elementos debajo siguen siendo
   clicables).
5. **Calculo agrupado**: listener de scroll pasivo + requestAnimationFrame +
   ResizeObserver sobre el contenedor y su contenido; se recalcula al montar.
6. **Detalles de contenedor**: `overscroll-behavior: contain`, hueco de barra
   estable (`scrollbar-gutter: stable`), marcado semantico de lista.

## Cuando usar

- Listas acotadas dentro de tarjetas o paneles (paises, miembros, opciones) donde
  la barra de scroll sola no indica que hay mas.

## Cuando NO usar

- Fondos con imagen o degradado: el fundido del color plano no coincide (usar
  `mask-image` en su lugar).
- Listas donde el ultimo elemento visible debe leerse completo (resultados de
  busqueda priorizados): el fundido rebaja el contraste justo ahi.
- Como unico indicador: con teclado o lector de pantalla el fundido no se
  percibe; el contenedor con scroll debe poder recibir foco si sus elementos no
  son enfocables (UNKNOWN en la fuente).

## Movimiento reducido

No anima: sigue al scroll del usuario. No requiere variante.

## Soporte de navegador

Universal. Alternativa sin JS: `mask-image` con `animation-timeline: scroll()`,
sin soporte en Safari (ver HR-VP-02 y VP-010).

## Contraste y WCAG

El texto bajo el fundido pierde contraste; mientras quede tapado parcialmente
debe haber scroll disponible para leerlo entero. Medir el elemento que queda
dentro del fundido en reposo.

## Coste de mantenimiento

Bajo.

## Evidence

Investigacion: REF-KITCHEN-001 componente 11.

## Fuentes

- https://www.dqnamo.com/experiments/scroll-fade-list (solo principios; sin licencia declarada).
