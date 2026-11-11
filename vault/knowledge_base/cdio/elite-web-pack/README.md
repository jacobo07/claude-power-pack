# CDIO — Elite Web Experience Agent Pack · v1.0.0

**9 agentes expertos de experiencia y conversión + 1 overlay para el CDIO canónico.** Diseñado para incorporarse al Chief Design Intelligence Officer de Claude Power Pack mediante descubrimiento y fusión de capacidades existentes. Idioma de los prompts: español. Especialización: webs universales, con modo específico de restaurante y hospitality.

## Qué incluye

- **9 × SYSTEM.md**, uno por especialista, con criterios compartidos y veto profesional.
- **9 × ROLE.md**, uno por especialista, con misión, método, entregables, revisión y aplicación a restauración.
- **9 subagentes Claude Code opcionales**, con frontmatter estándar y prompts ensamblados para uso tras comprobar colisiones con CDIO.
- **2 overlays de CDIO**, sistema y dirección de misión, que NO deben sobrescribir ciegamente el CDIO real.
- **Protocolos** de Reality Scan, lifecycle, evidencia, gates, handoff, memoria, permisos, enrutamiento y browser QA.
- **Plantillas** de DESIGN.md (solo como esquema, no duplicar autoridad), brief, ledger, componente, informe, plan inline, experimentos, handoff, veredicto y fresh-agent testing.
- **Caso de prueba MYTILUS**, basado en el briefing proporcionado y con todos los datos no verificados claramente etiquetados.
- **Prompt de integración listo para Claude Code**, que exige reconciliar arquitectura y realizar tests antes de declarar instalado.

## Nueve especialistas

| ID | Agente | Autoridad principal |
| --- | --- | --- |
| A | Director UX | Flujos, tareas, claridad y experiencia integral |
| B | CRO Strategist | Embudos, conversiones reales y experimentación comercial |
| C | Consumer Psychologist | Psicología de decisión, confianza y ética |
| D | Art Director | Identidad, dirección visual y fotografía |
| E | Motion Designer | Movimiento, microinteracción, accesibilidad y performance |
| F | Information Architect | Jerarquía, taxonomías, navegación y encontrabilidad |
| G | Frontend Experience Engineer | Implementación, accesibilidad, responsive y tests reales |
| H | Hospitality Brand Strategist | Autenticidad, propuesta de valor y comunicación |
| I | UX Researcher | Evidencia, investigación, tests y calidad de inferencia |

## Lecturas recomendadas

1. **06_INTEGRATION/QUICK_START.md**: flujo de importación.
2. **06_INTEGRATION/INTEGRATION_MAP.md**: arquitectura y qué no duplicar.
3. **06_INTEGRATION/CLAUDE_CODE_INSTALL_PROMPT.md**: instrucciones para que Claude Code realice la fusión.
4. **00_CDIO_ORCHESTRATION/** y **02_PROTOCOLS/**: autonomía, colaboración y gates.
5. **01_agents/** y **04_claude_code_ready/**: fuente por rol y versiones ejecutables opcionales.

## Restricción importante

Este ZIP **no demuestra que se haya instalado en CDIO**. No tengo acceso al repositorio de Claude Power Pack en esta entrega; las APIs, rutas y convenciones del CDIO real se deben descubrir. La integración tiene que conservar CDIO, CDICF, CCF, DESIGN.md, Knowledge Vault, UKDL y gates existentes, sin inventar adaptadores.

Los archivos de la carpeta 04 están basados en la especificación oficial de subagentes de Claude Code (noviembre de 2026), pero no reemplazan al orquestador canónico. Agent Teams es opcional y puede depender de disponibilidad y configuración; más agentes paralelos no implican mejor resultado.

## Qué significa autonomía

Capacidad de investigar, planificar, implementar, probar, corregir, autoevaluar y entregar con mínima intervención dentro de permisos. **No** significa despliegue no autorizado, capacidad de validar datos inexistentes, decisiones comerciales inventadas o eliminación de gates. Si falta una verdad crítica, los agentes deben mantener el progreso, solicitar el dato al owner cuando sea indispensable y proporcionar un handoff inequívoco.

## Precaución con duplicados

La versión por rol (SYSTEM y ROLE) y la versión ensamblada Claude Code corresponden a la misma definición; **no instalar ambas como agentes independientes**. La regla de integración es REUSE → EXTEND → MERGE → CONNECT → BUILD. Un rol nuevo se crea solo cuando se identifica una carencia real.

## Fuentes técnicas oficiales

- Subagentes Claude Code: https://code.claude.com/docs/en/sub-agents
- Agent Teams Claude Code: https://code.claude.com/docs/en/agent-teams
- Ajustes/permisos Claude Code: https://code.claude.com/docs/en/settings

Paquete de prompts y protocolos; no contiene datos personales, credenciales ni fotografías de terceros. Referencias y nombres de servicios del proyecto proceden del contexto del usuario y están sujetos a Reality Scan.
