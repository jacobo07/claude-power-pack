# SDD-OS PARTE II -- CONTRACTS, INVARIANTS & PROOF-DRIVEN EXECUTION

**Source:** Dataset SDD-OS 1.txt
**Source sha256:** a6c8f6bcd83a8230
**Source line range:** 614-1227 (614 lines)
**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).
**Tiers:** this OS defines FOUR tiers (0 Micro, 1 Standard, 2 Feature/System, 3 Strategic/Platform).

---

PARTE II — CONTRACTS, INVARIANTS & PROOF-DRIVEN EXECUTION

0. El problema oculto de los sistemas Spec-Driven

La mayoría de equipos creen que tienen un problema de implementación.

No lo tienen.

Tienen un problema de especificaciones incompletas.

Pero incluso los equipos que usan PRDs y Architecture Specs siguen produciendo errores.

¿Por qué?

Porque una spec puede estar perfectamente escrita y aun así ser incorrecta.

Puede:

- Contradecirse.
- Omitir casos.
- Romper invariantes.
- Generar efectos secundarios.
- Crear deuda futura.
- Permitir interpretaciones ambiguas.
- Ser imposible de validar.
- Ser imposible de operar.

Por eso aparece una nueva capa obligatoria:

CONTRACT-DRIVEN DEVELOPMENT

Toda spec debe generar contratos verificables.

Y toda ejecución debe demostrar que respeta esos contratos.

---

1. Principio fundamental

Nada se implementa hasta que existan contratos.

PRD sin contratos = documento.

Architecture Spec sin contratos = opinión.

Roadmap sin contratos = lista de deseos.

Implementación sin contratos = apuesta.

Claude Power Pack debe convertir automáticamente cualquier especificación relevante en contratos verificables.

---

2. Contract Extraction Engine

Después de crear PRD y Architecture Spec, Claude Power Pack debe ejecutar automáticamente:

CONTRACT EXTRACTION.

Debe identificar:

- Qué promete el sistema.
- Qué nunca debe ocurrir.
- Qué condiciones siempre deben mantenerse.
- Qué condiciones invalidan la solución.

---

3. Contratos obligatorios

Toda feature Tier 2 o Tier 3 debe generar:

Functional Contracts

Definen comportamiento esperado.

Ejemplo:

"Crear usuario debe producir exactamente un usuario."

No:

- Cero usuarios.
- Dos usuarios.
- Estado intermedio roto.

---

State Contracts

Definen estados válidos.

Ejemplo:

Pedido:

- CREATED
- PAID
- SHIPPED
- DELIVERED

No puede existir:

PAID → CREATED

---

Data Contracts

Definen estructura y significado.

Ejemplo:

email:

- obligatorio
- válido
- único

---

Security Contracts

Definen accesos permitidos.

Ejemplo:

Usuario estándar nunca puede acceder a datos admin.

---

Performance Contracts

Definen límites aceptables.

Ejemplo:

Operación < 500ms.

---

Cost Contracts

Definen límites económicos.

Ejemplo:

No aumentar coste operacional más de 5%.

---

Reliability Contracts

Definen comportamiento bajo fallo.

Ejemplo:

Si API externa falla:

- sistema no se cae
- reintenta
- registra error

---

UX Contracts

Definen experiencia mínima.

Ejemplo:

Usuario siempre recibe feedback.

Nunca puede quedar esperando indefinidamente.

---

Observability Contracts

Definen qué debe poder verse.

Ejemplo:

Toda operación crítica genera logs.

---

4. Invariant Engine

Claude Power Pack debe detectar automáticamente invariantes.

Un invariante es algo que siempre debe ser verdad.

Siempre.

No importa qué ocurra.

---

Ejemplos:

Cuenta bancaria:

saldo >= 0

Marketplace:

pedido entregado ⇒ pedido pagado

Workflow:

step_3 ⇒ step_2 completado

Claude Power Pack:

feature terminada ⇒ acceptance criteria satisfechos

---

5. Invariant Registry

Cada sistema debe mantener un registro vivo de invariantes.

Formato:

INV-001

INV-002

INV-003

...

Cada invariante debe tener:

- descripción
- motivo
- cómo validarlo
- qué rompe si falla

---

6. Global Invariant Discovery

Claude Power Pack debe intentar descubrir invariantes no declarados.

Ejemplo:

Usuario dice:

"quiero un sistema de pagos"

Invariante oculto:

Nunca cobrar dos veces.

Usuario no lo escribió.

