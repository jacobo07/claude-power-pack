# Modelo operativo autónomo de CDIO

## Autoridades y flujo previsto

Product intent → DESIGN.md (única autoridad de identidad) → CDIO/Experience Intelligence (análisis y estándares) → búsqueda en el catálogo de capabilities y componentes existentes → CCF u otro ejecutor verificado → render/navegador real → CDIO Reviewer y gates existentes → evidencia de producción → Knowledge Vault y UKDL → revisión de baseline.

Los nombres aquí proceden del contexto del usuario, no representan rutas de disco ni interfaces verificadas de la versión concreta que se instalará.

## Cuándo convocar cada rol

| Momento | Especialistas principales | Especialistas de revisión |
| --- | --- | --- |
| Intake y diagnóstico | A, F, H | I, B |
| Propuesta comercial | B, C, H | A, I |
| Identidad y composición | D, A, H | E, G |
| Navegación y copy | F, A, H | C, B |
| Motion e interacción | E, D, G | A, I |
| Implementación | G, A | F, E, CDIO Reviewer existente |
| Validación | I, G, A | B, F y los expertos afectados |
| Post-release | B, I, H | CDIO canónico |

Los especialistas se activan por necesidad y por ROI. No inicies nueve procesos para un cambio menor. Evita que roles de solo lectura editen los mismos archivos. En análisis complejo, los roles pueden trabajar simultáneamente y debatir resultados; implementación paralela requiere ownership y coordinación de cambios.

## Niveles de análisis

- EXECUTION: cambio acotado, pruebas conocidas, decisión reversible, sin deuda de arquitectura.
- PLAN: varias opciones o dependencias reales; presentar pasos y pruebas, luego ejecución autorizada.
- ULTRA-PLAN: cambios amplios de marca/arquitectura, múltiples subsistemas, integraciones desconocidas, alto riesgo de irreversibilidad; análisis exhaustivo y aprobación inline antes de actuar.

La selección es explícita con motivo y puede cambiar ante nueva evidencia. No conviertas alta reflexión en excusa para no cerrar tareas.

## Presupuesto cognitivo

Delega bajo demanda, devuelve síntesis en vez de logs completos, reutiliza evidencias, cachea los hallazgos en el sistema existente y establece stop rules. Detén variaciones que no producen mejora medible; identifica nueva hipótesis o cambia de método. Mide progreso por criterios satisfechos, no por tokens gastados.

## Autonomía y permisos

Permitir investigación, implementación local y validación bajo permisos existentes; exigir aprobación para producción, compras, bases de datos reales, credenciales, destrucción irreversible y decisiones de identidad que el usuario reservó para aprobación. El sistema debe poder seguir progresando sobre tareas independientes sin encallar esperando un dato no crítico.
