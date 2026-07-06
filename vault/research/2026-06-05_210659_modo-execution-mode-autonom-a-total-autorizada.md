The prompt is a research-report task with a fixed deliverable, not a code or planning task. The "EXECUTION MODE" line is just the framing — my job is to synthesize the research learnings into a detailed markdown report. No skill or subagent applies here; I'll write it directly.

Two distinct topics surfaced in the research, so I'll structure the report to cover both clearly.

---

# Informe de Investigación: Autonomía Supervisada en Dos Frentes — Tesla FSD en Europa y los Modos de Autonomía Total en CLIs de Codificación con IA

**Fecha:** 2026-06-05
**Modo:** Execution — síntesis completa de hallazgos
**Alcance:** Dos dominios convergentes bajo el concepto de "autonomía supervisada": (1) la aprobación regulatoria del Tesla FSD (Supervisado) en la UE, y (2) los modos de bypass de permisos en las CLIs de codificación con IA (Claude Code, Codex, Gemini).

---

## Resumen Ejecutivo

Ambos dominios investigados comparten un patrón estructural idéntico y revelador: **la delegación de control con una capa de supervisión retenida como salvaguarda legal y técnica**. Tesla etiqueta deliberadamente su producto como "FSD (Supervisado)" — el paréntesis no es cosmético, es la transferencia explícita de responsabilidad legal al conductor. De forma análoga, el "Auto Mode" de Claude Code no es autonomía ciega: introduce un clasificador independiente que supervisa cada acción, conservando una capa de juicio externa al agente que ejecuta.

La tesis central que emerge: **la "autonomía total" comercialmente viable en 2026 no es ausencia de supervisión, sino reubicación de la supervisión** — del humano-en-el-bucle a un sistema de vigilancia paralelo (cámara interior en Tesla; clasificador reasoning-blind en Claude Code), con el humano retenido como respaldo legal de último recurso.

---

## PARTE I — Tesla FSD (Supervisado) en Europa

### 1. El Hito Regulatorio: Holanda como Cabeza de Puente

El **RDW** (Rijksdienst voor het Wegverkeer, la autoridad holandesa de vehículos) otorgó la **homologación de tipo** (type approval) para el **Tesla FSD Supervised (Nivel 2)** el **10 de abril de 2026**, convirtiendo a los Países Bajos en el **primer país de la UE** en aprobar el sistema.

| Parámetro | Detalle |
|---|---|
| Autoridad | RDW (Países Bajos) |
| Fecha de aprobación | 10 de abril de 2026 |
| Versión de software | FSD v14 / versión 2026.3.6 |
| Hardware prioritario | HW4 primero; HW3 + FSD Computer a continuación |
| Tiempo de pruebas previo | ~18 meses |
| Ruta regulatoria | "Exención nacional" (national exemption), regla por regla |
| Nivel SAE | Nivel 2 (asistencia, NO autónomo) |

El detalle estratégico clave: Tesla **no esperó a la armonización a nivel UE**. En su lugar, utilizó una **ruta de exención nacional regla por regla** a través del RDW, una autoridad históricamente receptiva a la innovación en homologación. Esto le permitió obtener un punto de apoyo regulatorio que después podría propagarse mediante el principio de reconocimiento mutuo de la UE.

### 2. El Efecto Dominó: Reconocimiento Mutuo en la UE

La aprobación holandesa desencadenó un **despliegue en cascada** apoyado en el reconocimiento mutuo entre estados miembros:

| Orden | País | Autoridad | Estado / Fecha |
|---|---|---|---|
| 1.º | Países Bajos | RDW | Aprobado 10-abr-2026 |
| 2.º | Lituania | — | Aprobado 20-may-2026 |
| 3.º | Estonia | — | Aprobado 29-may-2026 |
| 4.º (esperado) | Bélgica | — | Mediados de junio 2026 |
| En preparación | Grecia | — | Legislación en curso |
| En revisión | Alemania | KBA | Pendiente — May/Jun → Q3/otoño 2026 |
| En revisión | Francia | DREAL | Pendiente |
| En revisión | Italia | MIT | Pendiente |

El patrón es deliberado: Tesla aseguró primero los **mercados pequeños y ágiles** (Países Bajos, Lituania, Estonia) cuyas autoridades pueden moverse rápido, construyendo un cuerpo de precedentes de homologación antes de enfrentarse a los **reguladores grandes y conservadores** — el KBA alemán, la DREAL francesa y el MIT italiano — que permanecen bajo revisión hasta Q3/otoño de 2026.

