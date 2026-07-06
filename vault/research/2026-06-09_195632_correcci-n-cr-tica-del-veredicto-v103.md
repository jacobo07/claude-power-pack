# Corrección Crítica del Veredicto v103 — KobiiSports Resort (Wii Homebrew / Kamek)

> **Nota de alcance y procedencia de la evidencia.** El barrido de fuentes públicas (SERP) devolvió **cero información** sobre «v103», su veredicto o sus diagnósticos de arranque: se trata de un proyecto interno/privado. El único recurso público de modding de *Wii Sports Resort* localizado fue el **GameBanana «WSR Hub»** (mods con soporte publicitario, sin contenido de diagnóstico de boot homebrew). En consecuencia, esta «corrección crítica» **no puede** apoyarse en una fuente externa que describa el veredicto v103; debe construirse desde **primeros principios de forense Wii** + el corpus de aprendizajes recogido + el estado documentado del proyecto (v102 ROOT CAUSE 2026-06-09 y RULE-105 Silicon Provenance Gate). Donde infiero el contenido del veredicto v103, lo marco explícitamente como **[ESPECULACIÓN]**.

---

## 1. Tesis de la corrección

La corrección crítica del veredicto v103 se reduce a **un único eje de procedencia (provenance)** que ya quedó sellado como enfermedad sistémica del proyecto:

> **Un veredicto que descansa sobre evidencia emulada (Dolphin / GEX44 HLE) NO es evidencia de silicio.** Los valores de retorno y la temporización IOS que produce Dolphin son **constantes escritas por Dolphin**, no respuestas del Starlet físico. Cualquier «GREEN», «callable», «verified» o «real-hw» derivado de ellos está **contaminado de procedencia** y debe degradarse.

Esto es exactamente la línea de `RULE-105` («GEX44 ≠ real-hw es la enfermedad sistémica») y de la causa raíz v102 del 2026-06-09 («el bug latente de boot quedó **enmascarado** por las migas OSReport de `KSR_FREEZE_DIAG`; el binario *clean* es el vector de regresión, no la no-determinación»). El veredicto v103 hereda ambos riesgos y la corrección consiste en **re-anclar el veredicto al silicio físico** y en **separar el bug real del artefacto de instrumentación**.

---

## 2. Por qué la evidencia emulada exige degradar el veredicto

El aprendizaje más decisivo del corpus es que **Dolphin no sólo aproxima IOS: lo falsifica activamente** cuando no tiene equivalente de host. Catálogo de mecanismos que invalidan cualquier veredicto basado en GEX44/Dolphin:

| Mecanismo de Dolphin HLE | Qué fabrica | Consecuencia para un veredicto |
|---|---|---|
| `IWII_IPC_HLE_Device` base | Escribe `FS_ENOENT` en `Open()` y `FS_EINVAL` en `Close()` en `command_address+4` | Un código errno «sano» (-2/-22…) puede ser un **valor de catálogo**, no una respuesta del módulo IOS real |
| `GetDefaultReply()` | Latencia de respuesta sintética fija = `GetTicksPerSecond()/4000` (~250 µs, valor **arbitrario**) | Cualquier inferencia de timing/RTT sobre HLE es **ruido autoría-Dolphin**, no timing del Starlet |
| Bluetooth passthrough (`usb_oh1_57e_305_real`) | Intercepta `HCI_CMD_READ_BUFFER_SIZE` y opcodes vendor `0xFC4C/0xFC4F`; sintetiza `FakeReadBufferSizeReply` / `FakeVendorCommandReply` con `status 0x00`, `ACL/SCO_PKT_SIZE/NUM` hardcodeados | Demuestra el patrón general: **un retorno de ioctl emulado puede estar enteramente fabricado** y divergir de cualquier adaptador físico |

**Aplicación a v103:** si el veredicto v103 declara un *address callable*, un *fd válido*, un *round-trip confirmado* o un *boot GREEN* **apoyándose en una traza de Dolphin/GEX44**, esa afirmación debe **degradarse a "no probado en silicio"**. Esto reproduce el patrón ya anulado en el proyecto: la «OVERTURN» del veredicto V92/V87 fue **anulada** precisamente porque la desk-disasm no demostraba *callability desde el scope de Kamek*, y porque «WSR lo llama internamente» ≠ «invocable desde Kamek». El mismo cuchillo corta v103.

