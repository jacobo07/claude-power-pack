# Mapa de integración de CDIO — sin interfaces inventadas

## Decisión

El pack NO tiene un instalador que escriba a ciegas sobre CDIO. Contiene prompts fuente editables y nueve archivos de subagente Claude Code usando el formato documentado. La fusión con CDIO y la selección de runtime se realiza tras inspección de código.

## Arquitectura observada en el contexto previo del proyecto (pendiente de revalidar)

- Chief Design Intelligence Officer (CDIO): cerebro de juicio y gate.
- CDIO Core/Reviewer/Standards Librarian, scorer, design_gate, design_index: agentes y mecanismos a buscar, no duplicar.
- CCF: ejecución/construcción de componentes cuando se compruebe vigente.
- CDICF: governance de dependencias cuando exista.
- DESIGN.md: autoridad canónica de diseño; no crear copias rivales.
- Knowledge Vault / UKDL: documentación factual y patrones generalizados.
- Baseline Ratchet / Fresh-agent test: promoción controlada de estándares.
- Production Reality Gate: evidencia en navegador real, no pase simulado.

## Estrategia por perfil

1. Buscar un agente existente con el mismo expertise. Si existe y su rol actual es compatible: MERGE su sistema/role prompt y reglas, sin duplicarlo.
2. Si la capacidad existe parcialmente en otra capa: EXTEND mediante contrato canónico, manteniendo owner y archivos originales.
3. Si un especialista nuevo es realmente necesario: BUILD un subagente o rol en la ubicación y formato verificados.
4. CONNECT con el orquestador mediante el mecanismo descubierto. No inventar eventos o nombres de hooks.
5. Probar con una misión simple, una misión de construcción y una de revisión adversarial. Verificar que el CDIO Reviewer no se puede eludir y que hay evidencia real.

## Adaptador Claude Code listo para estudiar

`04_claude_code_ready/.claude/agents/` contiene nueve archivos Markdown con frontmatter estándar y system prompt completo. En un repositorio Claude Code convencional pueden cargarse como subagentes si se copian tras resolver duplicidades; no se han instalado en ningún repositorio en este trabajo.

## Herramientas

Los agentes de investigación tienen acceso limitado a lectura local y búsqueda web incorporada cuando está disponible; no poseen permiso de edición por su definición portable. El agente G dispone de herramientas de edición y shell con permisos del host, pero debe usar el ejecutor canónico en vez de trabajar por una vía alternativa. Las herramientas especializadas del repositorio se incorporan solo tras descubrir sus nombres reales.

## Integridad de importación

Asegurar que el nombre, descripción y rol sean únicos; evitar colisiones; no reemplazar configuraciones del CDIO existente. Probar delegación, alcance, lectura de DESIGN.md, retorno de findings y compatibilidad con el flujo de gates.

Fuentes técnicas consultadas para el puente opcional: https://code.claude.com/docs/en/sub-agents y https://code.claude.com/docs/en/agent-teams (consultadas en noviembre de 2026). La disponibilidad real de Agent Teams debe comprobarse: puede ser experimental, dependiente de versión y configuración.
