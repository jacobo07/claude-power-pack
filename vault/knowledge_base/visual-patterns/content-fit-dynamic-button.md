---
id: VP-021
name: Content-Fit Dynamic Button (ancho que sigue a la etiqueta)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [form, settings, admin, checkout]
  excluded_from: [docs]
  min_expressiveness: restrained
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que un boton cuya etiqueta cambia de estado (Guardar, Guardando, Guardado) no salte de tamano ni desplace lo que tiene al lado"
---

# VP-021 — Content-Fit Dynamic Button

## Eje

Interaccion (E3) — cambio de etiqueta con ancho animado.

## Tecnica (sin codigo)

El boton mide el ancho que necesita la etiqueta nueva y anima su propio ancho
hasta ese valor, mientras el texto saliente y el entrante se cruzan con un
desplazamiento vertical corto.

Contrato observado en REF-KITCHEN-001 (OBSERVED):

1. **Medir, no estimar**: un elemento oculto (`aria-hidden`) con el mismo texto,
   relleno y borde da el ancho real; se vuelve a medir cuando cambia el texto,
   el icono o la variante, y con ResizeObserver (las fuentes web cargan tarde).
2. **Ancho por resorte sin rebote** (~0.26 s). Un rebote en un boton se lee como
   un error de maquetacion.
3. **Texto e icono se cruzan** con ~8 px de recorrido vertical en ~0.18 s y el
   ease-out compartido del proyecto. El icono puede tener su propia clave de
   estado, separada del texto.
4. **Modo ancho completo**: si el boton ocupa toda la fila, no hay nada que
   animar y la animacion de ancho se omite.
5. **Presion**: escala 0.97 al pulsar; color y sombra con la misma curva corta.

## Cuando usar

- Botones con estados de ciclo de vida: Guardar, Guardando, Guardado; Copiar,
  Copiado; acciones que cambian tras un exito.
- Barras de acciones donde un salto de ancho empujaria a los botones vecinos.

## Cuando NO usar

- Si la etiqueta cambia sin que cambie el estado: animar un cambio cosmetico
  distrae.
- Cuando el cambio de estado necesita ser anunciado y no hay region viva: la
  fuente no anuncia el cambio de etiqueta (UNKNOWN), asi que en un estado de
  exito o error hay que anadir un `role=status` aparte; el boton solo no basta.
- Etiquetas largas en pantallas estrechas: el ancho medido puede desbordar; usar
  ancho completo.

## Movimiento reducido (equivalente, no ausente)

Sin desplazamiento vertical del texto y ancho instantaneo; el cruce se acorta a
un fundido breve. La etiqueta final y el estado son los mismos.

## Soporte de navegador

Universal (ResizeObserver y `getComputedStyle` en todos los navegadores actuales).

## Contraste y WCAG

Durante el cruce, ambos textos estan a opacidad parcial: el estado final debe
cumplir 4.5:1. Mantener un objetivo tactil minimo aunque la etiqueta sea corta
(WCAG 2.5.8: 24 px).

## Coste de mantenimiento

Bajo, si la curva y la duracion son tokens del proyecto.

## Evidence

Investigacion: REF-KITCHEN-001 componente 7.

## Fuentes

- https://www.dqnamo.com/experiments/dynamic-button (solo principios; sin licencia declarada).