### 2.1 El ABI IPC sí es invariante — qué SÍ sobrevive a la emulación

La corrección no es nihilista. El **ABI IPC de Wii es fijo entre silicio y HLE**, y esto define qué porción del razonamiento v103 puede conservarse:

- **Offsets de `SIOCtlVBuffer`** (constantes en HW y HLE): parámetro/comando `+0x0C`, `NumberInBuffer +0x10`, `NumberPayloadBuffer +0x14`, `BufferVector +0x18`; el `IOSRequestWrapper` se rellena a `0x40` para alineación de 32 bytes.
- **Registros IPC Hollywood**: `IPC_PPCMSG=0x00`, `IPC_PPCCTRL=0x04` (X1=nuevo comando, X2=reload IOS), `IPC_ARMMSG=0x08`, `IPC_ARMCTRL=0x0c` (Y1=reply listo, Y2=ack).
- **Códigos de error libogc** `IOS_Ioctl/IOS_Ioctlv`: `-4` = error general/heap, `-22` = heap insuficiente.

**Regla de corrección:** la **estructura/layout** del request v103 (offsets, padding, secuencia de registros) es verificable estáticamente y puede declararse correcta sobre HLE. La **semántica del retorno** (¿el address es realmente esa API? ¿el fd es real? ¿el boot realmente sobrevive?) **no** es verificable sobre HLE y debe re-probarse en hardware físico.

---

## 3. La raíz arquitectónica: por qué las direcciones IOS divergen

El corpus explica *por qué* este eje de procedencia es tan corrosivo en Wii y no en GameCube:

- **libogc selecciona rutas en tiempo de compilación** vía `HW_DOL` (GameCube, acceso directo a registros memory-mapped PPC) vs `HW_RVL` (Wii). En Wii, **USB, WiFi, filesystem y seguridad se enrutan por el co-procesador ARM Starlet** corriendo IOS mediante IPC → operaciones **asíncronas y dirigidas por callback**. Esa indirección IPC es la **raíz arquitectónica** de que las direcciones dependientes de IOS se comporten distinto que las rutas de hardware directo.
- La memoria Wii se parte en arena principal + región **MEM2 de 64 MB** (funciones Arena2); `SYS_Init()` debe llamarse primero (EXI, DSP, IRQ); los subsistemas IOS (usbstorage, red lwIP/IOS) se apilan encima.
- Esto explica la distinción operativa del proyecto entre **wrappers libogc-internos de IOS** (cluster `0x8003bxxx`) y **helpers bare-MMIO silicon-reales** (`__IPCReadReg=0x8003a8c0`, `__IPCWriteReg=0x8003a8d0`, `DCFlushRange=0x800460e0`, `DCInvalidateRange=0x800460b0`). El buzón Hollywood en `0xCD000000` es **uniforme en silicio** entre versiones IOS.

**Aplicación a v103:** si el veredicto v103 trata una dirección del cluster libogc como «silicon-real» sólo porque WSR la enlaza, eso es la trampa V92 ya anulada. La distinción **bare-MMIO (silicon-uniforme) vs wrapper-libogc (estado-dependiente)** debe re-aplicarse a cada dirección que v103 invoque.

### 3.1 Vector de procedencia para *demostrar* qué se enlazó

libogc expone metadata de versión/build en runtime vía **`__sys_versioninfo`** (`libogc/system.c:196`): fecha de build + cadena de versión. Esto es un **vector de procedencia accionable** para confirmar qué cluster IOS/libogc empaqueta el DOL de WSR frente a un shim HLE de Dolphin/GEX44. **[ESPECULACIÓN / sugerencia proactiva]:** incorporar una lectura de `__sys_versioninfo` (o su equivalente en el DOL golden) en la instrumentación v104 daría una **firma de procedencia binaria** que distingue «corriendo en IOS real» de «corriendo bajo HLE» — cerrando la enfermedad GEX44≠real-hw a nivel de evidencia, no de política.

---

## 4. El segundo eje de corrección: el bug enmascarado por la instrumentación

La causa raíz v102 (2026-06-09) ya estableció que **el binario clean (FZDIAG-off) es el vector de regresión**, no la no-determinación: v102 vs v85 GREEN son 98.2% idénticos; el delta es la **eliminación del macro `KSR_FREEZE_DIAG` de `KobiiOnConfigure` (−324 instr)**. v85 sólo era «GREEN» por las migas OSReport.

