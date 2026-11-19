---
id: VP-AJS-002
name: Draggable Snap con alternativa sin arrastre
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, product-tour, onboarding]
  excluded_from: [checkout, auth, admin, settings, form, destructive, docs]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: animejs 4.5.0 MIT @ 01b81be1 (fuente leida, solo principios; BCAP2-04)
  purpose: "que una coleccion se pueda recorrer arrastrando con inercia y encaje, sin que el arrastre sea el unico camino a ningun contenido"
---

# VP-AJS-002 — Draggable Snap con alternativa sin arrastre

## Eje

Movimiento — interaccion fisica (arrastrar, soltar, lanzar, encajar).

## Tecnica (sin codigo)

El contenedor desplaza sus elementos con arrastre de puntero/tactil; al soltar, la velocidad se convierte en inercia y el
reposo se encaja al elemento mas cercano (snap). Toda la informacion y toda accion esencial tienen una via sin arrastre:
botones anterior/siguiente con foco visible, teclado (flechas), y orden de tabulacion natural. El estado (indice actual)
es unico y lo comparten arrastre, botones y teclado. Upstream (Anime.js `createDraggable` con snap y release) trae la
fisica; la gramatica exige ademas la via alternativa, que la libreria no impone.

## Cuando usar

- Carruseles o galerias de escaparate donde recorrer es placer y no la tarea.
- Una pieza por vista, con alternativa sin arrastre desde el primer render.

## Cuando NO usar

- Cuando arrastrar es la unica forma de alcanzar contenido o ejecutar una accion esencial.
- Dentro de contenedores con scroll anidado del mismo eje: captura el gesto y rompe la navegacion.
- Superficies transaccionales, formularios o destructivas: un gesto accidental no puede tener consecuencias.
- Sin limpieza de escuchas al desmontar o al cambiar de ruta.

## Movimiento reducido (equivalente, no ausente)

Sin inercia ni animacion de encaje: el cambio de elemento es inmediato; botones y teclado siguen funcionando y el
estado/indice anunciado es el mismo.

## Soporte de navegador

Eventos de puntero universales; la inercia es de implementacion propia o de libreria.

## Coste de mantenimiento

Medio: tres vias de entrada (puntero, tactil, teclado) que deben mantenerse sincronizadas.

## Evidence

`research`: capacidad inventariada de la fuente upstream; no construido aun en un proyecto del Owner.

## Fuentes

- https://github.com/juliangarnier/anime/tree/01b81be1df6843ccfe0a71c0699a746bf740dd77 (Anime.js v4.5.0, MIT; ver `vault/programs/bcap-2/animejs/NOTICE.md`). Solo el patron de diseno; ningun codigo copiado.