Claude debe detectarlo.

---

7. Contradiction Detection Layer

Antes de ejecutar:

Claude Power Pack debe buscar contradicciones.

---

Ejemplo:

Spec A:

Datos eliminados permanentemente.

Spec B:

Historial recuperable.

Ambas no pueden ser ciertas simultáneamente.

---

El sistema debe bloquear ejecución.

---

8. Assumption Registry

Toda implementación se basa en suposiciones.

Normalmente invisibles.

Esto genera bugs.

---

Claude debe listar:

ASS-001

ASS-002

ASS-003

...

Ejemplo:

ASS-001

La API externa tiene uptime aceptable.

ASS-002

Los usuarios tienen conexión.

ASS-003

El proveedor devuelve JSON válido.

---

9. Risk Registry

Toda feature debe producir:

RISK-001

RISK-002

RISK-003

...

Clasificados por:

- probabilidad
- impacto
- detectabilidad

---

10. Unknown Registry

Claude debe declarar explícitamente:

Lo que sabe.

Lo que cree.

Lo que no sabe.

Lo que necesita validar.

---

Categorías:

KNOWN

ASSUMED

UNKNOWN

UNVERIFIED

---

11. Proof-Driven Development

Nueva regla.

No basta con implementar.

Hay que demostrar.

---

Cada requisito debe responder:

¿Cómo demostraríamos que esto funciona?

Antes de escribir código.

---

Si no existe respuesta:

La spec es incompleta.

---

12. Proof Objects

Cada feature debe generar:

Proof of Correctness

¿Por qué creemos que funciona?

---

Proof of Safety

¿Por qué no rompe nada?

---

Proof of Completion

¿Por qué está realmente terminada?

---

Proof of Rollback

¿Por qué podemos revertir?

---

Proof of Observability

¿Por qué detectaríamos problemas?

---

13. Simulation Before Execution

Antes de ejecutar una feature relevante:

Claude debe ejecutar simulación mental obligatoria.

---

Casos:

Happy Path

Edge Cases

Partial Failure

External Failure

User Error

Concurrency

Rollback

Unexpected Inputs

---

14. Spec Stress Testing

Toda spec importante debe ser atacada.

Claude debe asumir el papel de:

- arquitecto rival
- QA extremo
- atacante
- operador
- usuario incompetente
- futuro mantenedor

Y buscar fallos.

---

15. Architecture Court

Nueva entidad obligatoria.

Antes de implementar:

La arquitectura entra en juicio.

---

Debe sobrevivir preguntas como:

¿Por qué esta arquitectura?

¿Por qué no otra?

¿Qué rompe?

¿Qué escala mal?

¿Qué ocurrirá dentro de 2 años?

¿Qué ocurrirá con 10x tráfico?

¿Qué ocurrirá con 100x usuarios?

¿Qué ocurrirá con otro modelo IA?

---

16. Future Maintenance Cost Score

Toda solución recibe puntuación.

FMC Score.

---

Evalúa:

- complejidad
- dependencia externa
- dificultad debugging
- onboarding
- escalabilidad
- observabilidad

---

Claude debe minimizar FMC.

No solo construir.

---

17. Universal Repository Memory

Cada repo debe construir conocimiento acumulativo.

---

Bug encontrado una vez.

Nunca debe enseñarse dos veces.

---

Nuevo patrón descubierto.

Debe convertirse en activo reutilizable.

---

Nueva validación útil.

Debe convertirse en estándar.

---

18. Organizational Learning Engine

Cada feature genera aprendizaje.

Ese aprendizaje debe clasificarse:

- reusable
- local
- dangerous
- mandatory
- future standard

---

19. Completion Tribunal

Ya no existe un único Completion Gate.

Ahora existe un tribunal.

Debe aprobar:

Spec

Contracts

Invariants

Risks

Proofs

Validation

Observability

Rollback

Future Maintenance

---

Si cualquiera falla:

La feature no está terminada.

---

20. Ley Suprema de la Parte II

Una implementación deja de ser considerada correcta cuando:

"parece funcionar".

Y pasa a ser considerada correcta únicamente cuando:

"respeta contratos, conserva invariantes, supera simulaciones, resiste contradicciones, tiene pruebas de funcionamiento y minimiza el coste futuro del sistema."

A partir de esta parte, Claude Power Pack deja de comportarse como un generador de código y empieza a comportarse como un sistema de ingeniería verificable.

CLAUDE POWER PACK — SPEC-DRIVEN DEVELOPMENT OS

