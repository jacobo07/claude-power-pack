---
id: VP-SYN-001
name: Skeleton como promesa estructural
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [dashboard, list-detail, landing]
  excluded_from: [checkout, auth, destructive, form]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: hypothesis
  provenance: Synsation video 7de80ae3 (frames only, wording INFERRED; BCAP2-05)
  purpose: "que la espera de una seccion con geometria final conocida reserve ese espacio y no desplace el contenido al llegar"
---

# VP-SYN-001 — Skeleton como promesa estructural

## Eje

Espera — estructura antes que contenido.

## Tecnica (sin codigo)

Se dibuja la jerarquia final (bloques con las mismas dimensiones reservadas) mientras llega el dato; al resolver, el
contenido ocupa exactamente ese espacio (sin salto de layout). Se elige con `waiting_pattern(..., geometry_known=True)`.

## Cuando usar

- Secciones o paginas cuya forma final se conoce de antemano y cuya carga supera el retardo minimo (300 ms por defecto).

## Cuando NO usar

- Estructura desconocida: el skeleton prometeria campos que pueden no existir.
- Operaciones por debajo del retardo minimo: el destello es un defecto (CDIO-07).
- Acciones locales de un control: va un indicador en linea, no una pagina entera.
- Espera indefinida: un skeleton perpetuo se lee como contenido deshabilitado.

## Movimiento reducido (equivalente, no ausente)

Bloques estaticos sin brillo animado; mismo espacio reservado y mismo anuncio de estado de carga.

## Evidence

`hypothesis`: observado en fotogramas de una fuente; sin construir ni medir CLS aqui.
