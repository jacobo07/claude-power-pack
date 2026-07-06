# Informe Forense: "No hice ningún cambio en la Wii entre el 23/05"

## 1. La afirmación bajo análisis

La afirmación del Owner —*"no hice ningún cambio en la Wii entre el 23/05 [y ahora]"*— es, en apariencia, una constatación trivial de estabilidad del entorno de prueba. En realidad es una **hipótesis forense crítica** para el diagnóstico abierto del proyecto: la regresión `v96`–`v104` de tipo *BLACK-before-title* frente a la *baseline* `v85` (title alcanzado + freeze al pulsar Start). El nudo del problema, registrado en la memoria del proyecto, es exactamente esta bifurcación:

> "Si `v99` reproduce el comportamiento de `v85` → la regresión está en MIS builds (fuente post-v85 o no-determinismo de kamek +24 B). Si `v99` también da BLACK-before-title → drift de entorno/estado de la Wii, NO código."

Por tanto, la pregunta no es retórica. **Si el estado persistente de la Wii puede haber mutado sin intervención deliberada del Owner, entonces "no hice ningún cambio" puede ser cierto a nivel de intención y falso a nivel de bytes en NAND** — y eso reabriría la rama "env/Wii state drift" que la memoria daba por condicionalmente cerrada.

Este informe sintetiza la arquitectura real de la NAND de Wii y su modelo de persistencia para responder con precisión: **¿qué significa físicamente "no cambiar nada" en una Wii, y es esa invariancia siquiera posible?**

---

## 2. Tesis central: la NAND de Wii NO es inmutable entre arranques

La conclusión técnica más importante, y la que contradice la intuición detrás de la afirmación, es la siguiente:

> **El sistema de ficheros de la Wii (SFFS) se reescribe en cada modificación, y un arranque normal de Wii Sports Resort (WSR) produce modificaciones.** "No hacer cambios" desde el punto de vista del usuario **no** implica una NAND idéntica byte-a-byte entre el 23/05 y hoy.

Evidencia directa en la propia memoria del proyecto: la captura de hardware GREEN de `v83` (`20260523_124109.mp4`) registra **"Play Count: 19"** en el título de WSR. El contador de partidas (*Play Count*) es un dato persistido en NAND que el firmware de WSR **incrementa y reescribe** en operación normal. Cada arranque que toca ese contador —o cualquier save, mensaje del Wii Message Board, o registro de IOS— dispara una reescritura del sistema de ficheros. La sección 4 explica el mecanismo exacto.

La distinción operativa es:

| Nivel | "No hice ningún cambio" | ¿Verdadero? |
|---|---|---|
| Intención del Owner (no instalé IOS, no toqué System Menu, no formateé) | Sí | Probablemente cierto |
| Configuración semántica (mismo IOS, mismos títulos instalados, misma región RZTP01) | Sí | Probablemente cierto |
| Estado byte-a-byte de NAND | "Idéntico" | **Falso por construcción** — SFFS muta en cada boot que persiste algo |
| Claves/HMAC por consola | Sin cambios | Cierto (no son reescritos en uso normal) |

---

## 3. Arquitectura física de la NAND de Wii (sustrato del análisis)

Para razonar sobre "cambio" hay que fijar las unidades físicas. La NAND de Wii es de **512 MiB** con la siguiente jerarquía:

| Unidad | Tamaño | Composición | Rol |
|---|---|---|---|
| Página | 2048 B datos + 64 B spare/ECC = 2112 B | unidad de lectura/escritura flash | — |
| Cluster | 16 384 B | 8 páginas | **unidad de asignación de SFFS** |
| Bloque | 131 072 B | 64 páginas | **unidad que puede fallar (bad block)** |
| Total | 512 MiB | 4096 bloques | — |

**Distribución de clusters:**

- **Clusters `0x40`–`0x7EFF`**: datos del sistema de ficheros, **cifrados con AES por-consola** y **firmados con HMAC por-consola**.
- **Clusters `0x7F00`–`0x7FFF`**: **16 superbloques SFFS** *sin cifrar*, uno cada 16 clusters.
- Los **primeros 64 entries** de la FAT están reservados (`0xFFFC`).