**Horizonte de armonización plena:** una aprobación armonizada a nivel UE mediante el voto del **Comité Técnico de Vehículos de Motor (TCMV)** de la UE está fijada como objetivo en torno al **Q1 2027**.

### 3. Validación de Campo: La Prueba de Xataka

El sistema fue probado de forma independiente por **Xataka** en **Ámsterdam y Haarlem**, cubriendo **~150 km**:

- **Consumo medio:** ~124 Wh/km (en un Tesla Model Y).
- **Veredicto de nivel:** Confirmado como **Nivel 2**, NO Nivel 4 autónomo.
- **Énfasis del etiquetado:** El paréntesis "(Supervisado)" subraya que la **responsabilidad legal es totalmente del conductor**, quien debe mantener los ojos en la carretera y manos/pies listos para intervenir.

### 4. Arquitectura Técnica del FSD Europeo

Un hallazgo crítico: el FSD europeo **no es un port directo** de la versión estadounidense. Es una versión **adaptada (tailored)** para las condiciones locales:

**Adaptaciones específicas:**
- Reglas de tráfico, señales de tráfico y tipos de vehículo locales.
- Redes neuronales **compiladas con MLIR** (Multi-Level Intermediate Representation).
- Manejo de **rotondas tipo turbo / holandesas** (turbo/Dutch roundabouts) — una geometría vial específicamente europea.

**Dominio Operativo de Diseño (ODD) restringido:**
- Limitado a **autopistas / arterias principales** únicamente.
- **Se desconecta** (disengages) en niebla densa, lluvia o nieve intensa.

**Marco regulatorio:**
- Gobernado por la **Regulación 171 de la ONU** (Driver Control Assistance Systems).
- Homologación de tipo **UNECE**.

### 5. Plataforma de Hardware y Obsolescencia Programada

El acceso a las capacidades plenas está estratificado por hardware, lo que plantea cuestiones de **obsolescencia programada**:

| Hardware | Lanzamiento | Acceso FSD | Garantía de actualización |
|---|---|---|---|
| **HW4** | 2023 | FSD v14 | Sí |
| **HW3** | Anterior | Limitado a FSD v12 | **Sin garantía** de actualización futura |

Los propietarios de vehículos HW3 quedan efectivamente **estancados en FSD v12** sin garantía de migración a v14 — un caso de manual de obsolescencia programada que probablemente generará fricción con los clientes que pagaron por la promesa de "Full Self-Driving" años atrás.

### 6. Estructura de Precios y Cambio de Modelo Comercial

| Modalidad | Precio (Europa) | Notas |
|---|---|---|
| Pago único | **7.500 €** | Indefinido; **Tesla terminó esta opción en la mayor parte de Europa en mayo 2026** |
| Suscripción estándar | **99 €/mes** (≈3 €/día) | Activación/baja flexible |
| Suscripción con descuento EAP | **49 €/mes** | Para titulares del Enhanced Autopilot previo |

El movimiento estratégico más significativo: **Tesla finalizó la compra única de FSD en la mayor parte de Europa en mayo de 2026**, forzando una transición hacia el modelo de **ingresos recurrentes por suscripción**. Esto convierte el FSD de un activo de capital (CapEx para el cliente) en un flujo de ingresos perpetuo para Tesla, y reduce la fricción de adopción inicial a costa del coste de propiedad a largo plazo.

### 7. Las Afirmaciones de Seguridad y la Sombra de la Publicidad Engañosa

Tesla respalda el lanzamiento con afirmaciones de seguridad agresivas, sobre una base de **14.000 millones de km recorridos con FSD activado**:

**Afirmaciones de Tesla:**
- **Siete veces menos** colisiones importantes y menores.
- Con adopción masiva, potencial de reducir el **80% de la siniestralidad de EE. UU.**

**Contexto de los datos base (NHTSA 2023):**
- 40.000 muertes y 2,4 millones de lesiones anuales en EE. UU.
- Proyección de Tesla: salvar hasta **32.000 vidas** y evitar **1,9 millones de lesiones**.

**Mecanismo de cumplimiento de la atención:**
- La **cámara interior** vigila la atención del conductor.
- Puede **bloquear el FSD durante 2 días** si el conductor se despista repetidamente — un mecanismo de castigo conductual para forzar la supervisión.

