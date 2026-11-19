---
id: VP-SYN-002
name: Control pendiente en linea
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [dashboard, list-detail, settings, form]
  excluded_from: [destructive]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: hypothesis
  provenance: Synsation video 7de80ae3 (frames only, wording INFERRED; BCAP2-05)
  purpose: "que el trabajo local de un control se muestre en ese control, sin bloquear ni reiniciar el resto de la pagina"
---

# VP-SYN-002 — Control pendiente en linea

## Eje

Espera — localidad.

## Tecnica (sin codigo)

El indicador vive dentro del control que espera y conserva su etiqueta; el ancho del control no cambia; la activacion
repetida queda bloqueada solo si duplicar es inseguro; el resto de la pagina sigue operativo. El final se reconcilia con
el resultado real del sistema (exito o error visible).

## Cuando usar

- Una accion acotada (enviar, guardar, marcar) con latencia sobre el retardo minimo.

## Cuando NO usar

- Latencia por debajo del retardo minimo: no mostrar nada.
- Acciones irreversibles o criticas: requieren estado de liquidacion explicito, no solo un spinner.
- Cuando se afecta a toda la pagina: eso es skeleton o progreso, no un control.

## Movimiento reducido (equivalente, no ausente)

Indicador estatico (texto "Guardando...") con el mismo aria-busy y el mismo bloqueo de duplicados.

## Evidence

`hypothesis`: observado en fotogramas; sin construir aqui.
