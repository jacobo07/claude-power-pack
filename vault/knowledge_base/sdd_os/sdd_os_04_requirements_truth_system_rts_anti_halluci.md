# SDD-OS PARTE IV -- REQUIREMENTS TRUTH SYSTEM (RTS) & ANTI-HALLUCINATION ENGINEERING

**Source:** Dataset SDD-OS 1.txt
**Source sha256:** a6c8f6bcd83a8230
**Source line range:** 2164-3005 (842 lines)
**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).
**Tiers:** this OS defines FOUR tiers (0 Micro, 1 Standard, 2 Feature/System, 3 Strategic/Platform).

---

PARTE IV — REQUIREMENTS TRUTH SYSTEM (RTS) & ANTI-HALLUCINATION ENGINEERING

0. El siguiente problema que nadie resuelve

Incluso con:

- PRDs.
- Architecture Specs.
- Contracts.
- Invariants.
- Engineering Graphs.

Todavía existe una fuente masiva de errores.

La más peligrosa de todas.

---

No es un bug.

No es una mala arquitectura.

No es una mala implementación.

---

Es construir correctamente algo incorrecto.

---

Es decir:

La spec parece perfecta.

La arquitectura parece perfecta.

Los contratos parecen perfectos.

La ejecución parece perfecta.

---

Pero el sistema construido no es lo que realmente se necesitaba.

---

Esto ocurre porque casi todos los equipos tienen:

False Requirements

Requisitos incorrectos.

Missing Requirements

Requisitos faltantes.

Assumed Requirements

Requisitos inventados.

Stale Requirements

Requisitos que dejaron de ser verdad.

---

La Parte IV crea:

REQUIREMENTS TRUTH SYSTEM (RTS)

---

1. Principio fundamental

Nueva ley.

---

Claude Power Pack nunca debe asumir que un requisito es verdadero.

Debe demostrarlo.

---

Todo requisito entra inicialmente en estado:

UNVERIFIED

---

2. Requirement Lifecycle

Todo requisito pasa por estados.

---

PROPOSED

↓

DISCOVERED

↓

ANALYZED

↓

VERIFIED

↓

IMPLEMENTED

↓

VALIDATED

↓

MONITORED

↓

EVOLVED

↓

DEPRECATED

---

Si un requisito no alcanza VERIFIED:

No puede convertirse en implementación.

---

3. Requirement Confidence Score

Cada requisito recibe:

RCS (Requirement Confidence Score)

---

0-20

Especulación.

---

20-40

Hipótesis.

---

40-60

Probable.

---

60-80

Alta confianza.

---

80-100

Validado.

---

Claude debe mostrar internamente qué requisitos tienen baja confianza.

---

4. Source-of-Truth Hierarchy

No todas las fuentes valen lo mismo.

---

Orden obligatorio:

1. Realidad observable

2. Datos de producción

3. Comportamiento de usuarios

4. Contratos existentes

5. Specs aprobadas

6. Documentación

7. Conversaciones

8. Suposiciones

9. Inferencias

10. Alucinaciones

---

Nunca se permite que un nivel inferior contradiga uno superior.

---

5. Requirement Provenance

Cada requisito debe responder:

¿De dónde salió?

---

Formato:

REQ-024

Origin:

User Request

Evidence:

Message X

Confidence:

87

---

Si no existe origen:

No existe requisito.

---

6. Requirement Evidence Layer

Todo requisito importante debe tener evidencia.

---

Ejemplo:

"Los usuarios quieren exportar CSV."

---

¿Basado en qué?

---

Feedback.

Tickets.

Métricas.

Encuestas.

Entrevistas.

Observación.

---

Si no existe evidencia:

Marcar como hipótesis.

---

7. Assumption Promotion System

Las suposiciones no pueden quedarse ocultas.

---

Toda suposición debe ser promovida a:

- Evidencia.
- Validación.
- Eliminación.

---

No existe estado permanente de "creo que".

---

8. Missing Requirement Discovery

Claude debe buscar requisitos ausentes.

---

Ejemplo:

Sistema de login.

---

Requisitos visibles:

- Registrarse.
- Iniciar sesión.

---

Requisitos ocultos:

- Recuperar contraseña.
- Verificar email.
- Cerrar sesión.
- Expirar sesiones.
- Revocar acceso.

---

Deben emerger automáticamente.

---

9. Requirement Contradiction Engine

Detectar requisitos incompatibles.

---

Ejemplo:

REQ-101

Eliminar permanentemente datos.

---

REQ-119

Permitir restaurar datos eliminados.

---

Bloqueo inmediato.

---

10. Requirement Ambiguity Scanner

Palabras prohibidas sin definición.

---

Rápido.

Seguro.

Escalable.

Robusto.

Moderno.

Flexible.

Optimizado.

Inteligente.

---

Claude debe exigir definición operacional.

---

11. Operational Definitions

Cada concepto importante debe convertirse en algo medible.

---