Un volcado completo vía BootMii **BackupMii** (release CEIL1NG_CAT) genera un `nand.bin` de **553 649 152 bytes** en la SD: `4096 × 64` páginas de `(2048+64)` bytes, más un **footer de 1024 bytes** que contiene:

| Offset (dentro del footer) | Tamaño | Contenido |
|---|---|---|
| 0 | 256 B | información legible (human-readable) |
| 256 | 128 B | **datos OTP** (one-time-programmable, claves) |
| 384 | 128 B | padding |
| 512 | 256 B | **SEEPROM** |
| 768 | 256 B | padding |

Este footer es la razón por la que **un backup de NAND es único por consola**: empaqueta OTP y SEEPROM, que contienen Console ID, NAND HMAC key, NAND AES key y la clave privada ECC.

---

## 4. El mecanismo que invalida la inmutabilidad: superbloques generacionales round-robin

Aquí está el corazón técnico que responde a la afirmación del Owner. SFFS **no** sobrescribe en sitio; usa **persistencia generacional round-robin** sobre los 16 superbloques:

1. Cada superbloque empieza con el **magic `'SFFS'`** + un **número de generación de 4 bytes** + un campo `0x10` de 4 bytes.
2. IOS, al arrancar, **selecciona el superbloque cuya generación coincide con el valor en SEEPROM**.
3. **En CUALQUIER modificación del sistema de ficheros**, IOS:
   - incrementa en 1 la generación en SEEPROM,
   - actualiza el número de generación del superbloque,
   - y **escribe un superbloque completamente nuevo en el siguiente slot** del anillo de 16.

La **FAT** vive a partir del offset `0xC` con `0x8000` entradas de 2 bytes por cluster. Valores especiales:

| Valor FAT | Significado |
|---|---|
| `0xFFFB` | fin de cadena (chain end) |
| `0xFFFC` | reservado (primeras 64 entradas) |
| `0xFFFD` | bloque defectuoso de fábrica (**siempre en grupos de 8**) |
| `0xFFFE` | vacío (empty) |

**Implicación directa para el caso:** cada vez que WSR persiste el *Play Count*, un save, o IOS toca un log/registro, **el número de generación en SEEPROM avanza y se materializa un superbloque físicamente distinto**. Entre la captura del 23/05 (`Play Count: 19`) y cualquier arranque posterior, **la generación SFFS casi con certeza ha avanzado**. La consola no está en el mismo estado de NAND; está en un estado *sucesor* legítimo, autoconsistente, pero distinto.

Esto **no** es corrupción ni un "cambio" en el sentido que el Owner niega. Es el funcionamiento normal del firmware. Pero es exactamente la clase de mutación silenciosa que puede:

- desplazar el punto de fallo si el bug latente de `v102` (sellado en RULE-106: *latent boot bug enmascarado por breadcrumbs FZDIAG*) depende de algún estado leído de NAND,
- alterar tiempos/contenido que el path de arranque H&S→SCENE_TITLE consume.

---

## 5. Firma criptográfica por-consola (por qué el estado no es trasplantable)

Cada cluster de datos (`0x40`–`0x7EFF`) se firma con HMAC usando:

- una **clave OTP de 20 bytes**, más
- un **salt no estándar de 0x40 bytes** compuesto por: `uid` + nombre de fichero de 12 bytes + índice de cluster + inodo FST + campo "x3" + padding de ceros.

El HMAC resultante (20 bytes) se almacena **por duplicado** en el spare/OOB de las **páginas 7 y 8** del cluster. Para clusters de metadatos **solo se rellena el campo de cluster** del salt.

Detalles que importan para cualquier intento de restauración o análisis:

- **Bug en la derivación de IV de BroadOn**: el bucle sobrescribe iteraciones, de modo que el **IV de cifrado acaba siendo los últimos 16 bytes (a cero) del salt**. Es un comportamiento documentado y reproducible, no aleatorio.
- **ECC roto en lectura cruda**: `wiinandfuse` advierte que la corrección ECC está rota; un volcado con programador de flash mostrará "corrupción" salvo que se ignoren los errores ECC (`-e`).

