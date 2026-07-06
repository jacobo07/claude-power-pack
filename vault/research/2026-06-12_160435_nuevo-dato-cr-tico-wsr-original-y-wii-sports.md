# Dato Crítico: WSR Original y Wii Sports — Inventario de Recursos de Ingeniería Inversa

> **Contexto del proyecto:** KobiiSports Resort (Kamek/C++ sobre *Wii Sports Resort*, Game ID **RZTP01**). Este informe consolida el hallazgo crítico — la existencia de **fuentes de símbolos y decompilaciones públicas tanto para *Wii Sports Resort* (WSR) como para el *Wii Sports* original** — y cataloga todos los recursos, formatos y datos forenses asociados que cambian la metodología de RE del proyecto.

---

## 1. Resumen Ejecutivo — Por Qué Esto Es Crítico

El dato nuevo y crítico no es un único hecho, sino un **ecosistema de recursos de símbolos y decompilación** que hasta ahora el proyecto resolvía a mano (campañas v20000.22–v20000.66 de caza de direcciones IOS por probe forense). Los hallazgos clave:

| Hallazgo | Impacto en KobiiSports Resort |
|---|---|
| **`riptl/wii-symbols`** hospeda `symbols/RZTP01.txt` con **3,449 símbolos** de WSR | Fuente directa para resolver nombres/direcciones `RPSysScene`/`Sp2` sin disasm manual |
| Decompilación comunitaria de WSR (`unicycleparrot2/-Wii-Sports-Resort-decompilation`) | Mapa de símbolos en formato parseable, nombres C++ mangled, direcciones absolutas DOL |
| Decompilación clean-room de *Wii Sports* (`doldecomp/ogws`) | Referencia cruzada para estructuras compartidas Wii Sports↔WSR (Bowling, Golf retornan) |
| **Ghidra-GameCube-Loader (Cuyler36)** con lenguaje Gekko/Broadway | Soporta paired-single instructions ausentes en Ghidra stock; importa los símbolos anteriores |
| Símbolos hermanos: *Wii Sports* **RSPE01** (2,312), *Wii Play* **RHAP01** (1,930) | Triangulación cruzada de funciones compartidas del SDK RVL |

**Conclusión estratégica:** la metodología de probe-forense ciego (PRE_CALL/POST_CALL watchdog, eliminación de direcciones por retorno-poison `0xCD000000`) puede ahora **complementarse o validarse** contra símbolos nombrados. Esto NO reemplaza la verificación en silicio (RULE-105 Silicon Provenance Gate sigue vigente: GEX44≠real-hw), pero **reduce drásticamente el espacio de búsqueda** y ofrece *ground truth* para los nombres de funciones del compositor de título — precisamente el muro AP-009 (Sp2TitleLayoutDraw) que bloquea el render de overlays.

---

## 2. Identidad de Disco y Códigos de Masterización

### 2.1 Serials confirmados

| Región | Serial | CRC32 | Tamaño | Códigos doc. | Idiomas |
|---|---|---|---|---|---|
| Europa/PAL | **RZTP01** | `56408F3E` | 4483 MB | 29 | En,Fr,De,Es,It |
| USA v1.00 | **RZTE01** | `C0171BCC` | 4483 MB | 38 | En,Fr,Es |
| Japón (master) | RVL-RZTP-0A-0 JPN S0 | — | — | — | — |

> **Nota de coherencia con el proyecto:** el CLAUDE.md del repo exige Disc ID **RZTP01** (KBSE/KBSE = fallo silencioso de carga del módulo). El serial confirmado **RZTP01 = Europa/PAL** alinea con el target `--region PAL`. El serial USA es **RZTE01** (no RZTP01); cualquier inyección sobre disco USA requeriría re-targeting.

### 2.2 Masterización física (redump ring data)

- **Prefijo estable:** `RZTP` = Resort; sufijo `01` = variante de región.
- Master JPN **RVL-RZTP-0A-0 JPN S0** confirmado en los **16 anillos de prensado japoneses** documentados.
- Evolución de mastering codes: `109F1804`/`209F` (2009, IFPI LQ11/LQ12) → `309G`/`309H` (IFPI LL38).
- **Revisión PAL documentada:** `RVL-RZTP` (Cover ID RVL-RZTP-STA, Manual RVL-RZTP-NOE, mastering **RVL-RZTP-0A-1 JPN**, hecho en Japón).
  - Track MD5 `1f33c715abd56f36db5b66b8d7000c7b`
  - SHA-1 `ba229eb780d07618dc56e4210bf481e80ce8cf14`
  - CRC-32 `c6628cc4`
  - Esta revisión **modifica la partición de update + el programa del Wii MotionPlus Instructional Video**.

