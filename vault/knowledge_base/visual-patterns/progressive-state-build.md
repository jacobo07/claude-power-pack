---
id: VP-017
name: Intra-State Progressive Build
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, hero, onboarding, product-tour]
  excluded_from: [checkout, auth, admin, settings, form, destructive]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: local
  provenance: REF-MOTION-001
  purpose: "que un estado demostrado se lea como producto vivo (causa -> efecto), no como captura"
---

# VP-017 — Intra-State Progressive Build

## Eje

Movimiento (B5) — revelado progresivo dentro de un estado.

## Tecnica (sin codigo)

Dentro de un estado ya visible, el contenido se **ensambla en el orden en que
el producto lo produciria**: la pregunta del usuario, luego la respuesta,
luego la sugerencia siguiente. Cada paso depende del anterior, asi que el
orden comunica causalidad ("pregunte X, me respondio Y") en lugar de decorar.

Observado en REF-MOTION-001 (OBSERVED): burbuja de usuario ~2.0 s, respuesta
~2.2 s, segunda respuesta ~3.2 s, chip de sugerencia ~3.7 s; separaciones de
~0.2-1.0 s. La primera respuesta llega rapido (el sistema "responde"); las
siguientes se espacian para poder leerlas.

Reglas:

1. **El orden de aparicion es el orden causal del producto.** Un stagger
   arbitrario (izquierda a derecha, arriba a abajo sin dependencia) es
   decoracion, y en ese caso usar un fade unico.
2. **Cada elemento aparece una vez y se queda**: nada se reordena mientras el
   usuario lo lee.
3. **Espaciado legible**: el siguiente elemento no llega antes de que el
   anterior sea legible (orientativo: >=~250 ms por linea corta).
4. **Entrada con `opacity` + desplazamiento pequeño** (<=8-12 px) en la
   direccion de lectura/flujo del producto; nunca escala del contenedor.

## Cuando usar

- Demostrar un producto conversacional, generativo o de pipeline, donde el
  valor ES la secuencia (pregunta -> respuesta, entrada -> resultado).
- Dentro de un estado de VP-016.

## Cuando NO usar

- Contenido que el usuario necesita completo de inmediato (tablas, formularios,
  resultados de busqueda): el revelado progresivo retrasa la tarea.
- Listas sin dependencia causal entre elementos: es un stagger decorativo.
- Como "animacion de carga" que simula trabajo que no ocurre: fabrica un estado
  (CDIO-07 §5, colision de confianza).

## Movimiento reducido (equivalente, no ausente)

Con `prefers-reduced-motion: reduce` se renderiza el **estado final completo**
de golpe, en el mismo orden de lectura. El usuario recibe la misma
informacion; la causalidad queda expresada por el orden del contenido.

## Soporte de navegador

Universal (transiciones CSS + temporizador, o `animation-delay`).

## Contraste y WCAG

2.3.3 via reduced-motion; `aria-live="polite"` solo en el contenedor del
estado si la construccion comunica algo que no esta en el titulo del estado,
para no inundar el lector de pantalla con cada linea.

## Coste de mantenimiento

Bajo si los tiempos son tokens del proyecto y no numeros sueltos.

## Evidence

- REF-MOTION-001 §2 estado S4. Una referencia: `evidence_level: local`.
- Produccion: `examples/motion-grammar/device-demo/` estado "coach".

## Fuentes

- REF-MOTION-001 (observacion propia, 2026-09-30).
