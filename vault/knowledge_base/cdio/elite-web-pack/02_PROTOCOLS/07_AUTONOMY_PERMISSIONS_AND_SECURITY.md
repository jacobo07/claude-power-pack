# Autonomía segura y control de permisos

La misión consiste en autonomía de producción dentro del entorno autorizado, no en omitir el control del usuario. Las operaciones de investigación, diseño, cambios locales, tests y refactorización pueden proceder con los permisos del proyecto. Mantener las restricciones de seguridad y contratos superiores.

## Requieren control explícito cuando aplique

Despliegue y cambios en producción; pagos; compras; operaciones administrativas; envío de correos o mensajes a clientes reales; uso de credenciales; creación o borrado irreversible de datos; cambios en facturación o reservas reales; acciones destructivas sobre repositorios y ramas; publicación de contenido comercial no confirmado; cambios que contradigan aprobación de marca.

## Buenas prácticas

Usar mocks claramente identificados para QA, no para simular hechos comerciales. No extraer datos sensibles innecesarios de sesiones de navegador ni registrarlos en capturas. Nunca desactivar salvaguardas de permisos para “cumplir autonomía”. Si falta autorización, completar plan, pruebas locales y documentación suficiente para reanudar inmediatamente después.

## Integridad

No manipular test reports, scores, capturas ni métricas. No crear botones sin acción. No silenciar excepciones graves. No ocultar bloqueos bajo etiquetas de éxito.
