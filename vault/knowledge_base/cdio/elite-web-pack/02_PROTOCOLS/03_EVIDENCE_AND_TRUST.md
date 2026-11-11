# Contrato de evidencia

## Etiquetas obligatorias

- VERIFIED: una observación respaldada por una fuente adecuada y reproducible. Indicar origen, hora si cambia, herramienta y alcance.
- OBSERVED: visto en un vídeo, captura o prueba concreta, sin garantizar que se generalice a otros contextos.
- INFERRED: inferencia razonable explicada con supuestos y señales indirectas.
- PROPOSED: idea que aún no se ha implementado o comprobado.
- UNKNOWN: dato requerido pero no disponible.
- MEASURED: número proveniente de una medición reproducible (método y muestra incluidos).

Toda afirmación crítica lleva una de estas etiquetas y un pointer a evidencia, no un porcentaje inventado. Las estimaciones se marcan ESTIMATE y no se confunden con MEASURED.

## Evidencia admisible

Fuente de sitio o repositorio verificado, respuesta documentada del propietario, test funcional real, captura fechada con viewport, documento de analítica confiable, estudio de usuario debidamente descrito o benchmark externo con URL y fecha. El material promocional de terceros no prueba desempeño ni resultados de conversión.

## Problemas críticos

No declarar VERIFIED por una captura de otro sitio o una referencia visual; no atribuir superposiciones del navegador o sistema operativo al CSS de la web; no confundir un clic con una transacción; no deducir disponibilidad comercial de una imagen. En pruebas con datos personales, minimizar captura y almacenamiento.

## Conciliación

Si dos fuentes discrepan, distinguir fechas y autoridad; resolver con dueño del dato o marcar incertidumbre. No tomar la fuente visualmente más atractiva como verdadera por defecto.

## Handoff

Toda propuesta técnica de alto impacto debe incluir evidencia de antes, hipótesis de después, criterio verificable y dato de post-test. Si no se pudo probar, el resultado se comunica como pendiente y no como pasado.
