---
id: VP-AJS-003
name: SVG Shape Morph (transformacion de una forma en otra)
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
  purpose: "que un icono o ilustracion cambie de forma para comunicar un cambio de estado real sin sustituir el contenido semantico"
---

# VP-AJS-003 — SVG Shape Morph (transformacion de una forma en otra)

## Eje

Movimiento — interpolacion de trazados SVG.

## Tecnica (sin codigo)

Dos trazados con el mismo numero y tipo de segmentos se interpolan punto a punto. Si no son compatibles se normalizan
antes de animar o se hace fundido cruzado; nunca se interpola a ciegas (resultado ilegible). La forma final comunica un
estado que el sistema ya alcanzo. El SVG lleva `role=img` y etiqueta (o `aria-hidden` si es decoracion) y el texto
semantico equivalente existe fuera del SVG. Upstream: `morphTo` de Anime.js; los tres casos de incompatibilidad
(segmentos distintos, subtrazados, arcos) son la lista de comprobacion.

## Cuando usar

- Icono de estado en escaparate (menu a cerrar, reproducir a pausar) donde la transicion refuerza un cambio ya ocurrido.
- Ilustracion de hero con un unico morph de entrada.

## Cuando NO usar

- Como unico canal de un estado: el texto semantico debe existir fuera del SVG.
- Cuando los trazados no son compatibles y no se ha normalizado: produce formas rotas.
- Para simular progreso o exito de una operacion que no ha terminado (CDIO-07 sec.12).
- Superficies de trabajo, formularios o destructivas.

## Movimiento reducido (equivalente, no ausente)

La forma final aparece directamente; el estado y su etiqueta accesible cambian en el mismo instante.

## Soporte de navegador

Interpolacion de `d` por JS universal; la animacion CSS de `d` no es universal (UNKNOWN por navegador).

## Coste de mantenimiento

Medio: cada par de formas requiere comprobar compatibilidad.

## Evidence

`research`: capacidad inventariada de la fuente upstream; no construido aun en un proyecto del Owner.

## Fuentes

- https://github.com/juliangarnier/anime/tree/01b81be1df6843ccfe0a71c0699a746bf740dd77 (Anime.js v4.5.0, MIT; ver `vault/programs/bcap-2/animejs/NOTICE.md`). Solo el patron de diseno; ningun codigo copiado.
