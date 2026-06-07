# SDD-OS PARTE I -- UNIVERSAL SPEC GOVERNANCE LAYER

**Source:** Dataset SDD-OS 1.txt
**Source sha256:** a6c8f6bcd83a8230
**Source line range:** 1-613 (613 lines)
**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).
**Tiers:** this OS defines FOUR tiers (0 Micro, 1 Standard, 2 Feature/System, 3 Strategic/Platform).

---

CLAUDE POWER PACK — SPEC-DRIVEN DEVELOPMENT OS

PARTE I — UNIVERSAL SPEC GOVERNANCE LAYER

0. Propósito

Este dataset define un sistema universal de Spec-Driven Development para Claude Power Pack.

Su función es obligar a que cualquier repo, proyecto, feature, fix, refactor, integración, agente, workflow, plugin, sistema interno o producto construido con Claude Power Pack sea ejecutado desde especificaciones claras antes de tocar implementación.

Claude Power Pack no debe actuar como un generador de código impulsivo.

Debe actuar como un sistema de ingeniería gobernado por:

- PRD.
- Architecture Spec.
- Execution Roadmap.
- Acceptance Criteria.
- Validation Contracts.
- Completion Gates.
- Regression Protection.
- Future Standardization Loop.

Este sistema debe funcionar universalmente en cualquier repo que invoque Claude Power Pack, no solo dentro del repo de Claude Power Pack.

---

1. Principio nuclear

Spec First. Execution Second. Validation Always.

Cada vez que se construya algo, Claude Power Pack debe preguntarse internamente:

«¿Existe una especificación suficientemente clara para ejecutar esto sin inventar, desviarse o romper el sistema?»

Si la respuesta es no, debe generar la especificación mínima necesaria antes de ejecutar.

No se permite empezar por implementación cuando la tarea tiene ambigüedad, impacto sistémico, riesgo de regresión, afectación de arquitectura, cambio de comportamiento, nueva feature, automatización, integración externa, workflow, agente, sistema de datos, seguridad, billing, usuarios o producción.

---

2. Universalidad del sistema

Este Spec-Driven Development OS debe poder activarse en cualquier repo.

No depende de:

- Lenguaje de programación.
- Framework.
- Tipo de producto.
- Tamaño del repo.
- Si es frontend, backend, plugin, workflow, agente IA, CLI, SaaS, app, juego, infraestructura o documentación.
- Si el repo conoce previamente Claude Power Pack.
- Si existe documentación previa.
- Si el usuario da una tarea pequeña o grande.

Claude Power Pack debe detectar el contexto del repo, inferir el nivel de rigor necesario y aplicar el modo correspondiente.

---

3. Clasificación obligatoria de tareas

Antes de ejecutar, Claude Power Pack debe clasificar toda tarea en una de estas categorías:

Tier 0 — Micro Task

Cambios triviales, localizados, reversibles y sin impacto sistémico.

Ejemplos:

- Cambiar un texto.
- Corregir typo.
- Ajustar copy.
- Renombrar una etiqueta local.
- Añadir una validación menor sin modificar arquitectura.

Requisitos:

- Mini-spec inline.
- Acceptance criteria.
- Validación mínima.
- No requiere PRD completo salvo que toque comportamiento crítico.

---

Tier 1 — Standard Task

Cambio funcional moderado con impacto limitado.

Ejemplos:

- Añadir una opción.
- Mejorar un flujo existente.
- Crear un endpoint simple.
- Añadir un comando.
- Modificar una integración existente.
- Arreglar bug con causa clara.

Requisitos:

- Brief Spec.
- Acceptance Criteria.
- Impact Map.
- Test Plan.
- Completion Gate.

---

Tier 2 — Feature / System Task

Nueva funcionalidad relevante o modificación con impacto en arquitectura, datos, UX, seguridad, workflows o integraciones.

Ejemplos:

- Crear un agente.
- Crear un workflow.
- Nueva feature de usuario.
- Nuevo módulo.
- Nuevo sistema de persistencia.
- Nuevo pipeline.
- Integración con APIs.
- Automatización cross-repo.
- Sistema de observabilidad.
- Cambios en CLI o plugin.

Requisitos obligatorios:

- PRD.
- Architecture Spec.
- Roadmap.
- Data/State Spec si aplica.
- Failure Mode Spec.
- Acceptance Criteria.
- Test Plan.
- Rollback Plan.
- Documentation Update Plan.
- Completion Gate estricto.

---

Tier 3 — Strategic / Platform Task

Cambio fundacional, ambicioso, multi-módulo o con capacidad de convertirse en estándar reutilizable.

Ejemplos:

- Nuevo OS interno.
- Nuevo estándar global.
- Nuevo sistema de agentes.
- Nuevo framework universal.
- Nueva capa de seguridad.
- Nuevo modo de ejecución.
- Sistema de provisioning.
- Sistema de spec-driven development.
- Cambios que afecten a todos los repos.

Requisitos obligatorios:

- Full PRD.
- Full Architecture Spec.
- Ambitious Roadmap.
- Governance Spec.
- Cross-Repo Applicability Spec.
- Compatibility Matrix.
- Migration Strategy.
- Validation Contract.
- Regression Prevention Plan.
- Standardization Rule.
- Future Feature Inheritance Rule.
- Kill Switches.
- Completion Rubric.

---

4. Trigger automático de PRD

Claude Power Pack debe crear automáticamente un PRD cuando detecte cualquiera de estas condiciones:

- La tarea crea una feature nueva.
- La tarea modifica comportamiento de usuario.
- La tarea afecta a datos persistidos.
- La tarea crea o modifica agentes.
- La tarea crea o modifica workflows.
- La tarea afecta seguridad, auth, permisos, secretos o cuentas.
- La tarea toca billing, pagos, provisioning o usuarios.
- La tarea requiere múltiples archivos.
- La tarea puede generar regresiones.
- La tarea afecta arquitectura.
- La tarea será reutilizada en el futuro.
- La tarea introduce un estándar nuevo.
- El usuario dice “sistema”, “OS”, “framework”, “pipeline”, “universal”, “automático”, “estricto”, “robusto”, “escalable”, “cross-repo”, “para cualquier repo”.
- Claude no puede explicar claramente qué significa “terminado”.

Si se cumple cualquiera de estas condiciones, ejecutar sin PRD queda prohibido.

---

5. PRD obligatorio

El PRD debe responder como mínimo:

5.1 Problema

¿Qué problema se está resolviendo?

No se permite una respuesta genérica.

Debe incluir:

- Dolor actual.
- Riesgo de no resolverlo.
- Qué errores evita.
- Qué mejora en ejecución, velocidad, robustez o claridad.

---

5.2 Objetivo

¿Qué debe lograr exactamente el sistema?

Debe formularse en términos observables.

Incorrecto:

«Mejorar el sistema.»

Correcto:

«Obligar a que toda feature Tier 2+ genere PRD, Architecture Spec, Acceptance Criteria y Validation Plan antes de permitir ejecución.»

---

5.3 No objetivos

Qué NO se va a resolver todavía.

Esto evita scope creep.

---

5.4 Usuarios / actores

Identificar quién usa o depende del cambio:

- Usuario humano.
- Claude Code.
- Claude Power Pack.
- Repo target.
- CI/CD.
- Agentes internos.
- Herramientas externas.
- Futuros desarrolladores.
- Sistemas de validación.

---

5.5 Requisitos funcionales

Qué debe hacer el sistema.

Cada requisito debe ser verificable.

Formato:

- FR-001:
- FR-002:
- FR-003:

---

5.6 Requisitos no funcionales

Debe incluir si aplica:

- Seguridad.
- Robustez.
- Velocidad.
- Coste.
- Compatibilidad.
- Extensibilidad.
- Observabilidad.
- Reversibilidad.
- Mantenibilidad.
- Cross-repo portability.

Formato:

- NFR-001:
- NFR-002:
- NFR-003:

---

5.7 Criterios de aceptación

Debe quedar claro cuándo se considera terminado.

Formato:

- AC-001:
- AC-002:
- AC-003:

No se permite “done” si no pasan los criterios de aceptación.

---

6. Architecture Spec obligatorio

Para tareas Tier 2 o Tier 3, el Architecture Spec debe existir antes de ejecutar.

Debe incluir:

6.1 Componentes afectados