**La sombra reputacional:**
- **Elon Musk prometió autonomía de Nivel 4 desde 2016** sin cumplirlo.
- Esto ha generado acusaciones de **publicidad engañosa**, actualmente bajo investigación.

> **Nota analítica (interpretación):** Las afirmaciones de "siete veces menos colisiones" deben tratarse con escepticismo metodológico. Los kilómetros con FSD activado se concentran desproporcionadamente en **autopistas** (el ODD del sistema), que son intrínsecamente los entornos de conducción más seguros por kilómetro. Comparar la tasa de siniestralidad de FSD-en-autopista contra la media nacional de TODOS los entornos (incluyendo intersecciones urbanas, conducción nocturna y vías secundarias) es una comparación sesgada por selección. La cifra de "80% de reducción" es, en el mejor de los casos, una extrapolación especulativa que asume una transferencia perfecta del rendimiento del ODD restringido a todos los entornos de conducción.

---

## PARTE II — Modos de Autonomía Total en CLIs de Codificación con IA

### 8. El Panorama Comparativo: Tres Filosofías de Bypass

A marzo de 2026, las tres principales CLIs de codificación con IA exponen distintas banderas de autonomía total, cada una reflejando una filosofía de seguridad diferente:

| CLI | Bandera de autonomía total | Nombre oficial / técnico | Filosofía |
|---|---|---|---|
| **Claude Code** | `--dangerously-skip-permissions` | Modo `bypassPermissions` | Solo `.git`/`.claude` siguen pidiendo confirmación |
| **Codex CLI** | `--yolo` | `--dangerously-bypass-approvals-and-sandbox` | Dos ejes independientes |
| **Gemini CLI** | `--approval-mode yolo` | Modo YOLO | Restringido deliberadamente a flag de CLI |

### 9. Claude Code: Seis Modos de Permiso

Claude Code ofrece la granularidad más alta con **seis modos de permiso**, ciclables a mitad de sesión mediante **Shift+Tab**:

1. `default` — confirmación estándar.
2. `acceptEdits` — acepta ediciones de archivos automáticamente.
3. `plan` — modo de planificación sin ejecución.
4. `auto` — ejecución sin prompts con clasificador de supervisión (ver §10).
5. `dontAsk` — no preguntar.
6. `bypassPermissions` — bypass total (solo `.git`/`.claude` siguen protegidos).

### 10. El Diferenciador: Claude Code "Auto Mode"

El **Auto Mode** de Claude Code es **único entre las tres CLIs**. No es un bypass ciego — es **autonomía supervisada**, el análogo computacional exacto del FSD (Supervisado) de Tesla.

**Cronología de despliegue:**

| Hito | Fecha | Versión |
|---|---|---|
| Lanzamiento como research preview | 24 de marzo de 2026 | v2.1.83 |
| Disponibilidad General (GA) | 16 de abril de 2026 | v2.1.111 (eliminó el flag obsoleto `--enable-auto-mode`) |

**Requisitos:** Plan Team/Enterprise/API, la API de Anthropic, y modelos **Sonnet 4.6 o Opus 4.6**. Disponible en GA a través de Max/Team/Enterprise/API.

**Principio operativo — Evaluación de la brecha de intención (intent-gap):**
> "Todo lo que el agente elige por su cuenta no está autorizado hasta que el usuario diga lo contrario."

La confirmación debe ser **explícita, no implícita**. Crucialmente, **las instrucciones de CLAUDE.md cuentan como intención del usuario** y son leídas por el clasificador.

### 11. Arquitectura de Defensa de Dos Capas

El Auto Mode reemplaza los prompts de permiso humano con una **defensa ML de dos capas** (autoría de **John Hughes en Anthropic**):

**Capa de entrada (input-layer) — Sonda de inyección de prompts del lado del servidor:**
- Escanea las salidas de herramientas: lecturas de archivos, fetches web, salida de shell.
- Inyecta advertencias cuando detecta intentos de inyección de prompts.

**Capa de salida (output-layer) — Clasificador de transcripción:**
- Corre sobre **Sonnet 4.6**.
- Evalúa cada acción mediante un **flujo de 3 niveles (tiers)**:
  - **Tier 1:** Allowlist de solo-lectura (read-only).
  - **Tier 2:** Ediciones de archivos dentro del proyecto.
  - **Tier 3:** Clasificador para acciones de shell/web/externas/subagentes.

### 12. El Clasificador "Reasoning-Blind" — Diseño Antiadversarial

