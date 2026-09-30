---
id: VP-016
name: Device Demo State Carousel (stable shell, rotating proof)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, hero, onboarding, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: local
  provenance: REF-MOTION-001
  purpose: "demostrar N capacidades del producto en el hueco de una sola captura, sin mover el CTA"
---

# VP-016 — Device Demo State Carousel

## Eje

Movimiento (B4) — coreografia de estados.

## Tecnica (sin codigo)

Un **marco estable** (titular + CTA de conversion + dispositivo) que nunca se
mueve, y dentro del dispositivo una secuencia de **estados reales del
producto**, uno por capacidad, en orden narrativo. Solo cambia el contenido
de la pantalla; el marco, el dispositivo y el CTA permanecen quietos, asi que
el ojo no tiene que re-orientarse en cada cambio.

Ritmo observado en REF-MOTION-001 (INFERRED, +/-33 ms): transiciones cortas
(~100-250 ms) contra esperas largas (~0.5-2.5 s); proporcion transicion:espera
~1:5 a 1:10. Son rangos observados, no tokens prescritos: el proyecto fija los
suyos en DESIGN.md.

Reglas de construccion:

1. **Un estado = una capacidad.** Si dos estados demuestran lo mismo, sobra uno.
2. **Orden narrativo, no alfabetico**: del valor mas inmediato al mas avanzado.
3. **Animar solo `opacity`/`transform`** de la capa de pantalla; nunca el
   layout del marco.
4. **Control de pausa visible y operable por teclado** (WCAG 2.2.2) y selector
   de estado (tabs/puntos) que funcione tambien como navegacion manual.
5. **Pausa al perder visibilidad** (pestaña oculta / fuera del viewport) y al
   recibir foco o hover el dispositivo.
6. **Estado completo en el DOM**: cada estado es contenido real, no un video;
   lectores de pantalla leen el estado activo (`aria-live="polite"` en el
   titulo del estado, no en todo el contenido).

## Cuando usar

- Hero de landing u onboarding de marketing cuyo producto se entiende mejor
  *viendolo* hacer varias cosas que leyendo una lista de features.
- Tour de producto con 3-6 capacidades con captura propia.

## Cuando NO usar

- Checkout, auth, formularios, ajustes, admin, dashboards de trabajo: la
  atencion es el recurso escaso y un carrusel autonomo compite con la tarea
  (CDIO-07 §5, colision con Flow).
- Cuando solo existe una capacidad que mostrar: una captura quieta es mejor.
- Cuando el contrato declara `expressiveness: none|restrained` o
  `motion_budget: none|low`: el patron excede el contrato y el resolver lo
  retiene.
- Cuando los estados serian maquetas inventadas: cada estado debe ser una
  pantalla real del producto (Reality Contract).

## Variantes

- Autoplay con pausa (por defecto) · solo manual (tabs) · controlado por
  scroll (ver VP-010, con su fallback de Safari).

## Movimiento reducido (equivalente, no ausente)

Con `prefers-reduced-motion: reduce`: **sin autoplay**, cambio de estado
instantaneo (sin transform ni blur), y los mismos estados alcanzables con el
selector manual. La informacion y las transiciones de estado llegan; solo
desaparece el movimiento (CDIO-07 §5, `equivalent`).

## Soporte de navegador

Universal si se implementa con transiciones CSS de `opacity`/`transform` y
un temporizador JS. `IntersectionObserver` y `visibilitychange` universales.

## Contraste y WCAG

2.2.2 Pause, Stop, Hide (obligatorio: el contenido se mueve >5 s junto a otro
contenido), 2.3.3 Animation from Interactions via reduced-motion, 2.1.1
teclado para pausa y selector, 4.1.2 nombre/estado del boton de pausa.

## Coste de mantenimiento

Medio: cada estado es una pantalla real que debe mantenerse al dia con el
producto; un estado obsoleto es una afirmacion falsa sobre el producto.

## Evidence

- REF-MOTION-001 (`evidence/REF-MOTION-001/OBSERVATION.md`): una referencia,
  capturada de pantalla con camara en mano. La referencia **no** tiene control
  de pausa; este patron lo exige.
- Produccion: `examples/motion-grammar/device-demo/` verificado por
  `tools/test_motion_grammar.py` (lane Production Reality).
- `evidence_level: local` — sube solo con una segunda referencia independiente
  y una transferencia a otra superficie que pase el gate.

## Fuentes

- REF-MOTION-001 (observacion propia, 2026-09-30).
- [WCAG 2.2 — 2.2.2 Pause, Stop, Hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html)
