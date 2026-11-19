---
id: VP-AJS-001
name: Staggered Timeline Choreography (coreografia escalonada de varios elementos)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, hero, product-tour, onboarding]
  excluded_from: [checkout, auth, admin, settings, form, dashboard, destructive, docs, list-detail]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: animejs 4.5.0 MIT @ 01b81be1 (fuente leida, solo principios; BCAP2-04)
  purpose: "que varios elementos de una misma escena entren en un orden legible (lectura de arriba abajo, del centro hacia fuera) en vez de aparecer a la vez"
---

# VP-AJS-001 — Staggered Timeline Choreography (coreografia escalonada de varios elementos)

## Eje

Movimiento — secuenciacion en el tiempo (stagger sobre tiempo, valor y posicion de timeline).

## Tecnica (sin codigo)

Un unico reloj de escena reparte un retardo incremental entre N elementos: el orden de entrada sigue el orden de
lectura (o una distancia al origen en una rejilla) y la escena completa dura un total acotado (objetivo <= 1.2 s,
UNKNOWN medido aqui). El estado final es el estado real de la interfaz: la coreografia solo decide cuando se ve, no
que se ve. La escena es cancelable y reversible: si el usuario navega a mitad, la escena salta al estado final y libera
sus temporizadores. Upstream (Anime.js `stagger` + `createTimeline`) lo expresa con posiciones de timeline; la
gramatica es independiente de la libreria y se resuelve igual con CSS `animation-delay` calculado o WAAPI.

## Cuando usar

- Entrada de una seccion con 3 a 12 elementos de peso similar (tarjetas, pasos, logotipos).
- Una sola coreografia por vista, en el punto de lectura que la justifica.

## Cuando NO usar

- Listas largas o datos que el usuario debe leer ya: el retardo acumulado oculta contenido real y fabrica latencia.
- Como indicador de carga o progreso: el escalonado no refleja trabajo real (CDIO-07 sec.12).
- Superficies transaccionales o de trabajo: compite con la tarea.
- Sin un limite total de duracion o sin estado final alcanzable al cancelar.

## Movimiento reducido (equivalente, no ausente)

Todos los elementos aparecen a la vez en su estado final (sin retardo ni desplazamiento); el orden de lectura y el foco
no cambian.

## Soporte de navegador

Universal con CSS/WAAPI; sin dependencia obligatoria.

## Coste de mantenimiento

Bajo si se calcula el retardo en un unico sitio; medio si cada elemento lleva su propio retardo a mano.

## Evidence

`research`: capacidad inventariada de la fuente upstream; no construido aun en un proyecto del Owner.

## Fuentes

- https://github.com/juliangarnier/anime/tree/01b81be1df6843ccfe0a71c0699a746bf740dd77 (Anime.js v4.5.0, MIT; ver `vault/programs/bcap-2/animejs/NOTICE.md`). Solo el patron de diseno; ningun codigo copiado.
