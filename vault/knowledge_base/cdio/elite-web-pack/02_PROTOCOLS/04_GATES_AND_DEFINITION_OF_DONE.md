# Gates constitutivos y criterios de cierre

**Nota:** estas categorías son un contrato portable para mapear al design_gate, scorer o CDIO Reviewer existentes. No son nombres de endpoint ni un esquema que debas imponer.

## G0 Context & Reality

Objetivo definido; sistema actual descubierto; propietario de datos reconocido; riesgos de integración conocidos; fuente DESIGN.md localizada. Sin G0, no crear módulos paralelos.

## G1 Business Truth & Content

Nada de precios, horarios, disponibilidad, reseñas, fotografías o biografía inventados. Links y destinos verificados. Contenido crítico disponible o bloqueo explícito; sin placeholders en entrega definitiva.

## G2 UX & Information Architecture

Tareas de usuarios cubiertas, acciones principales accesibles, estados de interfaz comprensibles, navegación consistente, flujo móvil efectivo y no-overlap de CTAs. Pruebas de encontrabilidad en tareas clave cuando proceda.

## G3 Brand & Emotional Quality

Consistencia con DESIGN.md; identidad diferenciada y auténtica; dirección de arte y lenguaje apropiados; sin efectos gratuitos o contenido representado falsamente.

## G4 Technical Quality

Build y pruebas relevantes pasan; no errores graves de consola; funcionalidades reales; seguridad y privacidad consideradas; ausencia de enlaces vacíos y regresiones conocidas; componentes existentes reutilizados o extensión justificada.

## G5 Accessibility & Responsiveness

Pruebas con teclado y foco; contraste y semántica cuando sean medibles; targets táctiles adecuados; layouts pequeños/medianos/grandes y zoom; reduced motion; lectura y controles sin obstrucciones. Objetivo mínimo WCAG 2.2 AA o política superior existente.

## G6 Performance & Motion

Medir cuando exista herramienta confiable. Objetivos generales p75: LCP ≤2,5s; INP ≤200ms; CLS ≤0,1. No calificar aprobado numéricamente sin datos. No degradar experiencia de navegación por efectos; fallback para imágenes o vídeo.

## G7 Real Browser Evidence

Pruebas reales de rutas críticas, estados de error, formularios, enlaces, scroll, responsive y consola, con capturas o reportes reproducibles. Si el navegador no está disponible, el gate queda NO VERIFICADO; no inventar un pase.

## G8 Independent Review & Institutional Learning

Revisión independiente por CDIO Reviewer o agente fresco, resolución de defectos críticos, Knowledge Vault/UKDL actualizados cuando exista motivo y baseline ratchet solo por evidencia repetible. Handoff con owner siguiente.

## Estados semánticos

PASS: evidencia suficiente; CONDITIONAL: cobertura parcial y riesgos aceptados de manera explícita; FAIL: defecto comprobado; BLOCKED: falta de dato/herramienta/permiso; NOT_RUN: nunca evaluado. **No equiparar CONDITIONAL, BLOCKED o NOT_RUN a PASS.**

## Política de veto

Veracidad comercial crítica, seguridad, privacidad, transacciones incorrectas, enlaces principales rotos, accesibilidad que impide usar la tarea esencial y bloqueos severos del navegador prevalecen sobre valoración estética. Un sitio visualmente sobresaliente puede fallar.

## Scoring orientativo, solo si no hay scorer existente

Se permite una rúbrica humana de 0–5 por dimensión (UX, CRO, marca, contenido, motion, performance, accesibilidad, ingeniería y evidencia), con fuente y razonamiento. No sustituyas al scorer canónico ni conviertas la cifra en dato científico. Nunca uses un promedio para ocultar defectos bloqueantes.