El detalle de diseño más sofisticado: el clasificador de transcripción es **deliberadamente "ciego al razonamiento" (reasoning-blind)**.

**Qué ve y qué NO ve:**
- **VE:** solo los mensajes del usuario y las llamadas de herramienta desnudas del agente (nombre + input).
- **NO VE:** el texto del propio asistente (las "explicaciones" de Claude) ni los resultados de herramientas.

**Por qué importa:** Esta amputación es una defensa antiadversarial deliberada con dos efectos:
1. El agente **no puede "convencer al clasificador"** de una mala llamada mediante racionalizaciones persuasivas.
2. El contenido inyectado vía salida de herramientas **no puede alcanzar al clasificador**.

**Pipeline de dos etapas:**

| Etapa | Función | Parámetros | Métricas |
|---|---|---|---|
| **Etapa 1** | Filtro rápido de un token sí/no | `max_tokens` 64, `stop_sequence` `</block>`, ajustado a "errar del lado de bloquear" | 8,5% FPR / 6,6% FNR sobre acciones excesivas reales |
| **Etapa 2** | Razonamiento chain-of-thought solo sobre ítems marcados | `max_tokens` 4096 | FPR del pipeline completo: **0,4%**; FNR sube a **17%** sobre acciones excesivas reales (5,7% FNR sobre exfiltración sintética, n=1000) |

**Detalles de eficiencia y fail-safe:**
- La Etapa 2 es **casi totalmente cache-hit** desde la Etapa 1, ya que solo difiere la instrucción final.
- Salida no parseable del clasificador → **falla cerrado (bloquea)**.

### 13. El Modo de Fallo Residual: Mala Interpretación del Alcance del Consentimiento

El **17% de FNR honesto** (falsos negativos) tiene una causa raíz identificada: **mala interpretación del alcance del consentimiento (consent-scope misjudgment)**.

El clasificador **identifica correctamente el peligro** (force-push, eliminación) pero **acepta erróneamente "evidencia con forma de aprobación"** como cobertura del radio de explosión (blast radius) de la acción. Es decir: el sistema ve que algo fue aparentemente aprobado y asume que la aprobación cubre más de lo que realmente cubre.

### 14. Defensas en Profundidad del Auto Mode

Para mitigar el modo de fallo de §13, el Auto Mode incorpora múltiples defensas:

1. **Despojo de reglas amplias:** Al entrar en Auto Mode, **elimina las reglas allow amplias** que conceden ejecución arbitraria de código (`Bash(*)`, `python*`, `node*`, `npx`, `ssh`, `eval`, reglas de Agent) — de modo que el clasificador **vea** los comandos dañinos en lugar de que pasen pre-aprobados.
2. **Evaluación de impacto real mediante wrappers:** decodifica base64, ensambla scripts, y trata las **cadenas `&&` como una sola acción** — evaluando el impacto en el mundo real, no la superficie sintáctica.
3. **Verificación de subagentes en dos puntos:** los subagentes se comprueban **en la delegación Y en el retorno**.
4. **Backstop de denegación:** detiene el modelo tras **3 denegaciones consecutivas o 20 totales** (escalando a un humano, o terminando en modo headless `-p`).

### 15. Validación Académica Independiente

El sistema ha sido evaluado de forma independiente por un paper de stress-test en arXiv:
- **Referencia:** arXiv 2604.04978v1
- **Título:** "Measuring the Permission Gate"
- **Autores:** Zimo Ji, Zongjie Li, Shuai Wang et al.

Esta evaluación externa otorga credibilidad de tercera parte a las métricas de FPR/FNR reportadas por Anthropic.

### 16. Codex CLI y Gemini CLI: Modelos Contrastantes

**Codex CLI — Control en dos ejes:**

| Eje | Opciones |
|---|---|
| Política de aprobación | untrusted, on-request, never |
| Modo de sandbox | read-only, workspace-write, danger-full-access |

- `--full-auto` combina **workspace-write + on-request** (un punto medio razonable).
- `--yolo` / `--dangerously-bypass-approvals-and-sandbox` es el bypass total.

**Gemini CLI — Restricción deliberada:**
- El modo `yolo` está **intencionalmente restringido a un flag de CLI** — **no puede establecerse como predeterminado** en `settings.json`. Esto es una decisión de diseño de seguridad: obliga a una elección consciente por sesión.

**Controles de administración empresarial:**