> ⚠️ Existen **dos huellas PAL distintas** en los learnings: CRC32 `56408F3E` (imagen completa) y CRC-32 `c6628cc4` (track de la revisión con update modificado). Verificar cuál corresponde al golden DOL del proyecto (`f7eeb69dc44cef6f661b805b379632c0` es el boot.dol del patcher RSA, no la imagen de disco).

---

## 3. Recursos de Símbolos (el núcleo del dato crítico)

### 3.1 `riptl/wii-symbols` (GitHub)

- Ruta directa: **`symbols/RZTP01.txt`** → **3,449 símbolos** de WSR.
- Títulos hermanos en el mismo repo:
  - *Wii Sports* **RSPE01** → 2,312 símbolos
  - *Wii Play* **RHAP01** → 1,930 símbolos
- **Uso inmediato:** resolución de nombres/direcciones de `RPSysScene` y `Sp2` (scene-manager) durante disassembly — exactamente el dominio donde el proyecto invirtió múltiples ciclos.

### 3.2 Decompilación comunitaria de WSR

- Repo: **`github.com/unicycleparrot2/-Wii-Sports-Resort-decompilation`**
- Formato de mapa de símbolos (una línea por símbolo):

  ```
  symbol_name = section:address; // type:function size:0xNN scope:global align:N data:...
  ```

- **Nombres C++ = mangled** (Itanium/CFront-style). Ejemplo real:

  ```
  __dt__13mDoExt_bckAnmFv = .text:0x800DD2EC; // type:function size:0x5C scope:global align:4
  ```

- **Direcciones DOL = absolutas** (`0x8000xxxx`); **direcciones REL = relativas a sección**.

#### Atributos de símbolo soportados

| Atributo | Significado |
|---|---|
| `type` | function / object / label |
| `size` | tamaño en bytes (`0xNN`) |
| `scope` | global / local / weak |
| `align` | alineación |
| `data` | tipo de dato |
| `force_active` | anti-deadstrip; añade a `FORCEACTIVE` en `ldscript.lcf` |
| `noreloc` | sin relocación |
| `noexport` | no exportar |
| `stripped` | rastrea símbolos que afectan el **bug de inflación de BSS común** aun ausentes del binario final |

> **Aplicación al proyecto:** el formato `nombre = sección:dirección` es directamente importable como mapa de símbolos en Ghidra (via GameCube-Loader) o como tabla de lookup para sustituir el `externals/PAL.txt` artesanal. El flag `stripped` explica por qué ciertas direcciones aparecen/desaparecen entre binarios — relevante para el RULE-106 "binary residue gap" (FZDIAG-on vs FZDIAG-off, +24B kamek non-determinism).

### 3.3 Decompilación clean-room de *Wii Sports* (`doldecomp/ogws`)

- WIP clean-room; **NO contiene assets ni ensamblador del juego**.
- Target soportado: **US Revision 1** (SHA-1 `8bb422971b88b5551a37de98db69557df7b46637`, build 2007/07/05). Rev 0 = 2006/10/07.
- **Doctrina legal explícita y crítica para el proyecto:**
  - Debug info dejado en retail (mapas linker/símbolos, debug builds, `.o`/`.a`) **NO se considera "material filtrado"** y es **permisible** para RE.
  - **SDK source filtrado SÍ está prohibido.**

> Esto valida legalmente el uso de `riptl/wii-symbols` y los mapas de decomp: son debug-info derivado del retail, no SDK filtrado.

---

## 4. Tooling de Ingeniería Inversa

### 4.1 Ghidra-GameCube-Loader (Cuyler36)

- Añade **loader** para binarios Wii DOL/REL/Apploader.
- Añade **definición de lenguaje Gekko/Broadway PowerPC** con soporte de **paired-single instructions** (ausentes en Ghidra stock — crítico para float-heavy code PPC 750CL).
- **Importa mapas de símbolos** de juegos que envían debugging symbols.

### 4.2 Catálogos de juegos con símbolos

- Dolphin-emu wiki: lista *"Ships with Debugging Symbols"*.
- `retroreversing.com/wii-debug-symbols`.

### 4.3 Herramientas de assets mencionadas (TCRF, *Wii Sports* no Resort)

- **BrawlCrate**, **Kuriimu**, **Switch Toolbox**.
- ⚠️ Recordatorio del proyecto: BrawlCrate-exported BRRES dispara el **nw4r patricia trap** (`ResFile::GetResMdl(const char*)` falla → usar walker directo).

---

