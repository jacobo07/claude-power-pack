---
id: VP-020
name: Magnetic Drop Zone (zona de arrastre que anticipa)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [form, settings, admin]
  excluded_from: [landing, hero, auth, destructive]
  min_expressiveness: restrained
  min_motion_budget: low
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que el objetivo de un arrastre de archivo se anuncie antes de que el archivo llegue, y que el resultado se lea sin ambiguedad"
---

# VP-020 — Magnetic Drop Zone

## Eje

Interaccion (E2) — objetivo de arrastre con proximidad.

## Tecnica (sin codigo)

La zona escucha el arrastre **a nivel de ventana**, y solo cuando lo arrastrado
son archivos. Con la proximidad del puntero, la zona se desplaza unos pocos
pixeles hacia el y cambia de estado antes de que el archivo entre.

Contrato observado en REF-KITCHEN-001 (OBSERVED):

1. **Tres estados con texto propio**, no solo color: reposo ("suelta un archivo
   aqui"), cerca ("acercalo"), encima ("suelta para anadirlo").
2. **Atraccion acotada**: radio de ~180 px medido desde el borde; desplazamiento
   maximo ~10 px; escala de 1.01 cerca y 1.025 encima. Resorte sin rebote
   visible (rigidez 280, amortiguacion 24, masa 0.65).
3. **Encima, el desplazamiento vuelve a cero**: la zona deja de moverse cuando
   el puntero ya esta dentro, para no perseguir al cursor.
4. **Alternativa nativa**: en reposo la zona es un `button` que abre el selector
   de archivos ("o haz clic para buscar · hasta 20 MB").
5. **Validacion con el nombre del archivo** ("X no es un tipo admitido", "X
   supera 20 MB"), anunciada de forma educada, y la seleccion se vacia.
6. **Estado listo**: icono por tipo, nombre, "+N" si hay varios, tamano; acciones
   Reemplazar y Quitar (con etiqueta accesible que incluye el nombre).
7. **Reinicio robusto**: `drop` y `dragend` en la ventana devuelven la zona al
   reposo aunque el archivo caiga fuera.

## Cuando usar

- Subida de archivos en formularios y ajustes donde arrastrar es el gesto
  habitual (adjuntos, importaciones, avatares).

## Cuando NO usar

- Pantallas tactiles como gesto principal: no hay arrastre de archivos del
  sistema; el boton nativo es la interfaz real y la atraccion no aporta.
- Varias zonas cercanas en la misma vista: los radios se solapan y dos zonas
  compiten por el mismo arrastre.
- Cuando el archivo no se valida en el servidor: la validacion del cliente es
  orientacion, no autorizacion.

## Movimiento reducido (equivalente, no ausente)

Sin desplazamiento, sin escala y sin brillo: se mantienen los tres estados por
texto, borde y fondo. La informacion (cerca / encima / listo / error) es la
misma; solo desaparece el movimiento.

## Soporte de navegador

Universal para HTML Drag and Drop de archivos en escritorio. El resorte requiere
JS (la fuente usa motion/react; cualquier resorte equivalente sirve).

## Contraste y WCAG

El cambio de estado no puede depender solo del color (WCAG 1.4.1): el texto
cambia. El borde de la zona en reposo debe superar 3:1 contra el fondo si es lo
que la identifica (1.4.11). Anillo de foco visible en el boton.

## Coste de mantenimiento

Medio: listeners de ventana que hay que limpiar al desmontar, y reglas de
`accept` (extension, MIME comodin, MIME exacto) que deben coincidir con las del
servidor.

## Evidence

Investigacion: REF-KITCHEN-001 componente 6. Una alternativa de teclado mas alla
del boton nativo es UNKNOWN en la fuente.

## Fuentes

- https://www.dqnamo.com/experiments/magnetic-drop-zone (solo principios; sin licencia declarada).