| CLI | Mecanismo de bloqueo administrativo |
|---|---|
| Gemini CLI | `security.disableYoloMode: true` |
| Claude Code | `permissions.disableBypassPermissionsMode: "disable"` (managed settings) |

### 17. Cuadro Comparativo Síntesis de las Tres CLIs

| Dimensión | Claude Code | Codex CLI | Gemini CLI |
|---|---|---|---|
| Flag de autonomía total | `--dangerously-skip-permissions` | `--yolo` | `--approval-mode yolo` |
| Modo supervisado intermedio | **`auto` (clasificador ML)** | `--full-auto` (workspace-write + on-request) | — |
| Granularidad de modos | 6 modos | 2 ejes × 3 opciones c/u | Flag-only |
| Defensa antiadversarial | Clasificador reasoning-blind de 2 etapas | Sandbox por ejes | Restricción a flag de sesión |
| Bloqueo empresarial | `disableBypassPermissionsMode` | (por configuración de sandbox) | `disableYoloMode` |
| Validación académica | arXiv 2604.04978v1 | — | — |

---

## PARTE III — Síntesis Transversal y Observaciones Estratégicas

### 18. El Patrón Unificador: Supervisión Reubicada, No Eliminada

El paralelismo entre ambos dominios es estructural y profundo:

| Concepto | Tesla FSD (Supervisado) | Claude Code Auto Mode |
|---|---|---|
| Capa de supervisión | Cámara interior + conductor | Clasificador reasoning-blind |
| Mecanismo de castigo/freno | Bloqueo de FSD por 2 días | Backstop: 3 consecutivas / 20 totales |
| Responsabilidad de último recurso | El conductor (legal) | El humano (escalación) |
| Naturaleza del etiquetado | "(Supervisado)" explícito | "Auto" ≠ autónomo total |
| Dominio operativo restringido | Autopistas/arterias (ODD) | Tiers 1-3, allowlists |
| Fallo en condiciones adversas | Desconexión en niebla/nieve | Fail-closed en output no parseable |

Ambos sistemas materializan la misma tesis: **la autonomía comercialmente desplegable en 2026 es autonomía con un supervisor de circuito paralelo retenido como respaldo**, no autonomía verdaderamente sin supervisión.

### 19. Contraste de Filosofías de Seguridad (Especulación Analítica)

> **Nota: la siguiente es una interpretación analítica, flagueada como especulación.**

Existe una asimetría interesante en cómo cada dominio gestiona el riesgo:

- **Tesla** externaliza la responsabilidad al humano (el conductor es legalmente responsable) mientras maximiza la percepción de capacidad ("Full Self-Driving"). El supervisor (cámara) sirve para **proteger a Tesla legalmente**, no principalmente para mejorar la seguridad.
- **Claude Code** internaliza la responsabilidad en el sistema (el clasificador bloquea activamente) mientras es conservador en la percepción de capacidad ("Auto", no "Autonomous"). El supervisor (clasificador) sirve para **proteger al usuario**, errando del lado de bloquear (8,5% FPR aceptado).

Esta divergencia refleja sus respectivos perfiles de responsabilidad: el daño de un coche autónomo es físico, irreversible y litigable; el daño de un agente de código es (generalmente) reversible vía control de versiones, lo que permite a Anthropic adoptar una postura de "fail-closed" más agresiva sin paralizar el producto.

### 20. Soluciones y Ángulos No Considerados (Proactividad)

**Para el dominio Tesla/regulatorio:**
- La ruta de **exención nacional regla por regla** es un patrón replicable que otros fabricantes (Mobileye, Waymo, BYD) podrían explotar — la cabeza de puente holandesa establece un precedente que erosiona la ventaja de la armonización UE-céntrica.
- El cambio a suscripción pura (fin del pago único) crea un **vector de riesgo regulatorio**: si un regulador grande (KBA) revoca o restringe la aprobación, Tesla tiene una base de suscriptores activos a quienes debe gestionar reembolsos/migraciones, a diferencia del modelo de pago único.

**Para el dominio de las CLIs:**
- El diseño **reasoning-blind** del clasificador de Claude Code es una innovación de seguridad transferible: cualquier sistema agente que quiera prevenir "jailbreak por auto-racionalización" debería amputar el razonamiento del agente de la vista del supervisor. Es un principio de diseño generalizable más allá del código.
- El **17% de FNR por consent-scope misjudgment** sugiere una mejora futura: un "ledger de consentimiento" estructurado donde cada aprobación del usuario declare explícitamente su blast-radius (p. ej., "apruebo esta eliminación SOLO para este archivo"), reduciendo la ambigüedad que el clasificador malinterpreta.