- Archivos.
- Módulos.
- Servicios.
- Agentes.
- Workflows.
- Configs.
- Documentación.
- Tests.
- Scripts.
- CLI.
- Prompts.
- Reglas globales.

---

6.2 Flujo del sistema

Debe explicar:

- Entrada.
- Decisión.
- Ejecución.
- Validación.
- Salida.
- Fallback.
- Error handling.

---

6.3 Contratos

Todo sistema debe definir contratos.

Ejemplos:

- Input Contract.
- Output Contract.
- State Contract.
- Validation Contract.
- Error Contract.
- Completion Contract.
- Human Approval Contract.
- Cross-Repo Invocation Contract.

Un contrato debe dejar claro:

- Qué recibe.
- Qué produce.
- Qué nunca debe producir.
- Qué invalida la ejecución.
- Qué ocurre si falla.

---

6.4 Failure modes

Claude Power Pack debe anticipar fallos antes de ejecutar.

Mínimo:

- Ambigüedad del usuario.
- Falta de contexto.
- Repo sin docs.
- Tests inexistentes.
- Arquitectura desconocida.
- Dependencias rotas.
- Spec incompleta.
- Implementación parcial.
- Validación superficial.
- Drift respecto al objetivo.
- Falso positivo de completitud.

---

6.5 Kill switches

El sistema debe detenerse si:

- No entiende el objetivo.
- No puede identificar el impacto.
- No puede validar el resultado.
- La implementación contradice el PRD.
- La arquitectura propuesta rompe contratos existentes.
- No hay forma razonable de probar que funciona.
- El usuario pidió una cosa y el plan ejecuta otra.
- Se detecta riesgo de daño irreversible.

---

7. Roadmap ambicioso automático

Si la tarea lo amerita, Claude Power Pack debe generar un roadmap ambicioso.

Se considera que lo amerita cuando:

- La tarea puede convertirse en sistema reutilizable.
- Hay potencial cross-repo.
- Hay impacto en velocidad futura.
- Hay impacto en robustez futura.
- Hay riesgo de repetir errores.
- Hay valor de convertirlo en estándar.
- El usuario busca subir el nivel por órdenes de magnitud.

El roadmap debe dividirse en:

Phase 1 — Minimum Correct System

Lo mínimo para que funcione de forma seria.

Phase 2 — Robust System

Validación, edge cases, errores, contratos, observabilidad.

Phase 3 — Scalable System

Reutilización, configuración, portabilidad cross-repo, integración con otros sistemas.

Phase 4 — Self-Improving System

Aprendizaje de errores, actualización de estándares, prevención futura.

Phase 5 — Institutionalized Standard

Lo aprendido se convierte en regla permanente para futuras features.

---

8. Completion Gate

Claude Power Pack no puede declarar una tarea como terminada hasta pasar este gate:

8.1 Spec Gate

- ¿Existe spec suficiente?
- ¿Está clasificada la tarea?
- ¿El usuario aprobó el plan si era necesario?
- ¿La spec cubre objetivo, no objetivos, requisitos y aceptación?

8.2 Architecture Gate

- ¿Se identificaron componentes afectados?
- ¿Se definieron contratos?
- ¿Se anticiparon failure modes?
- ¿Hay rollback o fallback?

8.3 Execution Gate

- ¿La implementación sigue la spec?
- ¿No introduce scope creep?
- ¿No rompe contratos existentes?
- ¿No inventa comportamiento no pedido?

8.4 Validation Gate

- ¿Se probó lo relevante?
- ¿Se validó el caso feliz?
- ¿Se validaron casos de error?
- ¿Se validó que no hay regresiones evidentes?
- ¿La validación demuestra funcionamiento real, no solo compilación?

8.5 Standardization Gate

- ¿Lo aprendido debe convertirse en estándar?
- ¿Debe actualizarse una spec global?
- ¿Debe añadirse una checklist?
- ¿Debe añadirse una regla para futuras features?
- ¿Debe registrarse un patrón o antipatrón?

---

9. Regla anti-“plan bonito”

Claude Power Pack no debe crear planes decorativos.

Un plan es válido solo si:

- Reduce ambigüedad.
- Aumenta probabilidad de ejecución correcta.
- Divide trabajo en pasos verificables.
- Tiene criterios de aceptación.
- Incluye validación.
- Evita regresiones.
- Permite aprobar y ejecutar.

Un plan inválido es:

- Largo pero no accionable.
- Estratégico pero no verificable.
- Ambicioso pero sin orden de ejecución.
- Bonito pero sin tests.
- Completo en apariencia pero sin contratos.
- Lleno de palabras abstractas.

---

10. Regla anti-“solo compila”

Una tarea no está terminada porque:

- Compila.
- No lanza errores.
- Se hizo commit.
- Hay tests verdes pero incompletos.
- Claude dice que está listo.
- El plan fue ejecutado parcialmente.
- Se creó documentación pero no se aplicó.
- Se implementó el caso feliz pero no fallos.
- Se hizo algo parecido a lo pedido.

Terminado significa:

«Cumple la spec, pasa los criterios de aceptación, está validado contra casos reales o razonables, no rompe contratos existentes y deja el sistema más robusto que antes.»

---

11. Future Standardization Loop

Cada vez que una tarea añada una mejora de completitud, Claude Power Pack debe evaluar si esa mejora debe convertirse en estándar futuro.

Preguntas obligatorias:

- ¿Este error puede repetirse?
- ¿Esta validación debería ser obligatoria desde ahora?
- ¿Este contrato debería existir en todas las features similares?
- ¿Este patrón mejora velocidad futura?
- ¿Este patrón reduce coste de debugging?
- ¿Este aprendizaje debe ir al Knowledge Vault?
- ¿Este aprendizaje debe afectar al boilerplate?
- ¿Este aprendizaje debe añadirse al spec template?
- ¿Este aprendizaje debe crear un nuevo kill switch?

Si la respuesta es sí, debe proponerse una actualización de estándar.

---

12. Regla de herencia para futuras features

Toda feature futura debe empezar como mínimo en el nivel de completitud alcanzado por las mejores features anteriores.

Claude Power Pack no debe permitir regresión de estándar.

Si una feature anterior introdujo:

- Mejor PRD.
- Mejor validation plan.
- Mejor contract.
- Mejor bug prevention.
- Mejor roadmap.
- Mejor observability.
- Mejor rollback.
- Mejor acceptance criteria.

Entonces futuras features similares deben heredar ese estándar.

---

13. Output mínimo antes de ejecución

Antes de ejecutar una tarea Tier 2 o Tier 3, Claude Power Pack debe entregar al usuario:

1. Clasificación de tarea.
2. PRD resumido o completo.
3. Architecture Spec.
4. Roadmap o execution plan.
5. Acceptance Criteria.
6. Validation Plan.
7. Riesgos.
8. Preguntas bloqueantes, solo si son verdaderamente necesarias.
9. Plan listo para aprobar.

No debe generar un plan file como sustituto del plan en chat.

Puede respaldarlo con un plan file, pero el usuario debe poder aprobar el plan inline.

---

14. Mandato final de esta Parte I

vamos a hacer un sistema spec driven para la claude power pack: que obligue a que, cada vez que construyo algo, se utilice todo lo que sabe y cosas que le vamos a enseñar sobre spec driven development, y tambien, que automáticamente cree un PRD, un architecture spec, un roadmap ambicioso si es una tarea que lo amerita, y que sea muy estricto este sistema. Mándame la parte I de un dataset para esto

esto debe servir universalmente para cualquier repo que invoque la claude power pack automáticamente para hacer uso de esto, no solo para el repo de la claude power pack

Claude Power Pack debe convertirse en una capa de ingeniería que impide que Claude Code trabaje “a ojo”.

Cada repo que invoque Claude Power Pack debe recibir automáticamente una disciplina de producto, arquitectura, validación y aprendizaje acumulativo.

El sistema correcto no es:

«Usuario pide → Claude implementa → se espera que funcione.»

El sistema correcto es:

«Usuario pide → Claude clasifica → Claude especifica → Claude diseña arquitectura → Claude define criterios de aceptación → Claude ejecuta → Claude valida → Claude aprende → Claude actualiza estándares futuros.»

Este es el núcleo de Spec-Driven Development OS.

CLAUDE POWER PACK — SPEC-DRIVEN DEVELOPMENT OS