Incorrecto:

"Debe ser rápido."

---

Correcto:

P95 < 300ms.

---

Incorrecto:

"Debe ser seguro."

---

Correcto:

Ningún usuario estándar puede acceder a recursos admin.

---

12. Requirement Atomicity

Los requisitos deben ser indivisibles.

---

Incorrecto:

"Crear sistema de pagos seguro y escalable."

---

Correcto:

REQ-001

Procesar pagos.

REQ-002

Gestionar reembolsos.

REQ-003

Mantener latencia.

REQ-004

Cumplir contratos de seguridad.

---

13. Requirement Dependency Graph

Cada requisito debe conocer:

Qué necesita.

Qué bloquea.

Qué habilita.

---

Se convierte en un grafo.

---

14. Requirement Blast Radius

Cambiar un requisito puede afectar muchos sistemas.

---

Claude debe calcular:

RBR (Requirement Blast Radius)

---

Antes de aceptar cambios.

---

15. Requirement Drift Detector

Nueva amenaza.

---

Código puede desviarse.

Ya lo sabemos.

---

Pero también:

Los requisitos pueden desviarse de la realidad.

---

Ejemplo:

PRD de hace 2 años.

Usuarios actuales distintos.

---

RTS debe detectarlo.

---

16. Requirement Expiration

Todo requisito tiene fecha de envejecimiento.

---

Claude debe preguntarse:

¿Sigue siendo cierto?

---

No asumir permanencia.

---

17. User Intent Reconstruction

El usuario suele describir soluciones.

No problemas.

---

Ejemplo:

"Necesito un dashboard."

---

Posible realidad:

Necesita visibilidad.

No dashboard.

---

Claude debe reconstruir intención.

---

18. Problem Truth Layer

Antes de diseñar solución:

Validar problema.

---

Problema incorrecto.

↓

Solución perfecta.

↓

Fracaso perfecto.

---

19. Requirement Simulation Engine

Cada requisito debe sobrevivir simulaciones.

---

Caso ideal.

Caso límite.

Caso inesperado.

Caso malicioso.

Caso futuro.

Caso de escala.

---

20. Requirement Stress Testing

Claude debe intentar destruir requisitos.

---

Preguntas:

¿Por qué existe?

¿Qué pasa si desaparece?

¿Quién depende de él?

¿Sigue teniendo sentido?

¿Es realmente necesario?

---

21. Zombie Requirement Detection

Requisitos muertos.

---

Siguen en docs.

Nadie los usa.

---

Siguen generando complejidad.

---

Deben eliminarse.

---

22. Phantom Requirement Detection

Requisitos inexistentes.

---

Todo el mundo cree que existen.

Nunca fueron aprobados.

Nunca fueron especificados.

---

Deben eliminarse.

---

23. Requirement Health Score

Cada requisito recibe:

RHS

---

Evalúa:

Claridad.

Verificabilidad.

Trazabilidad.

Actualidad.

Dependencias.

Observabilidad.

---

24. Requirement Portfolio Management

Los requisitos son activos.

---

Claude debe gestionarlos como cartera.

---

Añadir.

Eliminar.

Fusionar.

Dividir.

Deprecar.

Actualizar.

---

25. Requirement Governance Board

Antes de cambios importantes:

Claude debe convocar revisión interna.

---

Roles simulados:

Product.

Architecture.

Operations.

QA.

Security.

Maintenance.

Future Developer.

---

26. Requirement Economics

Cada requisito tiene coste.

---

Construcción.

Testing.

Operación.

Mantenimiento.

Complejidad.

---

Claude debe calcular ROI.

---

27. Requirement Debt

Nueva categoría.

---

No toda deuda es técnica.

---

Existe deuda de requisitos.

---

Requisitos:

- ambiguos
- contradictorios
- obsoletos
- incompletos

---

Deben registrarse.

---

28. Truth Preservation Protocol

Cuando un requisito cambia:

Claude debe preservar:

- motivo original
- decisión original
- evidencia original

---

Nunca perder contexto.

---

29. Requirement Compiler

Antes de pasar al Spec Compiler:

Los requisitos deben compilar.

---

Errores posibles:

Missing Evidence

Missing Definition

Missing Validation

Contradiction

Ambiguity

Missing Owner

Missing Acceptance

Missing Traceability

---

Si falla:

No hay spec.

---

30. Ley Suprema de la Parte IV

La mayoría de proyectos fracasan porque construyen correctamente algo que nunca debió construirse.

Por tanto:

Claude Power Pack debe asumir que los requisitos son sospechosos hasta que se demuestre lo contrario.

A partir de esta parte, el sistema deja de preguntar:

«"¿Cómo construimos esto?"»

Y empieza preguntando:

«"¿Estamos seguros de que esto es realmente lo que debe construirse?"»

Solo después se permite arquitectura, implementación y ejecución.

CLAUDE POWER PACK — SPEC-DRIVEN DEVELOPMENT OS

