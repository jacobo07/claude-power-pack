# Guía de instalación y uso

1. Extraer el ZIP en un espacio de trabajo temporal o directorio de documentación del proyecto.
2. Leer README.md, INTEGRATION_MAP.md, el prompt de instalación y los contratos de evidencia.
3. Dar el ZIP y el prompt de integración a Claude Code dentro del repositorio Claude Power Pack.
4. Permitir que inspeccione el CDIO existente y proponga una fusión, sin copiar a ciegas todos los archivos de subagente.
5. Si no existe ninguna equivalencia en el CDIO canónico, considerar los subagentes Claude Code ya formateados de 04_claude_code_ready; comprobar compatibilidad, herramientas y colisiones de nombres.
6. Probar con una misión de auditoría y otra de creación web. Verificar participación por necesidad, trazabilidad a DESIGN.md, revisión independiente y no-regresión.
7. Solo declarar integrado tras una llamada real de agentes y evaluación de calidad real.

La carpeta 01_agents contiene los nueve pares de SYSTEM.md y ROLE.md originales por rol. El directorio 04 contiene una versión ensamblada de cada par con frontmatter de Claude Code; no necesitas copiar ambos formatos en el runtime.

No se ha conectado ni modificado automáticamente ningún repositorio del usuario. El ZIP es un paquete de integración transferible, no una instalación ejecutada.
