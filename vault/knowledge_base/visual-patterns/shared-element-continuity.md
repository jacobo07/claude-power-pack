---
id: VP-018
name: Shared-Element Continuity (object permanence across states)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [list-detail, dashboard, product-tour, landing, hero, onboarding]
  excluded_from: [checkout, auth, destructive]
  min_expressiveness: restrained
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: hypothesis
  provenance: REF-MOTION-001
  purpose: "que el elemento elegido en el estado N siga siendo el mismo objeto en el estado N+1 (orientacion, no adorno)"
---

# VP-018 — Shared-Element Continuity

## Eje

Movimiento (B6) — continuidad espacial entre estados.

## Tecnica (sin codigo)

Cuando un elemento del estado N (una tarjeta, una foto, una fila) **es** el
sujeto del estado N+1, se transforma desde su posicion y tamaño originales a
los nuevos en lugar de desaparecer y reaparecer. El usuario no tiene que
buscar "donde fue a parar" lo que acaba de pulsar: la permanencia del objeto
responde esa pregunta.

Implementaciones canonicas, por orden de preferencia cuando el proyecto no
tiene ya una: View Transitions API (`view-transition-name` por elemento), o
FLIP manual con `transform` (medir First/Last, Invertir, Reproducir). Un
runtime de animacion (p.ej. `layoutId` de Motion) solo si el proyecto ya
depende de el.

Reglas:

1. **Solo un elemento compartido por transicion**, el que lleva el foco de la
   accion. Varios elementos compartidos compiten y se vuelven ruido.
2. **Duracion corta** (orientativo 150-300 ms): la continuidad debe ser
   percibida, no contemplada.
3. **El foco del teclado sigue al objeto**: tras la transicion, el foco esta
   en el nuevo contenedor del elemento (o en su titulo), nunca en `body`.
4. **Nunca bloquear la entrada**: la transicion es interrumpible; un segundo
   click no espera a que termine.

## Cuando usar

- Lista -> detalle (fila o tarjeta que se expande a su vista de detalle).
- Drill-down de dashboard (una metrica que se convierte en su grafico).
- Dentro de VP-016, cuando un estado nace de un elemento del anterior.

## Cuando NO usar

- Cuando el estado nuevo no es "el mismo objeto": transformar una tarjeta de
  producto en un formulario de pago afirma una identidad que no existe.
- Checkout, auth y acciones destructivas: la continuidad suaviza lo que debe
  sentirse como un cambio de contexto deliberado.
- Navegaciones entre secciones sin elemento comun (usar un fade o nada).

## Movimiento reducido (equivalente, no ausente)

Cambio instantaneo al estado nuevo con el **foco movido al elemento
correspondiente** y, si ayuda, un resaltado estatico breve. La relacion se
comunica por foco y posicion, no por movimiento.

## Soporte de navegador

View Transitions de mismo documento: Chrome/Edge 111+, Safari 18+; Firefox
en desarrollo a fecha de esta entrada. **Fallback obligatorio**: cambio de
estado sin transicion (la funcionalidad es identica). FLIP con `transform`
es universal.

## Contraste y WCAG

2.3.3 via reduced-motion; 2.4.3 orden de foco (el foco sigue al objeto).

## Coste de mantenimiento

Medio: los nombres de transicion deben ser unicos por pagina, y un layout
que cambia puede romper la medicion FLIP silenciosamente.

## Evidence

- REF-MOTION-001 §2 S5->S6: la foto aparece dentro del tracker (f160) y es el
  hero de la pantalla siguiente en f164. Dos frames con desenfoque: lectura
  **HYPOTHESIZED**, por eso `evidence_level: hypothesis`. El principio en si
  tiene respaldo externo amplio (fuentes abajo); lo hipotetico es que la
  referencia lo use.

## Fuentes

- REF-MOTION-001 (observacion propia, 2026-09-30).
- [View Transition API — MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API)
- [FLIP Your Animations — Paul Lewis](https://aerotwist.com/blog/flip-your-animations/)