Esto impone una **segunda corrección al veredicto v103**: cualquier veredicto v103 debe declarar **explícitamente si se midió sobre binario instrumentado o clean**, porque:

- Un **GREEN sobre binario instrumentado** sólo prueba «las migas enmascaran el bug latente», no «el bug está corregido».
- Un **RED sobre binario clean** es el comportamiento honesto del producto de envío.
- Mezclar ambos (medir GREEN instrumentado y declarar el producto clean «listo») reproduce exactamente el error v85→v102.

**Regla de corrección:** el veredicto v103 debe re-emitirse como una **matriz {instrumentado, clean} × {hardware-físico, GEX44/HLE}**, con la celda de envío siendo **clean × hardware-físico**. Cualquier otra celda es diagnóstico, no veredicto de producto.

---

## 5. Metodología forense correcta para re-emitir el veredicto

El corpus aporta el toolkit exacto para anclar el veredicto v103 en silicio. Estas son las técnicas que la corrección debe usar **en lugar de** la traza emulada:

### 5.1 Captura de estado de excepción en hardware físico (sin USB Gecko)

El **Star/Riidefi Custom Exception Handler** es un código Gecko distribuible que muestra info de excepción en la TV al crashear y luego vuelve al System Menu tras hacer scroll — alternativa **hardware-side** a addr2line/objdump para capturar `SRR0/DSISR/DAR` **sin** USB Gecko ni Dolphin:

| Región | Hook address |
|---|---|
| PAL | `C2023694` |
| NTSC-U | `C20235F4` |
| NTSC-J | `C20235B4` |
| NTSC-K | `C20236F4` |

Como KobiiSports Resort es **RZTP01 (PAL)** por contrato de Disc ID, el hook aplicable es **`C2023694`**. Esto entrega el `SRR0` del *black-before-title* **en silicio físico**, que es justamente la celda de evidencia que falta y que dispara el Forensic Reflex Arc del proyecto (`SRR0=`/`DSISR=`/`DAR=` → `addr2line` + `objdump`).

### 5.2 De la dirección de crash al source C++

- **`powerpc-gekko-addr2line -e <elf> <address>`** o **`gdb info line *0x800084ac`** contra la info de símbolos del `.elf` (sin USB Gecko).
- Alternativa por compilación: `CXXFLAGS = -save-temps -Xassembler -aln=$@.lst`, hallar el símbolo *nearest-not-over* en el `.map`, y localizar la directiva `.loc 1 <line> 0` en el offset de la función dentro del `.lst` (p.ej. función en `0x2d0` + offset 72 B = `0x318`).
- Para depuración remota: devkitPro provee **`powerpc-gekko-gdb`/`gdbtui`/`insight`** sobre USB Gecko (`target remote /dev/ttyUSB0` o COM vía driver VCP). Dolphin muestra `printf`/`OSReport` con *Debugging UI* + logging OSReport activados (**pero recordar §2: el OSReport bajo HLE puede correr sobre IOS falsificado**).

### 5.3 Recuperación de brick durante el diagnóstico de boot

Como v96–v103 entran en territorio *black-before-title* (peor modo de fallo que el *title→Start→black* de v85), el diagnóstico de boot debe blindarse:

- **BootMii**: instalable vía IOS o directamente a **boot2**; el install a boot2 da protección anti-brick extendida y carga **antes** de la mayoría de errores de brick mayores, pero requiere un **boot1 vulnerable** presente sólo en Wiis fabricadas **antes de 2009**. Cuando boot2 no está disponible, se recomienda **Priiloader** junto a BootMii-IOS.
- **Backups NAND vía BootMii** son el mecanismo de recuperación recomendado para diagnósticos de fallo de arranque.
- Estructura estándar homebrew (WiiBrew, wiki canónica): `/apps/<AppName>/{boot.dol, meta.xml, icon.png}`.

**[Sugerencia proactiva]:** antes de la próxima campaña de boot físico (la celda *clean × hardware* del §4), confirmar fecha de fabricación de la Wii de pruebas; si es pre-2009 con boot1 vulnerable, instalar **BootMii-boot2 + backup NAND** convierte cada boot RED en recuperable sin riesgo de brick — habilitando iteración agresiva sobre el bug latente.

---

## 6. La contradicción de toolchain — una anomalía que el veredicto debe resolver