## 5. Framework de Scene-Hooking (PackProject/Caddie)

Relevante directamente porque KobiiSports Resort corre como overlays sobre `SCENE_TITLE`.

### 5.1 `caddieSceneHookMgr.h`

- Struct **`SceneHook`** = cuatro punteros a función `SceneCallback`, tipados `void(*)(RPSysScene*)`:
  - `onConfigure`
  - `onCalculate`
  - `onUserDraw`
  - `onExit`
- **`SceneHookMgr`** = singleton que mapea hooks por **`RPSysSceneCreator::ESceneID`**.
- Sentinel **`SCENE_ALL`** → enruta a `mGlobalSceneHook` (separado del array per-scene `mSceneHooks[SCENE_MAX]`).
- Sentinel **`SCENE_MAX`** = tamaño del array.

### 5.2 Dispatch y pausa

- Enum `RPSysSceneCreator::ESceneID` desde `RP/RPSystem.h`.
- Permiso de pausa por escena: `bool mPauseSetting[SCENE_MAX]` (default `true`).
- Entry points estáticos de dispatch:
  - `DoConfigure` / `DoCalculate` / `DoUserDraw` / `DoExit` / `DoUpdatePause`.

> **Correlación con el bug abierto del proyecto:** el orden de draw es el muro. El proyecto observó (AP-009) que el **compositor de título WSR dibuja DESPUÉS de la cadena Caddie OnUserDraw** → frames blancos. Con la estructura `SceneHook`/`SceneHookMgr` confirmada y los **3,449 símbolos de RZTP01**, ahora es posible localizar la función real del compositor (`Sp2TitleLayoutDraw` o equivalente) por nombre en lugar de por disasm ciego. **El SERP NO devolvió la dirección directa** — debe extraerse del mapa de símbolos real (ver §8).

---

## 6. Estructuras de RAM en Vivo y Gecko/Memory Codes

Códigos region-specific revelan estructuras de estado residentes en MEM1 durante título/flyover:

| Dirección / Offset | Uso |
|---|---|
| **`0x0086E454`** (base RAM aprox.) | Puntero de button-state / dirección de condición en control P1 Wiimote e Island Flyover Teleporter |
| `0x00D2E194`–`0x00D2E19C` | Datos de posición |
| `0x00CFC0A0`–`0x00CFC0A8` | Datos de posición |

> Estas direcciones son **fuentes de estado en vivo verificadas** durante la escena título/flyover — útiles para anclar la lectura de input fresco (N10 Input Freshness) y para validar dónde reside el estado del juego frente a las direcciones IOS cazadas por probe.

---

## 7. Ecosistema de Modding y Provenance

### 7.1 Modding ecosystem

- Centro: **GameBanana "WSR Hub"** (Wii Sports Resort Modding Community).
- Repo de archivos Wii/GameCube hospedado en **copyparty**.
- **Discord** para soporte de modders y updates del repositorio.

### 7.2 Parcheo RSA (CMOC Miis)

- WSR usa **verificación RSA** sobre contenido descargado (CMOC Miis).
- Un **patcher comunitario reescribe la clave pública RSA** de WSR por una custom → elimina el requisito previo de lanzar vía **USB Loader/cIOS** para descargas de Mii por Disc Channel.
- boot.dol del patcher: md5 **`f7eeb69dc44cef6f661b805b379632c0`**.

### 7.3 Prerequisito homebrew

- Ejecutar código no firmado requiere **modificar la consola primero**.
- Referencia canónica: **Wii Hacks Guide** (`wii.hacks.guide`) — cubre Wii, vWii, Wii mini.

### 7.4 Ficha del juego (provenance)

- *Wii Sports Resort* (2009, **Nintendo EAD**, director **Yoshikazu Yamashita**, producer **Katsuya Eguchi**).
- **12 deportes** en **Wuhu Island**; **primer juego first-party que requiere Wii MotionPlus**.
- Solo **Bowling y Golf** retornan del *Wii Sports* original (2006); tennis, baseball y boxing fueron removidos.
- Ventas: **33.14 millones** de copias (al 31 marzo 2021).

> El solapamiento Bowling/Golf entre *Wii Sports* (RSPE01) y WSR (RZTP01) es la **ruta de mayor valor para triangulación cruzada de símbolos** — funciones compartidas o cercanas en ambos binarios validan nombres recuperados.

---

## 8. Brecha Identificada — Lo Que el SERP NO Devolvió

Hallazgo honesto y crítico de método:

- El SERP **NO devolvió direcciones directas de símbolos** para:
  - `SCENE_TITLE`
  - Layout `Sp2`
  - Funciones de la cadena de draw del compositor
