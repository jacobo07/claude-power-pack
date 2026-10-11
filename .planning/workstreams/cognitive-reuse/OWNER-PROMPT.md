# Owner prompt (2026-10-11) — binding sections, verbatim

Source: the Owner's "CLAUDE POWER PACK PRINCIPAL INSTITUTIONAL MEMORY ARCHITECT" prompt, pasted in
the arming pane (session c84deb9e). Sections 9, 10, 15, 16, 17, 24, 26 and 27 are copied verbatim
below. The other sections (context-first, delegation, mode selection, budget, waves) are already
reflected in REQUIREMENTS.md and ROADMAP.md.

## 9. CONTRATO UNIVERSAL DE IDENTIDAD Y REUTILIZACIÓN

Exige que cualquier trabajo cognitivo costoso pueda identificarse de forma estable.

La identidad debe permitir distinguir: La fuente original. Su contenido. Su versión. Sus fragmentos. La transformación aplicada. La versión del extractor. La metodología. La configuración relevante. El contexto de aplicabilidad. El resultado obtenido. La evidencia que valida ese resultado. Sus dependencias. Su estado de vigencia. Su ámbito de autorización.

Investiga qué identificadores y almacenes ya existen y reutilízalos.

Una ruta de archivo no debe convertirse automáticamente en identidad universal de contenido.

Dos repositorios autorizados que contengan fuentes idénticas deben poder reconocer esa equivalencia sin duplicar procesamiento.

Dos fuentes con el mismo nombre pero contenido diferente no deben confundirse.

Dos resultados derivados del mismo contenido mediante transformaciones distintas no deben considerarse automáticamente equivalentes.

Los resultados deben permitir deduplicación sin destruir procedencia.

No confundas múltiples copias de una fuente con múltiples evidencias independientes.

## 10. COGNITIVE WORK REUSE CONTRACT

Define y verifica una propiedad institucional:

Todo resultado cognitivo válido y reutilizable debe poder recuperarse antes de autorizar trabajo equivalente nuevo.

El sistema debe diferenciar: Reutilización exacta. Reutilización parcial. Reutilización condicionada. Resultado insuficiente. Resultado invalidado. Resultado inaccesible. Resultado no autorizado. Resultado inexistente. Estado desconocido.

Nunca conviertas UNKNOWN en una razón implícita para declarar una caché válida.

Tampoco conviertas UNKNOWN en autorización automática para ejecutar una minería extremadamente costosa.

Utiliza una política de decisión basada en coste, evidencia, riesgo y necesidad.

Si existe un resultado equivalente, íntegro, vigente, autorizado y verificable, reutilízalo.

Si el corpus contiene únicamente cambios parciales, procesa exclusivamente las partes afectadas cuando el contrato permita hacerlo con seguridad.

Si la metodología cambió, evalúa qué resultados necesitan realmente regenerarse.

Si aparece una pregunta nueva, recupera primero el conocimiento existente y amplía solamente las dimensiones no cubiertas.

Si la recuperación es insuficiente, documenta por qué y ejecuta la extracción mínima necesaria.

No debe existir una opción silenciosa de volver a minar todo por conveniencia.

## 15. CONSTITUTIVE BASELINE RATCHET

Esta campaña no termina al resolver la ingestión.

Debes convertir las propiedades verdaderamente universales demostradas en estándares de completitud heredables.

Integra las mejoras con UCR-CIF, el Universal Baseline Compiler y el mecanismo Constitutive Baseline Ratchet que realmente esté implementado.

No crees un segundo ratchet.

La nueva capacidad debe distinguir entre: Baseline universal. Baseline de familia de software. Baseline de sistemas de conocimiento. Baseline de ingestión. Baseline de agentes. Baseline de repositorio. Baseline específico de proyecto.

No impongas a software no relacionado una obligación que carezca de sentido.

Pero cuando una feature dependa de conocimiento persistido, reutilizado o derivado, exige los contratos aplicables de identidad, validez, recuperación, evidencia y coste.

EJEMPLO CONCEPTUAL:

Un sistema que ingiere información y después no puede recuperar de forma fiable los resultados anteriormente validados no debe calificarse como completo en su dimensión de memoria.

Un agente autónomo que reproduce trabajo costoso porque perdió el resultado anterior no debe considerarse plenamente resiliente en esa dimensión.

Una infraestructura de conocimiento que almacena fuentes pero no puede alcanzar sus consumidores no debe considerarse operativa.

Estas propiedades deben quedar incorporadas al sistema que evalúa futuras implementaciones.