Un aprendizaje **contradice frontalmente** un supuesto del proyecto y debe señalarse como riesgo de procedencia de toolchain:

> **Kamek** (motor de inyección de código GC/Wii, de Ninji/Treeki 2010-2021, hoy mantenido por RoadrunnerWMC) **requiere NXP CodeWarrior Special Edition para MPC55xx/MPC56xx v2.10** para compilar. **GCC/Clang están explícitamente NO soportados** porque el C++ ABI de CodeWarrior difiere — clases y herencia virtual sólo funcionan correctamente con CW. El linker .NET 10.0 hace el paso de inyección.

Esto **contradice el supuesto devkitPPC / `powerpc-eabi-gcc`** declarado en el `CLAUDE.md` del proyecto y en el flujo `make.py --region PAL`.

**Implicación para el veredicto v103 — dos lecturas posibles:**

1. **[ESPECULACIÓN]** El proyecto usa un fork/variante de Kamek o un patrón de inyección que sí tolera el ABI de devkitPPC (lo cual sería un hecho de procedencia del proyecto que el aprendizaje público no captura). En ese caso, el riesgo es **C++ con herencia virtual**: si algún módulo Kamek de KobiiSports usa clases con vtables compiladas por GCC e interactúa con vtables WSR (compiladas por el toolchain original), un **layout de vtable divergente** es un candidato de primer orden para un *black-before-title* — exactamente el tipo de fallo latente, no-determinista en apariencia, que enmascara `KSR_FREEZE_DIAG`.
2. Si el supuesto devkitPPC es correcto y suficiente, entonces este aprendizaje es un **falso-aplicable** para este repo y debe registrarse como tal (evitando que futuras sesiones «corrijan» el toolchain hacia CodeWarrior por error).

**Corrección recomendada:** el veredicto v103 debe incluir una línea de **provenance de ABI**: ¿hay alguna clase con métodos virtuales en la ruta de inyección (`tools/caddie/src/`) que cruce la frontera ABI con WSR? Si la respuesta es sí, ese cruce es un sospechoso de boot-crash que ningún addr2line sobre HLE detectará, porque el layout de vtable es correcto bajo el mismo compilador y sólo diverge contra el binario WSR real.

---

## 7. Veredicto corregido (forma propuesta)

Reuniendo los dos ejes, el veredicto v103 corregido debería re-emitirse así:

| Dimensión | Veredicto pre-corrección (riesgo) | Veredicto corregido (exigido) |
|---|---|---|
| **Procedencia de evidencia** | GEX44/Dolphin tratado como «real-hw» | Degradar todo GREEN/callable/round-trip emulado a **«no probado en silicio»** (RULE-105) |
| **Binario medido** | GREEN instrumentado ≈ producto listo | Matriz **{instrumentado, clean} × {físico, HLE}**; envío = **clean × físico** |
| **Direcciones IOS** | cluster libogc «silicon-real» por enlace WSR | re-clasificar: **bare-MMIO = silicon-uniforme**, **wrapper-libogc = estado-dependiente** (anti-trampa V92) |
| **Captura del crash** | OSReport bajo HLE | **Star Exception Handler `C2023694` (PAL)** en hardware físico → `SRR0` → `addr2line` |
| **Toolchain/ABI** | devkitPPC asumido sin riesgo | auditar **cruces de vtable C++ GCC↔WSR**; documentar por qué Kamek-sin-CodeWarrior es válido aquí |
| **Bug vs instrumentación** | «no-determinación» | **bug de boot latente real**, enmascarado por migas `KSR_FREEZE_DIAG` (causa raíz v102) |

**Conclusión de la corrección:** el veredicto v103 no puede declararse **product-GREEN** mientras la única evidencia favorable provenga de GEX44/Dolphin o de binario instrumentado. El estado honesto es **«diagnóstico en curso, bug de boot latente confirmado por subtracción, pendiente de captura `SRR0` en silicio físico»** — coherente con la dirección «next = instrumented clean + trap hardware boot (ADR-004 MC-02)» ya anotada en el estado del proyecto.

---

## 8. Acciones siguientes recomendadas (proactivas)