- Solo se surfó la **documentación del formato** del mapa de símbolos y notas de TCRF sobre *Wii Sports* (no Resort) referenciando BrawlCrate/Kuriimu/Switch Toolbox.

**Implicación operativa:** las direcciones del compositor de título **deben extraerse de los archivos de mapa de símbolos reales** del repo de decomp (`unicycleparrot2/...`) o de `riptl/wii-symbols/symbols/RZTP01.txt` — **no existen pre-indexadas en SERP**. El próximo paso forense es clonar/leer esos mapas y grep por `Sp2`, `Title`, `Layout`, `Draw`, `Scene`.

---

## 9. Soluciones y Próximos Pasos Que Quizá No Consideraste

> Marcado como recomendación proactiva; algunas con componente especulativo (flag explícito).

1. **Sustituir/aumentar `externals/PAL.txt` con `RZTP01.txt` (3,449 símbolos).** El proyecto mantiene un `PAL.txt` artesanal con direcciones verificadas una a una. Importar el mapa de 3,449 símbolos como **capa de hipótesis** (no de verdad — RULE-105 sigue: cada símbolo es hipótesis hasta validación en silicio) acelera la resolución de la cadena de draw. *Riesgo:* el mapa puede no ser bit-exacto contra tu pressing PAL específico; verificar contra la huella `56408F3E`/`c6628cc4`.

2. **Cross-validar las direcciones IOS cazadas (v20000.53–66) contra `RZTP01.txt`.** Tienes `IOS_Open=0x8003b1f0`, `IOS_Write=0x8003b7a0`, `IOS_Ioctl=0x8003bbc0`, `IOS_Ioctlv=0x8003bf20` verificadas por probe en silicio. Si el mapa de símbolos las nombra, confirmas el cluster libogc por *ground truth* — y si NO las nombra (probable, son libogc internas), eso **refuerza** tu hallazgo de que el WSR DOL bundlea un cluster libogc no exportado.

3. **Atacar el muro AP-009/compositor por nombre, no por disasm.** Grep `RZTP01.txt` por el patrón del `Sp2TitleLayoutDraw`. Con la estructura `SceneHook` (onUserDraw) confirmada y el dispatch `DoUserDraw`, puedes localizar exactamente dónde el compositor de título se inserta en la cadena → el entry point para suprimir/reordenar el draw que produce frames blancos.

4. **[Especulativo] Triangular Bowling/Golf entre RSPE01 y RZTP01** para recuperar nombres de funciones de física/cámara compartidas — útil si KobiiSports añade deportes que mimetizan WSR (N20 Mimetismo Obsesivo exige ≥3 análogos WSR). *Especulación:* el grado de reutilización de código EAD 2006→2009 es desconocido; podría ser alto (engine RP compartido) o bajo (reescritura MotionPlus).

5. **Importar todo en Ghidra-GameCube-Loader** para obtener decompilación con paired-singles correctos — el `make.py --region PAL` del proyecto y el análisis de float-heavy hot-paths (16.6ms/frame, no double) se benefician de ver las instrucciones paired-single reales que Ghidra stock no decodifica.

6. **Registrar el formato `stripped`/`force_active` como lente para RULE-106.** Tu "binary residue gap" (FZDIAG removido = −324 instrs en KobiiOnConfigure, bug latente desenmascarado) tiene un análogo conocido: el **bug de inflación de BSS** que el flag `stripped` rastrea. Vale auditar si tu non-determinism +24B kamek correlaciona con símbolos `stripped`/`force_active` mal manejados.

---

## 10. Tabla Maestra de Recursos (Referencia Rápida)

| Recurso | Ubicación | Contenido | Uso primario |
|---|---|---|---|
| Símbolos WSR | `riptl/wii-symbols` → `symbols/RZTP01.txt` | 3,449 símbolos | Resolver RPSysScene/Sp2 |
| Símbolos Wii Sports | mismo repo → RSPE01 | 2,312 símbolos | Triangulación cruzada |
| Símbolos Wii Play | mismo repo → RHAP01 | 1,930 símbolos | Triangulación SDK RVL |
| Decomp WSR | `unicycleparrot2/-Wii-Sports-Resort-decompilation` | Mapa símbolos mangled, dir. absolutas DOL | Importar a Ghidra / lookup |
| Decomp Wii Sports | `doldecomp/ogws` | Clean-room, US Rev1 | Referencia legal + estructuras |
| Loader Ghidra | Ghidra-GameCube-Loader (Cuyler36) | DOL/REL/Apploader + Gekko paired-singles | Disasm/decompile |
| Catálogo símbolos | dolphin-emu wiki / retroreversing.com | "Ships with Debugging Symbols" | Descubrir más símbolos |
| Framework hooks | PackProject/Caddie `caddieSceneHookMgr.h` | SceneHook/SceneHookMgr | Overlay en SCENE_TITLE |
| Modding hub | GameBanana "WSR Hub" + Discord + copyparty | Repo archivos, soporte | Assets/comunidad |
| RSA patcher | boot.dol md5 `f7eeb69dc...` | Reescribe clave RSA | CMOC Mii sin cIOS |
| Guía homebrew | `wii.hacks.guide` | Wii/vWii/Wii mini | Prerequisito ejecución |

