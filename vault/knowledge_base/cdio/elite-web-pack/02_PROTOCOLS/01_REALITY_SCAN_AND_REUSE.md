# Reality Scan y reutilización obligatoria

Antes de instalar o activar este paquete dentro de CDIO:

1. Localiza el CDIO canónico real y sus roles, prompts, scorer, review gate y design_index; si el repositorio expone rutas como modules/cdio o cdio-core, verifica su contenido, vigencia y ownership.
2. Localiza CDICF, CCF, capability runtime, DESIGN.md, estándares, Knowledge Vault, UKDL, Baseline Ratchet, pruebas E2E, screenshot/browser capture, herramientas de motion y AGENT TEAMS disponibles.
3. Para cada uno de los nueve perfiles compara cobertura existente, herramientas, autoridad, límites y contratos. Clasifica resultado como REUSE, EXTEND, MERGE, CONNECT o BUILD.
4. Prioriza usar la skill/agente canónico. No renombres ni sustituyas agentes de CDIO ya activos sin una migración expresa. En caso de solapamiento, extrae criterios nuevos y intégralos en el rol existente; no dejes prompts duplicados compitiendo.
5. Determina dónde pueden residir prompts y cómo se descubren, en vez de suponer que el runtime usa una carpeta concreta. La versión portable del ZIP conserva referencias; las definiciones en la carpeta 04 son un puente opcional confirmado por documentación de Claude Code, no un reemplazo de las interfaces CDIO.
6. Define equivalencias entre resultados semánticos del paquete y contratos reales de CDIO. No escribas campos inventados en módulos con schemas desconocidos.
7. Inspecciona permisos y opciones de equipo disponibles. Para escritura simultánea define ownership; para revisiones usa el reviewer canónico.
8. Produce un informe de integración con ubicación real de cada cambio, diff, riesgos, tests y evaluación de regresión.

**Regla:** ninguna conclusión basada solo en el nombre de un archivo. Verifica importación real, convocatoria real y resultado real con una prueba fresh-agent antes de declarar integrado.