1. **Instalar el Star/Riidefi Exception Handler `C2023694`** sobre el WBFS clean v103 y bootear en hardware físico → capturar `SRR0/DSISR/DAR` del black-before-title. Es la pieza de evidencia que cierra el veredicto sin depender de HLE.
2. **Emitir el binario clean con un mínimo de migas «no-instrumentadas»** que no alteren `KobiiOnConfigure` (p.ej. escritura a MEM2 fija leída post-mortem por NAND-log, no OSReport) para evitar que la instrumentación vuelva a enmascarar el bug (lección v102/v85).
3. **Auditoría de vtable C++ en `tools/caddie/src/`**: enumerar toda clase con métodos virtuales que toque tipos WSR; el aprendizaje Kamek↔CodeWarrior eleva esto de «higiene» a «sospechoso primario de boot-crash».
4. **Añadir lectura de `__sys_versioninfo`** (o firma equivalente del DOL golden) a la instrumentación → firma binaria de procedencia que distingue silicio de HLE de forma automática.
5. **Backup NAND + BootMii-boot2** en la Wii de pruebas (si boot1 es pre-2009) para iterar boots RED sin riesgo de brick.
6. **Registrar el toolchain como hecho de procedencia explícito** en el vault: por qué este repo inyecta con devkitPPC pese a que upstream Kamek exige CodeWarrior — para que ninguna sesión futura «corrija» el toolchain por error.

---

### Anexo — limitación honesta de este informe

Este informe **no contiene** el texto literal del veredicto v103 porque **ninguna fuente, pública o de research, lo aportó**; el proyecto es interno. Todas las afirmaciones sobre el *contenido* del veredicto v103 están marcadas **[ESPECULACIÓN]**. Lo que sí es firme y verificado es: (a) el mecanismo por el que Dolphin/GEX44 falsifica respuestas IOS, (b) la invariancia del ABI IPC, (c) el toolkit forense de captura `SRR0`→source, (d) la contradicción de toolchain Kamek/CodeWarrior, y (e) el patrón de bug-enmascarado-por-instrumentación ya sellado como causa raíz v102. La corrección crítica se sostiene sobre estos cinco hechos, no sobre el veredicto v103 sin ver.

## Sources

- <https://gamebanana.com/games/6332>
- <https://wiibrew.org/wiki/Main_Page>
- <https://www.reddit.com/r/WiiHacks/comments/xmzydl/wii_hacks_wii_modding_help_thread/>
- <https://wii.hacks.guide/hbc.html>
- <https://github.com/Treeki/Kamek>
- <https://www.reddit.com/r/WiiHacks/comments/13zbc2x/so_what_exactly_is_lecode_exception_handler/>
- <http://www.wiibrew.org/wiki/Debugging>
- <https://mariokartwii.com/showthread.php?tid=1032>
- <https://wiibrew.org/wiki/Libogc>
- <https://github.com/devkitPro/libogc>
- <https://deepwiki.com/devkitPro/libogc>
- <https://www.reddit.com/r/WiiHacks/comments/i3s62e/wii_ios_documentation/>
- <https://github.com/Neui/dolphin-emu/blob/master/Source/Core/Core/IPC_HLE/WII_IPC_HLE_Device_usb_bt_real.cpp>
- <https://github.com/Neui/dolphin-emu/blob/master/Source/Core/Core/IPC_HLE/WII_IPC_HLE_Device.cpp>
- <https://readmex.com/en-US/dolphin-emu/dolphin/page-3.43a60e18e-8a2c-4246-9000-eb119192d71f>
- <https://deepwiki.com/devkitPro/libogc/3.3-ipc-and-ios-services>
- <https://wiibrew.org/wiki/IPC_(SDK)>

## Run metadata

- **Prompt:** Corrección crítica del veredicto v103.
- **Depth / breadth:** 2 / 3
- **Queries used:** 5 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 474.7 s
- **Errors during run:** 4
- **Started at:** 2026-06-09T17:56:32Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://forum.wii-homebrew.com/...': page-fetch: https://forum.wii-homebrew.com/: HTTP Error 403: Forbidden`
- `fetch_page 'https://horizon.miraheze.org/wiki/Changing_the_Exception_Han...': page-fetch: https://horizon.miraheze.org/wiki/Changing_the_Exception_Handler_Message: HTTP Error 403: Forbidden`
- `fetch_page 'https://forum.wii-homebrew.com/...': page-fetch: https://forum.wii-homebrew.com/: HTTP Error 403: Forbidden`
- `web_search 'black-before-title boot regression FZDIA...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`

</details>
