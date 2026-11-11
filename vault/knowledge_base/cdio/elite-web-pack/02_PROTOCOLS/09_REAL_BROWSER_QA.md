# Protocolo de verificación en navegador real

Verificar primero los entornos realmente disponibles: Playwright existente, navegador de Claude Code, herramientas de CDIO/CPP, CI o pipeline de captura. No instales nuevas dependencias sin valorar duplicación y permisos.

- Capturar configuración, viewport, navegador, ruta, fecha, idioma, estado de autenticación, datos usados y variante tested.
- Probar desde carga fría: hero, navegación, CTAs, menú, formularios, errores, estado de carga, scroll hasta el footer, enlaces externos y rutas de retorno.
- Probar móvil estrecho y común, tablet y escritorio; modos portrait/landscape cuando aporten valor; zoom y tamaño de fuente aumentado.
- Verificar que acciones sticky no ocultan contenido, que overlays tienen cierre y que existe una ruta alternativa mediante teclado.
- Registrar eventos de consola y red pertinentes sin exponer credenciales ni datos personales.
- Evaluar animaciones con y sin reduced motion; verificar que los efectos no bloquean tareas ni provocan cambios de layout inesperados.
- Medir Web Vitals cuando exista herramienta válida; acompañar números con entorno y limitaciones. Evitar atribuir porcentajes de negocio sin datos.
- Usar capturas antes/después y comparaciones visuales interpretadas por un agente independiente: un diff de píxeles no indica por sí solo calidad.
- Si la herramienta falla, intentar una ruta alternativa ya aprobada. Si ninguna está disponible, anotar NOT_RUN y no inventar pruebas.