**Consecuencia forense:** el estado de NAND está **criptográficamente ligado a ESTA consola**. No se puede "resetear a un estado conocido" trasplantando un backup de otra Wii, ni se puede comparar limpiamente un volcado contra una referencia externa sin las claves OTP de la propia consola.

---

## 6. Riesgo de restauración: por qué "volver atrás" no es trivial

Si el equipo considerara restaurar la NAND al estado del 23/05 para descartar drift, las restricciones son severas:

- Restaurar un backup **no verificado**, **de otra Wii**, o leído de una **SD defectuosa** puede provocar un **brick PEOR** — el estado NAND está keyed/HMAC-bound por consola.
- **BootMii RestoreMii** ejecuta obligatoriamente un **pase de SIMULACIÓN** primero y, cuando BootMii está instalado **como IOS**, exige el **código Konami** (↑↑↓↓←→←→ B A START) mediante **mando de GameCube**.
- **Wii Family Edition y Wii mini NO pueden restaurar backups de NAND** (no tienen puerto GameCube para el código de confirmación; no son consolas boot2).

Por tanto, una restauración completa es una herramienta **de alto riesgo**, no un "rollback" casual. No es el camino de primera línea para este diagnóstico.

---

## 7. Camino seguro recomendado: extracción quirúrgica vía Dolphin

Existe una vía **sin reescritura completa de NAND** que es la apropiada para forense y para preservar/comparar estado:

1. Volcar la NAND con **BootMii BackupMii** (genera el `nand.bin` de 553 649 152 B descrito en §3).
2. Importar ese backup en **Dolphin Emulator**.
3. Para saves de juego: **Tools → "Export All Wii Saves"**.
4. Para datos específicos —p. ej. el **Wii Message Board** en `Wii/title/00000001/00000002/data/cdb.vff`— extraer el fichero y, si hiciera falta, re-inyectar con **WiiXplorer**.

Esta ruta es **más segura que un RestoreMii completo** ante corrupción de saves, y —clave para el proyecto— permite **comparar el estado persistido del 23/05 contra el actual** sin tocar la consola física.

---

## 8. Síntesis aplicada al diagnóstico v85→v104

Cruzando la arquitectura NAND con el árbol de fallo registrado en la memoria del proyecto:

| Hipótesis del proyecto | ¿Qué dice la arquitectura NAND? |
|---|---|
| Regresión está en MIS builds (fuente post-v85 / no-determinismo kamek +24 B) | Compatible: el path H&S→SCENE_TITLE (`KSR_AUTO_HUB` main.cpp:8351 nunca ejecuta) puede ser puro código. La NAND no es necesaria para explicarlo. |
| Drift de entorno/estado Wii, NO código | **La NAND SÍ ha derivado** (generación SFFS avanzada por *Play Count*/saves), pero esa deriva es *normal y autoconsistente*, no corrupción. Para ser causa del BLACK habría que probar que el boot path lee un valor NAND sensible al estado. |
| `v102` latent boot bug enmascarado por breadcrumbs FZDIAG (RULE-106) | El enmascaramiento es de **timing/orden de instrucciones**, no de NAND. La deriva NAND es un *segundo* factor independiente, no el sellado en RULE-106. |

**Recomendación de priorización (no especulativa):**

1. La afirmación "no hice ningún cambio" es **creíble a nivel de intención** y **no debe usarse como prueba de NAND idéntica**. Es metodológicamente incorrecto cerrar la rama "code regression" apoyándose en ella.
2. El experimento `v99` (re-inject bit-perfect de `v85`, WBFS md5 `fc076ea1…`) **sigue siendo el discriminador correcto**: si `v99` reproduce *title→Start→freeze*, la deriva NAND queda descartada como causa y el foco vuelve a la fuente post-v85. Si `v99` da BLACK, entonces —y solo entonces— la deriva NAND/entorno entra como sospechoso real, y el camino §7 (BackupMii + Dolphin diff) es el siguiente paso.
3. **No** intentar RestoreMii como atajo de "reset de estado" — el riesgo de brick peor (§6) no compensa frente a la extracción no destructiva de §7.

---

## 9. Especulación (claramente marcada)

