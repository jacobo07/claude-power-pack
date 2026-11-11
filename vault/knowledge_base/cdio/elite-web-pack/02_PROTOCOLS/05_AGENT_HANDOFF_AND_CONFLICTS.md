# Contrato de delegación y handoff entre agentes

## Contrato de entrada mínimo

Identificador de misión; fase; objetivo; restricciones; artefactos de contexto; hechos confirmados; información desconocida; fuentes accesibles; herramientas realmente disponibles; permisos; alcance de archivos; formato de salida; fecha/versión de evidencia; stop rule.

## Respuesta mínima

Estado de tarea; hallazgos con evidencia; propuestas con beneficios y riesgos; cambios ya realizados solo si son verificables; test ejecutado con resultado; limitaciones y métricas no medidas; criterio de aceptación; siguiente propietario; siguiente acción inequívoca.

## Ownership

Una decisión puede discutirse entre roles, pero cada modificación de archivo tiene un único owner simultáneo. Los revisores no reescriben a espaldas del implementador. En conflictos, separar críticas de requisito y preferencias; enviar decisión al CDIO canónico con evidencia.

## Revisión adversarial

La mejor propuesta del diseñador es revisada por CRO y Frontend; la mejor propuesta de CRO es revisada por UX, Psychology y Hospitality; la arquitectura propuesta por IA se contrasta con tareas; la implementación se revisa por Research y Reviewer canónico. El desacuerdo debe generar una decisión o un test, nunca una conversación infinita.

## Recovery

Tras compaction, reanudación o fallo: leer DESIGN.md, el plan aprobado, handoff más reciente y ledger; verificar estado del árbol y ejecutar la siguiente prueba antes de continuar. No asumir que un subagente aún está vivo; comprobar liveness si la herramienta lo soporta. Nunca crear tareas huérfanas ni anunciar un avance que solo exista en memoria de una sesión.