---

## Conclusión

Los dos frentes investigados —la homologación europea del Tesla FSD (Supervisado) y los modos de autonomía total de las CLIs de codificación con IA— convergen en una lección de 2026: **la autonomía total, tal como se comercializa, es un eufemismo para autonomía supervisada por un circuito paralelo**. Tesla obtuvo su cabeza de puente regulatoria en Holanda el 10 de abril de 2026 mediante una astuta ruta de exención nacional, desencadenando un dominó de reconocimiento mutuo (Lituania, Estonia, Bélgica inminente) mientras los grandes reguladores deliberan hasta Q3 2026 y la armonización plena se proyecta a Q1 2027 — todo manteniendo al conductor como responsable legal de último recurso bajo el paréntesis "(Supervisado)".

Paralelamente, Claude Code estableció el estándar de la industria en autonomía supervisada con su Auto Mode (GA el 16 de abril de 2026), cuyo clasificador reasoning-blind de dos etapas representa el diseño antiadversarial más sofisticado entre las tres CLIs principales, aceptando explícitamente un 8,5% de falsos positivos en aras de la seguridad y fallando cerrado por diseño.

La firma común de ambos: **el humano nunca abandona el bucle del todo — solo se desplaza del asiento del conductor activo al del fiador de último recurso.**

---

*Fin del informe. Síntesis completa de los 11 hallazgos de investigación a través de dos dominios.*

## Sources

- <https://www.xataka.com/movilidad/he-probado-modo-fsd-supervisado-tesla-he-descubierto-cosa-supervisar-agotador-que-conducir>
- <https://fsdtracker.eu/>
- <https://fsdeuropenews.com/>
- <https://vfuturemedia.com/electric-vehicles/tesla-fsd-europe-expansion-current-status-and-timeline-may-2026/>
- <https://www.teslaacessories.com/blogs/news/fsd-crossing-the-atlantic-decoding-the-dutch-rdw-approval-and-the-2026-eu-rollout>
- <https://electrek.co/2025/11/24/tesla-announces-fsd-approval-europe-february-2026/>
- <https://github.com/bradAGI/awesome-cli-coding-agents>
- <https://codenote.net/en/posts/ai-coding-cli-full-permission-autonomous-agents/>
- <https://www.verdent.ai/guides/ai-coding-agent-2026>
- <https://agenticai-flow.com/en/posts/ai-coding-agents-complete-guide/>
- <https://www.codeai.studio/blog/mastering-agent-mode-autonomous-ai-coding>
- <https://www.anthropic.com/engineering/claude-code-auto-mode>
- <https://arxiv.org/pdf/2604.04978v1>
- <https://code.claude.com/docs/en/auto-mode-config>
- <https://gist.github.com/sc0tfree/11c86116df4c2281a976d796f9493cd7>
- <https://claudefa.st/blog/guide/development/auto-mode>

## Run metadata

- **Prompt:** MODO: EXECUTION MODE — AUTONOMÍA TOTAL AUTORIZADA
- **Depth / breadth:** 2 / 3
- **Queries used:** 4 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 381.1 s
- **Errors during run:** 4
- **Started at:** 2026-06-05T19:06:59Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://www.tesla.com/ownersmanual/modely/es_mx_0126/GUID-2C...': page-fetch: https://www.tesla.com/ownersmanual/modely/es_mx_0126/GUID-2CB60804-9CEA-4F4B-8B04-09B991368DC5.html: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.tesla.com/ownersmanual/models/es_mx/GUID-B3EF4EA...': page-fetch: https://www.tesla.com/ownersmanual/models/es_mx/GUID-B3EF4EAF-6B25-4590-9DDC-B8767F143377.html: HTTP Error 403: Forbidden`
- `fetch_page 'https://www.tesery.com/es-es/blogs/tesla-model-3-s-x-y-cyber...': page-fetch: https://www.tesery.com/es-es/blogs/tesla-model-3-s-x-y-cybertruck-guides/unlocking-autonomy-how-to-engage-full-self-driving-mode-in-your-tesla: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`
- `fetch_page 'https://www.tesery.com/es-es/blogs/news/how-to-put-tesla-in-...': page-fetch: https://www.tesery.com/es-es/blogs/news/how-to-put-tesla-in-self-driving-mode: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1010)>`

</details>