> **[ESPECULACIÓN — no confirmada por las learnings]** Si el bug latente de boot sellado en RULE-106 dependiera de algún registro de IOS o de un valor en el cluster de configuración (p. ej. estado de region/STM o un flag NWC24 que WSR toca durante H&S), entonces la deriva generacional de SFFS entre el 23/05 y hoy podría —en teoría— mover el cluster activo a un slot del anillo round-robin cuyo contenido difiera lo suficiente como para cambiar el momento exacto del freeze. **Esto es una conjetura**: ninguna de las learnings establece que el path H&S→SCENE_TITLE lea estado NAND más allá de lo estándar de IOS. La forma barata de falsarlo es exactamente el experimento `v99` + un diff Dolphin de saves entre dos volcados (§7). Si los saves extraídos son idénticos salvo el *Play Count*, la hipótesis de "NAND como causa" queda muy debilitada.

> **[ESPECULACIÓN]** Dado que la memoria registra que `GEX44 ≠ real-hw` es "la enfermedad sistémica" del proyecto (RULE-105, Silicon Provenance Gate), conviene notar que **la deriva NAND es un fenómeno de *hardware real* que el emulador GEX44/Dolphin no reproduce fielmente** salvo que se le re-importe el backup actual. Cualquier reproducción del BLACK en emulador con una NAND *vieja* importada estaría, paradójicamente, probando un estado que la consola física **ya no tiene**. Esto refuerza usar un **volcado fresco** si se quiere paridad emulador↔silicio.

---

## 10. Conclusiones

1. **"No hice ningún cambio en la Wii desde el 23/05" es cierto como declaración de intención y de configuración, pero técnicamente falso como afirmación de invariancia byte-a-byte de NAND.** SFFS reescribe un superbloque nuevo (generación +1 en SEEPROM) en cada modificación del sistema de ficheros, y un arranque normal de WSR persiste datos (mínimo, el *Play Count* visto en `Play Count: 19`).
2. La deriva NAND resultante es **normal, autoconsistente y criptográficamente válida** —no corrupción— y **no es trasplantable ni reseteable trivialmente** por su ligadura HMAC/AES por-consola.
3. Para el diagnóstico v85→v104, **la afirmación no debe usarse como prueba** para cerrar la rama "code regression". El discriminador válido sigue siendo el re-inject bit-perfect `v99`; la deriva NAND solo asciende a sospechoso real si `v99` también da BLACK.
4. Si llega ese punto, la vía **no destructiva** correcta es **BackupMii → import en Dolphin → Export All Wii Saves / extracción de `cdb.vff`**, nunca un **RestoreMii** completo (riesgo de brick peor; imposible en Family Edition / Wii mini).

**Acción concreta siguiente (mía, no del Owner):** dejar registrado en el vault que la frase "no cambié nada" **no certifica NAND idéntica**, y enlazar este informe al árbol de decisión de `v99` para que el experimento de re-inject siga siendo el gate forense, con BackupMii+Dolphin diff como rama secundaria condicionada al verdict de `v99`.

## Sources

- <https://www.reddit.com/r/WiiHacks/comments/tbzky7/wii_homebrew_guide_modded_to_stock_read_premises/>
- <https://gbatemp.net/threads/nand-backup-and-restore.620123/>
- <https://wii.hacks.guide/bootmiirecover.html>
- <https://gbatemp.net/threads/help-restoring-wii-to-unmodded-default-state.637478/>
- <https://wiibrew.org/wiki/BackupMii>
- <https://github.com/isfshax/isfshax/blob/master/README.md>
- <https://wiibrew.org/wiki/Wiinandfuse>
- <https://github.com/wiiu-wasteland/wiiunandfuse>
- <https://wiibrew.org/wiki/Hardware/NAND>
- <https://wiki.hacks.guide/wiki/User:Techno_Eggnog/sandbox>

## Run metadata

- **Prompt:** No hice ningún cambio en la Wii entre el 23/05
- **Depth / breadth:** 2 / 3
- **Queries used:** 2 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 323.7 s
- **Errors during run:** 0
- **Started at:** 2026-06-12T13:15:55Z
- **Module version:** deep_research 0.1.0