No basta con actualizar documentación.

Demuestra que una construcción futura hereda el requisito sin que el Owner vuelva a solicitarlo.

El ratchet debe proteger también contra regresiones de baseline.

Un estándar nuevo no se promueve por entusiasmo, sino por evidencia de necesidad, transferibilidad, viabilidad y compatibilidad.

## 16. DONE-GATES Y CERTIFICACIÓN ADVERSARIAL

Diseña pruebas ejecutables sobre los contratos reales.

Como mínimo verifica:

CASO A — PRIMERA INGESTIÓN: Un corpus nuevo se procesa, produce resultados verificables y deja un registro persistente.

CASO B — REPETICIÓN EXACTA: El mismo corpus, con la misma transformación y precondiciones, no provoca una nueva extracción costosa mediante modelos cuando existe un artefacto reutilizable válido.

CASO C — CAMBIO PARCIAL: Modificar una unidad independiente no obliga a repetir el análisis de todas las unidades no afectadas, salvo que las dependencias justifiquen lo contrario.

CASO D — CAMBIO DE EXTRACTOR: El sistema identifica la incompatibilidad, reutiliza lo seguro y regenera lo estrictamente necesario.

CASO E — SEGUNDO REPOSITORIO: Otro repositorio autorizado recupera conocimiento reutilizable sin pagar una segunda minería equivalente.

CASO F — SEGUNDA SESIÓN: Un agente nuevo y sin memoria conversacional recupera el trabajo anterior.

CASO G — COMPACCIÓN: La campaña puede continuar sin perder el estado cognitivo institucional.

CASO H — INTERRUPCIÓN: Un fallo a mitad de ingestión no permite falsos resultados completos y puede recuperarse correctamente.

CASO I — CONFLICTO: Dos fuentes contradictorias no se fusionan como una verdad única.

CASO J — VIGENCIA: Una conclusión invalidada no se entrega como vigente.

CASO K — SEGURIDAD: Un consumidor sin autorización no accede al conocimiento restringido.

CASO L — FALLO DE ENTREGA: Si un hook, inyector o consumidor no recibe la información, el sistema no confunde silencio con éxito.

CASO M — CONCURRENCIA: Dos agentes procesando simultáneamente el mismo corpus no producen estados inconsistentes ni trabajo duplicado evitable.

CASO N — CORRUPCIÓN: Un índice corrupto se detecta y puede recuperarse sin perder la fuente canónica.

CASO O — FUTURA FEATURE: Un proyecto nuevo hereda automáticamente los done-gates aplicables del Constitutive Baseline Ratchet.

CASO P — REPLAY HISTÓRICO: Reproduce el fallo real de 01_Datasets, o el escenario más fiel que permita la evidencia disponible, y demuestra qué mecanismo lo previene ahora.

Incluye pruebas negativas, mutaciones realistas y revisión adversarial independiente.

Una prueba que nunca ejecuta el camino real del consumidor no certifica alcanzabilidad.

Una prueba que evalúa únicamente datos sintéticos favorables no certifica una integración productiva.

No declares PASS cuando exista solamente evidencia parcial.

## 17. PRODUCTION REALITY GATE

Production Reality es obligatorio en cada fase y done-gate.

Antes de declarar una fase terminada, demuestra: El componente existe. Está integrado en su propietario correcto. Es alcanzable desde su consumidor real. El consumidor recibe la información correcta. La información tiene vigencia y permisos correctos. Los fallos se clasifican correctamente. Los tests relevantes pasan. Las pruebas negativas detectan el defecto que deben detectar. El resultado es reproducible. La documentación coincide con el comportamiento. El cambio está versionado. El mecanismo puede ser descubierto por un agente futuro.

Aplica el Contrato de Realidad: Cero botones vacíos. Cero placeholders presentados como funcionalidad. Cero integraciones aparentes. Cero 401 inesperados en flujos autorizados. Cero desconexiones ocultas entre frontend, CLI, agentes, hooks, backend y almacenamiento.

Estas comprobaciones se ejecutarán sobre las superficies a las que realmente apliquen, sin fabricar interfaces innecesarias para satisfacerlas.

Kernel vMAX-NULL-ERROR activo.

UNKNOWN, INCONCLUSIVE, UNVERIFIED y BLOCKED no son PASS.

## 24. CRITERIOS FINALES DE DONE

No declares COMPLETE AND PROVEN hasta demostrar lo siguiente:

1. La causa raíz del incidente está identificada con evidencia suficiente, o los límites de reconstrucción histórica están documentados honestamente.
2. Existe un mecanismo efectivo para evitar repetir minería cognitiva costosa cuando los resultados anteriores siguen siendo válidos.
3. La reutilización exacta del corpus verificado no provoca nuevas llamadas de extracción mediante modelos.
4. Los cambios parciales utilizan invalidación y reprocesamiento proporcionados al impacto real.
5. Los artefactos tienen identidad, procedencia, versión, vigencia y condiciones de uso.
6. La memoria persiste entre sesiones.
7. Los consumidores autorizados pueden descubrirla y utilizarla.
8. El camino de ejecución real está probado, no solamente documentado.
9. Los fallos de entrega, corrupción y validación no se confunden con éxito.
10. La infraestructura no provoca filtraciones de conocimiento entre proyectos.
11. Se han medido los costes y beneficios disponibles sin inventar cifras.
12. Los tests adversariales y de regresión aplicables pasan.
13. Production Reality Gate pasa en todas las superficies cubiertas.
14. Los cambios están incorporados en micro-commits trazables.
15. Knowledge Vault contiene las incidencias y aprendizajes correspondientes.
16. UKDL incorpora los patrones universalizables sin duplicar doctrina.
17. Constitutive Baseline Ratchet ha incorporado y verificado la herencia de los nuevos estándares justificados.
18. Una futura feature del tipo aplicable puede descubrir y cumplir esos contratos sin intervención manual del Owner.
19. Un agente fresco puede recuperar la arquitectura, operar el sistema y verificarlo sin conocer esta conversación.
20. No quedan residuos, cambios sin atribuir, afirmaciones de PASS sin pruebas ni migraciones incompletas ocultas.

El criterio ejecutable definitivo deberá identificarse y fijarse en el plan aprobado mediante los comandos reales de pruebas y certificación del repositorio.

No inventes nombres de test ni comandos que todavía no existen.

Si un requisito permanece bloqueado, informa del estado parcial real.

No rebajes los done-gates para obtener un cierre satisfactorio.

## 26. HANDOFF FINAL OBLIGATORIO

Termina con dos niveles de handoff.

OWNER SUMMARY:
- Qué se encontró.
- Qué se corrigió.
- Qué quedó demostrado.
- Cuánto trabajo y coste se evitó, si es medible.
- Qué está pendiente.
- Qué requiere autorización externa.
- Estado real de completitud.

ENGINEERING HANDOFF:
- PANE actual. Proyecto. Campaña. Sprint. Wave. Modo utilizado. Branch. Worktree. HEAD.
- Micro-commits. Archivos y módulos relevantes. Evidencia producida.
- Tests ejecutados. Tests no ejecutados. Resultados adversariales. Production Reality Gate.
- Estado de memoria persistente. Estado de recuperación federada.
- Costes medidos. Token budget consumido.
- Knowledge Vault actualizado. UKDL actualizado. Constitutive Baseline Ratchet actualizado.
- Product Delta. Intelligence Delta.
- Riesgos. Incertidumbres. Retractaciones. Bloqueos.
- Próximo pane. Próxima tarea exacta. Próximo modo recomendado. Instrucción precisa de reanudación.

Debe quedar claro qué pane produjo el handoff y cuál debe continuar.

No inventes el número de pane si el runtime no lo proporciona.

## 27. KILL-SWITCHES

Prohibido:
- Insertar código en la respuesta al Owner cuando no lo ha solicitado.
- Construir otro Knowledge Vault sin demostrar la necesidad.
- Construir otro Graphify.
- Construir otro ratchet.
- Crear sistemas paralelos de verdad institucional.
- Reprocesar corpus idénticos sin justificación.
- Confundir índices con conocimiento consolidado.
- Confundir existencia de un módulo con ejecución real.
- Confundir presencia de un hook con entrega efectiva.
- Confundir documentación con capacidad.
- Confundir tests unitarios con validación end-to-end.
- Confundir silencio con aprobación.
- Fabricar ahorro económico.
- Declarar pruebas no ejecutadas como PASS.
- Elevar una regla local a universal sin evidencia.
- Consumir tokens masivamente en análisis redundante.
- Crear loops infinitos.
- Saltarse límites de autorización.
- Sobrescribir trabajo de otros agentes.
- Desactivar Production Reality para completar una fase.
- Rebajar el baseline para cerrar la campaña.
- Terminar únicamente porque una fase haya acabado, si la campaña autónoma aprobada todavía tiene trabajo ejecutable dentro de su presupuesto.
