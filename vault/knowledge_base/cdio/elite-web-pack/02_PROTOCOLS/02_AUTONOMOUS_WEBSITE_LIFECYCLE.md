# Ciclo autónomo para creación o rediseño de sitios web

## Etapa 0 — Intake y alcance

Identifica propósito, público, sector, tareas primarias, evento de éxito, identidad y restricciones. Distingue información proporcionada de información verificada. Si hay sitio existente, conserva primero rutas y funciones reales. Determina si la misión exige un plan de aprobación inline o ejecución directa según las reglas del proyecto.

## Etapa 1 — Discovery/Reality

Mapea arquitectura y rutas reales; captura navegador móvil y escritorio; revisa performance, accesibilidad, errores, contenido, datos de negocio y referencias pertinentes. Busca capacidades ya disponibles. El ledger de evidencia registra qué pudo comprobarse y qué no.

## Etapa 2 — Síntesis y desacuerdo experto

Activa A, F, H para estructurar la experiencia; B, C e I para intención/hipótesis/medición; D y E para propuestas visuales y movimiento; G para revisión de viabilidad. Presenta alternativa de mínimo coste, alternativa balanceada y alternativa distintiva cuando el rediseño lo justifique. Critica cada una contra las necesidades reales, sin tratar los estilos como objetivos.

## Etapa 3 — Propuesta y plan inline

Presenta recomendación con trade-offs, orden de secciones, componentes, fuentes de verdad, eventos de conversión, dependencias y pruebas. Usa DESIGN.md, sin documentos de identidad competidores. El plan inline debe ser revisable/aprobable en el flujo humano existente, y mantener respaldo en el plan-file cuando el repositorio lo requiera.

## Etapa 4 — Prototipos y especificación

Crea especificaciones de contenido, componentes, estados, navegación, responsive, animaciones, reduced motion, fallbacks y requisitos de accesibilidad. No inventes assets o datos. Resuelve dudas con prototipos o user tests pequeños antes de una implementación costosa.

## Etapa 5 — Construcción

Entrega cambios incrementales a CCF o ejecutor ya establecido. Microcommits por capacidad. Evita ediciones simultáneas del mismo archivo. Los componentes deben tener comportamiento real, enlaces operativos, estados gestionados y datos confiables. Si faltan assets, usa un fallback neutro honestamente etiquetado en entornos de prueba, no una foto falsa publicada.

## Etapa 6 — Production Reality Gate

Renderiza la versión construida y navega flujos reales. Mide/observa LCP, INP, CLS si la herramienta lo permite, tamaño de pantallas, teclado, reduced motion, navegación, botones, formularios, errores, scroll, traducciones y presentación de contenido. Adjunta evidencia y resultados en vez de afirmar “testeado” sin ejecución.

## Etapa 7 — Gate CDIO

Reviewer canónico independiente compara intención, DESIGN.md, producto implementado y evidencia real. Prioriza defectos críticos sobre rating visual. Si falla: asigna corrección, repite prueba y vuelve a revisar. No maquilles fallos.

## Etapa 8 — Memoria y handoff

Registra errores y patrones, cataloga componentes nuevos y valida que la documentación se puede seguir con un agente nuevo. Propón Baseline Ratchet cuando la regla sea universalizable, comprobada y compatible con sistemas actuales. Entrega veredicto, pendientes, próximo owner y próximos pasos sin depender de memoria de sesión.

## Stop rules

Proseguir si hay tareas verificables no bloqueadas. Parar únicamente por permisos, falta de hecho crítico, riesgo inaceptable, fallos persistentes que requieren nueva estrategia o criterios completos. Ante un bucle de bajo progreso, cambia método. Nunca repitas indefinidamente una exploración sin nueva evidencia.
