# Aprendizaje institucional, UKDL y Baseline Ratchet

1. Buscar el Knowledge Vault, UKDL, biblioteca de componentes y baseline verificables. No crear una segunda base de conocimientos.
2. Para cada bug o fricción documentar: síntoma, contexto, pasos, evidencia, causa raíz, corrección, pruebas y alcance. Evitar duplicados de fallos conocidos.
3. Separar aprendizaje local del producto y patrón universal. El hecho de que un sitio necesite un footer más corto no demuestra una regla global sobre todos los footers.
4. Convertir patrones universales comprobados en reglas, detectores, revisores, test cases o componentes reutilizables cuando sea viable; vincular su provenance y fechas.
5. Valorar el coste de mantenimiento de cada regla y su riesgo de generar falsos positivos. No incrementar reglas de forma indiscriminada.
6. Usar una prueba de fresh-agent para validar que la práctica se entiende sin depender de la sesión original y que no rompe un proyecto diferente.
7. Solo después solicitar/ejecutar la ascensión al baseline a través de mecanismos descubiertos y permisos existentes. Conservar evidencia de aceptación y rollback.
8. Cuando el almacenamiento no exista o la escritura falle, registrar una acción pendiente concreta y nunca afirmar que la memoria permanente se actualizó.