---

## 11. Síntesis Final

El "dato crítico" reposiciona la estrategia de RE del proyecto de **caza ciega de direcciones** (donde invertiste ~13 ciclos forenses v20000.x) hacia **RE asistida por símbolos nombrados**, con tres salvaguardas que el proyecto ya tiene codificadas y que **siguen siendo vinculantes**:

1. **RULE-105 (Silicon Provenance Gate):** todo símbolo del mapa es hipótesis hasta validación en silicio físico (GEX44/Dolphin ≠ real-hw). Los 3,449 símbolos **no anulan** la necesidad de boot en Wii real.
2. **Doctrina legal (`ogws`):** debug-info retail es permisible; SDK filtrado no. Los recursos catalogados caen del lado permisible.
3. **Brecha SERP:** las direcciones del compositor de título **no están pre-indexadas** — el siguiente paso concreto es clonar `riptl/wii-symbols` y `unicycleparrot2/...`, grep por `Sp2`/`Title`/`Layout`/`Draw`, y cross-validar contra tu `PAL.txt` y tus direcciones IOS verificadas.

El mayor desbloqueo potencial es **AP-009**: con `SceneHook.onUserDraw`/`DoUserDraw` confirmados y 3,449 símbolos disponibles, el muro del compositor que produce frames blancos pasa de "Ghidra Sp2TitleLayoutDraw suppression" especulativo a **una búsqueda por nombre en un mapa de símbolos existente**.

## Sources

- <https://gamebanana.com/games/6332>
- <https://mariocube.com/>
- <https://wii.hacks.guide/>
- <https://oscwii.org/library/app/WSR-Patcher>
- <http://redump.org/disc/10334/>
- <https://wiki.raregamingdump.ca/index.php/Wii_Boot_Process>
- <https://wiird.gamehacking.org/forum/index.php?topic=4058.0>
- <https://github.com/riptl/wii-symbols>
- <https://www.reddit.com/r/wii/comments/15gkm6d/is_wii_sport_resort_better_than_wii_sports/>
- <https://en.wikipedia.org/wiki/Wii_Sports_Resort>
- <https://www.youtube.com/watch?v=l7IIlt9dN2o>
- <https://github.com/PackProject/Caddie/blob/main/include/caddie/core/caddieSceneHookMgr.h>
- <https://github.com/unicycleparrot2/-Wii-Sports-Resort-decompilation/blob/main/docs/symbols.md>
- <https://gamehacking.org/system/wii/wii%20sports%20resort>
- <https://archive.org/download/SP2E01>
- <https://github.com/doldecomp/ogws>
- <http://redump.org/disc/51199/>
- <https://frds.github.io/wii/>
- <https://wiibrew.org/wiki/Using_Ghidra_with_the_Wii>
- <https://www.retroreversing.com/wii>
- <https://tcrf.net/Notes:Wii_Sports>
- <https://www.reddit.com/r/WiiHombrewDevelopment/comments/1clz07v/compiling_wii_sports_from_decomp/>

## Run metadata

- **Prompt:** Nuevo dato crítico: WSR original y Wii Sports
- **Depth / breadth:** 2 / 3
- **Queries used:** 6 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: bs4-strip, readability, trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 553.9 s
- **Errors during run:** 3
- **Started at:** 2026-06-12T14:04:35Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://lavarda.org/wiimodding.html...': page-fetch: https://lavarda.org/wiimodding.html: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1010)>`
- `fetch_page 'https://archive.org/download/rr-nintendo-wii-e3/europe-pal/W...': page-fetch: https://archive.org/download/rr-nintendo-wii-e3/europe-pal/Wii%20Sports%20Resort%20%5BRZTP01%5D.7z/: HTTP Error 404: Not Found`
- `fetch_page 'https://wiisports.fandom.com/wiki/Wii_Sports_Resort...': page-fetch: https://wiisports.fandom.com/wiki/Wii_Sports_Resort: HTTP Error 403: Forbidden`

</details>
