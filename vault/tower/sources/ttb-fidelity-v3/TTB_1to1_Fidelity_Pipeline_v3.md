# THE TWO BUILDERS — 1:1 FIDELITY PIPELINE v3.0

**Tipo:** especificación de producción y protocolo de aceptación; no representa funcionalidades implementadas.  
**Destino:** LEGO Star Wars: The Complete Saga, versión **Wii física**; Dolphin actúa como banco de pruebas.  
**Principio rector:** no declarar PASS por semejanza superficial, captura bonita, comportamiento aislado, resultado de PC ni éxito parcial en Dolphin.  
**Objetivo de diseño:** reproducir la identidad y composición de las referencias autorizadas con precisión muy alta. **No se promete pixel-perfect de renders modernos en el motor Wii**.

## A. Congelación de objetivos y límites

1. **Jacobo**: referencia `file_00000000c1c48211809fb06364900755.png` (1448×1086) y/o `1000521173.png` (1536×1152). Cabello negro despeinado en mechones puntiagudos, cejas espesas, ojos oscuros, expresión concreta, túnica marfil, cinturón doble, capa marrón. Separar identidad 3D de portrait prerenderizado.
2. **Madzia**: referencia `file_00000000ce4081f4a5ab024223bac3a8.png` (1448×1086) y/o `1000521170.png` (1536×1152). Pelo rubio dorado largo y suelto con raya central, secciones delanteras, ojos verdes, expresión concreta, túnica marfil, cinturón y capa.
3. **Hub + puerta TTB**: referencia `IMG-20261014-WA0020(1).jpg` (1672×941). Seis puertas originales intactas + séptima TTB en pared curva, letrero TTB / THE TWO BUILDERS, interior espacial azul con planeta y dos figuras, iluminación coherente, trayecto funcional y retorno.
4. **Kitten Call**: referencia `1000521199.png` (1536×1152). Gatos de cuerpo felino legible y colores consistentes, animaciones y FX, activación / reacción / seguimiento / reposo; preservar control de ambos jugadores.
5. **Base observada**: `tbshots.zip`: 42 PNG 1920×1080, 14 resultados, tres frames por resultado, capturados desde Dolphin en GEX44. No hay prueba de Wii física incluida. Registrar los originales con SHA-256 antes de trabajar.

**Regla de honestidad:** clasificar cada propiedad como REFERENCIA, DISEÑADO, CONSTRUIDO, CARGA EN DOLPHIN, FUNCIONA EN DOLPHIN, VALIDADO EN WII, APROBADO VISUALMENTE. No mezclar niveles de evidencia.

## B. Arquitectura: tres carriles inconfundibles

### B1. Art Truth (fuente de verdad visual)
- **Reference Registry:** asset original, hash, propietario, región de interés, resolución, relación de aspecto, versión e interpretación. La fotografía/render original nunca se sobrescribe.
- **Canonical Asset:** modelos `.blend`, UV, atlas, materiales de referencia, rig y montaje, vistas ortográficas, retratos 2D. Canonical no se exporta directamente a Wii como verdad visual definitiva.
- **Feature Contract:** rasgos que NO pueden cambiar (silueta del pelo, iris verdes, posición de las puertas, señalética, etc.) y grados libres limitados (iluminación, simplificación de triángulos y antialiasing).
- **Approvals:** owner sign-off por rostro, pelo, torso, espalda, puerta y gato; la similitud automática NO sustituye el visto bueno.

### B2. Runtime Truth (lo que existe en Wii)
- **Target Registry:** ID y hash de la edición exacta de TCS Wii; región, revisión, executables/archives relevantes; usar copias propias. PC nunca representa automáticamente Wii.
- **Format Lab:** investigación de contenedores DAT, GHG y/o cualquier formato encontrado en esa build; endianess, offsets, padding, tablas de objetos, checksum, referencias, texturas, vértices, skinning y parámetros por material. **No asumir que todos los archivos Wii son GHG-PC**.
- **Round-trip Serializer:** `extract → parse → serialize → rebuild → reload`; los no modificados deben conservar semántica y, donde sea aplicable, igualdad binaria; un fallo debe abortar con diagnóstico.
- **Injection Layer:** selección probada por unidad entre reemplazo de archivo del disco, reconstrucción de contenedor o parche de memoria. Riivolution solo reemplaza archivos de disco, no mágicamente subarchivos dentro de DAT sin reconstruir.
- **Runtime Adapter:** personajes y accesorios ensamblados con anclajes correctos; no alterar huesos ni animaciones originales hasta demostrar estabilidad.

### B3. Proof Truth (evidencia verificable)
- Cada build emite identificadores, parámetros y hashes para generar resultados reproducibles.
- Captura sincronizada antes/después de mismas cámaras, luz, pose, FOV, aspecto y distancia; juego sin HUD salvo tests de HUD.
- Dos perfiles de Dolphin, uno **WII_EQUIVALENT** (nativa, sin mejoras visuales engañosas) y otro **DOLPHIN_HD** (solo diagnóstico/marketing, jamás criterio de Wii).
- Pruebas de ejecución continua, estados, animaciones, límites de cámara, rendimiento, memoria, transición y guardado.
- Ensayos de hardware Wii física con vídeo y logs disponibles; sin esta evidencia no hay `WII_PASS`.

## C. Estructura obligatoria en el repositorio

- `fidelity/references/`: originales inmutables, licencias, SHA-256, máscaras de evaluación.
- `fidelity/contracts/`: contratos visuales JSON/YAML por asset y gating.
- `fidelity/canonical/`: modelos maestros, UV, rigs, PSD/KRA/PNG fuente; previsualizaciones ortográficas.
- `fidelity/exports/pc-research/` y `fidelity/exports/wii-target/`: **nunca mezclar**.
- `fidelity/format-lab/`: notas del formato detectado, pruebas diferenciales y round-trips.
- `fidelity/captures/dolphin-native/`, `fidelity/captures/dolphin-hd/`, `fidelity/captures/wii-hardware/`.
- `fidelity/measurements/`: puntos de referencia, máscaras, silhouettes, errores registrables.
- `fidelity/golden/`: capturas de aceptación con sus condiciones de reproducción.
- `fidelity/reports/`: artefacto por cambio: build, test, métrica, vídeo, foto, fallos y decisión.
- `fidelity/decisions/`: aprobaciones humanas, excepciones y justificación; no se autoaprueban gates.

## D. Contratos visuales a nivel de feature

Cada contrato debe especificar: `asset_id`, `reference_ids`, `source_sha256`, `critical_features`, `known_unknowns`, `allowed_deviation`, `disallowed_shortcuts`, `screenshots_required`, `behavior_required`, `wii_constraints`, `owner_approval`, `runtime_tests`, `metrics`, `status`, `evidence_links`.

### D1. Jacobo (P0)
- Pelo: volumen/silueta oscura, textura de mechones y caída sobre frente; geometría 3D real o pieza equivalente, **no** cambio de color de peinado liso.
- Rostro: distribución de ojos, cejas oscuras gruesas, sonrisa leve; una textura frontal nueva con iluminación neutra y una vista de 3/4 donde la cara siga siendo reconocible.
- Cuerpo: trazos V de túnica marfil, ribete oscuro, mangas, bolsillos/hebillas marrones, capa chocolate; mismas proporciones globales de minifigura que la pareja.
- Función: ciclo idle, caminar, correr, salto, ataque, bloquear, construir, cambio de personaje, pickup, death/respawn, co-op; sin clipping de pelo o capa.
- HUD: retrato hecho a partir del mismo diseño aprobado, no sustituir el modelo con una ilustración diferente.

### D2. Madzia (P0)
- Pelo: largo, suelto, rubio dorado claro, raya central, dos secciones delanteras y parte posterior coherentes; **nunca coleta o casco genérico**.
- Cara: ojos verdes legibles a la resolución de juego, cejas suaves, sonrisa delicada, colocación consistente en UV con cabeza y rendering.
- Rig/capa: comprobar cabello largo vs hombro, brazo alzado, salto, espada y giro; corrección por geometría segmentada si el rígido atraviesa el torso. No fingir simulación física si no está implementada.
- Especial: pose de alzar brazos y secuencia Kitten Call integradas sin secuestrar el control del otro jugador.

### D3. Hub y puerta TTB (P0)
- Seis puertas originales conservadas y funcionales. Séptima puerta correctamente integrada en el arco espacial/arquitectónico de la pared, sin tapar una original.
- Misma escala de moldura, plataforma, perspectiva y separación; rótulo legible TTB / THE TWO BUILDERS; luces verdes, planeta azul, dos siluetas de espaldas con pequeño corazón.
- Escala/hitbox/colisiones: no estorbar circulación ni NPC; entrada/retorno, cámara, música, acceso y guardado coherentes.
- Demostrar plano general de siete puertas de una sola vez **en una captura auténtica del juego**, más vídeo entrando y volviendo por la séptima sin dañar las seis.
- Fallback honesto: si el ejecutable no soporta una séptima ruta, documentar el bloqueo y diseñar ampliación técnica; no reemplazar a escondidas una puerta original ni declarar el gate superado.

### D4. Gatito y Kitten Call (P1)
- Canonical de un gato pequeño real: cuadrúpedo, orejas triangulares, hocico, cola, ojos, proporciones legibles con silhouette test sin texturas.
- Primera aprobación con `single-kitten static pose` bajo luz neutra; NO avanzar a seguidores hasta corregir F3B multicolor y F3C/F4B blancas.
- Atlas y UV con textura verificable mediante checkerboard, paleta controlada, materiales estables bajo iluminación del hub.
- Rig mínimo y animaciones: caminar, trotar, sentarse, girar, salto simple. Si se usa un solo hueso, declararlo solo prototipo, no animación final.
- Invocación: arms-up → spawn FX → aparición → navegación/reacción → despawn o reposo; límites activos medidos, colisiones y vínculo de compañero correctos.

## E. Captura reproducible y medición de fidelidad

### E1. Problema de las fuentes
Referencias: personajes 4:3 (1448×1086), hub panorámico 16:9 (1672×941); Dolphin base 16:9 (1920×1080). Una comparación de píxeles directa no es científicamente válida. Primero registrar cámara/recortes, proporciones, rostro, silueta y perspectiva, después medir.

### E2. Matriz de cámaras (mínimos)
- PERSONAJE: frontal ortográfico, 3/4 izquierdo, perfil, espalda, close-up de cara, primer plano del cabello, idle, caminar, salto, giro, acción con arma, dinámica co-op.
- HUB: plano general exacto de siete puertas, frontal TTB, lateral 3/4 mostrando profundidad, cámara de entrada, cámara de salida, co-op con separación.
- KITTEN: silueta frontal/lateral/arriba, checker UV, albedo neutro, andar, seguir, sentarse, interacción sin enemigos y reacción en combate.
- HUD: 4:3 y 16:9 si el juego los soporta de forma real; safe area en CRT y capturas nativas.

### E3. Comparación multinivel
1. **Geometry Truth**: silueta, distancias relativas, proporciones, posiciones de piezas, OBB/AABB, normales, índice de tris, tangentes si aplica.
2. **Face Identity**: landmarks manuales ojos/cejas/boca, escala relativa de iris, tonos y contraste a resolución de pantalla; subjectivo aprobado por propietario.
3. **Material Truth**: color en espacio consistente, albedo separado de iluminación, ausencia de UV rotas, fugas y colores temporales.
4. **Camera Truth**: marco/perspectiva y field-of-view repetibles; no compensar un mal modelo moviendo la cámara hasta que parezca bueno.
5. **Scene Truth**: ocupación y distribución de puertas/objetos, lectura de rótulo, oclusiones y colisiones.
6. **Animation Truth**: estabilidad temporal, transformación por frame y ausencia de clipping; video obligatorio.
7. **Behavior Truth**: interacción, inputs, transiciones, guardados y cooperativo.
8. **Hardware Truth**: memoria, rendimiento relativo a baseline, carga y estabilidad en Wii real.

### E4. Métricas — orientativas, requieren calibración
- **Geometría**: Silhouette IoU por vista registrada; landmark error normalizado por anchura de cabeza; error de proporciones corporales; todo con rangos y masks documentados.
- **Cara**: distancia de puntos rasgo a rasgo; evaluador humano independiente; no confiar en sistemas de reconocimiento de identidad para caricaturas.
- **Color**: diferencia perceptual en superficies homólogas, sobre tomas de luz calibrada, no fotos arbitrarias.
- **Textura**: cobertura UV, islands, solapamientos intencionales, bleeding, mipmap y atlas budget.
- **Estabilidad temporal**: clipping, oscilación/cambio brusco de material, popping/LOD visible, penetración de capa/pelo.
- **Rendimiento**: frametime P50/P95/P99 y caídas respecto a baseline idéntico, consumo de memoria del juego si instrumentable, no mera resolución de captura.
- **Puerta**: siete entradas detectables y las siete navegables, título legible en resolución nativa y visual de portal equivalente.
- **Criterios del primer sprint (propuestos, NO promesa):** silhouette IoU objetivo inicial ≥0.90 en vistas registradas para pelo y contorno; error de 5 landmarks principales ≤3% del ancho de cara; cero features críticas ausentes; cero penetraciones visibles en suite de animación; cero regresiones de funcionalidad base. Refinar cifras tras benchmark con imágenes pareadas, no maquillar métricas.

### E5. Gate antifraude
- Capturas deben incluir metadata de build, commit, ROM ID y hash, región, Dolphin version, settings exactos, render backend, tick/input replay, cámara y hash de cada asset.
- Reportar nativa y HD **lado a lado**; las mejoras HD no elevan puntuación de hardware.
- La selección automática de tres frames sirve para *muestreo inicial*, nunca para confirmar animaciones. Capturar clips completos (5–15s por estado) y escoger frames de momentos definidos.
- Mostrar siempre `REFERENCE | WII_NATIVE | DIFFERENCE/MASK | HD_DIAGNOSTIC` cuando proceda.
- Cualquier PASS sin evidencia se transforma en `UNVERIFIED`; errores visuales graves se convierten en `FAIL` aunque la modificación cargue.

## F. Gates no negociables

- **G0 INVENTORY**: identificada build Wii/región/hash, se puede arrancar sin modificar; referencias y baseline capturados.
- **G1 FORMAT READ**: localizados archivos reales de modelos y scripts; parseo reproducible, round-trip sin alterar originales.
- **G2 FORMAT WRITE**: un cambio mínimo 3D/textura se reinyecta en Wii y sobrevive a boot, quit y restart; no vale solo PC.
- **G3 JACOBO VISUAL**: cara, pelo, torso/capa, vistas y movimiento aprobado por humano.
- **G4 MADZIA VISUAL**: cara, pelo largo, vistas y movimiento aprobado por humano.
- **G5 CO-OP**: ambos simultáneos, todas las animaciones importantes, sin cámara que pierda la acción.
- **G6 HUB PORTAL**: siete puertas, seis originales intactas, TTB integrada y transición operativa.
- **G7 KITTEN MESH**: gato legible en silueta, correctos UV/materiales y animación propia.
- **G8 KITTEN CALL**: secuencia end-to-end, comportamiento idle y combate, sin daño aliado, límites de instancias.
- **G9 POLISH**: UI 4:3/16:9 si aplica, localización, lighting, HUD y consistencia de materiales.
- **G10 DOLPHIN-NATIVE**: suite determinista con captura reproducible, sin trampas de HD.
- **G11 WII-HARDWARE**: prueba continua física con co-op, vuelta a hub, save/load, nuevas sesiones y caso estrés; rendimiento relativo documentado.
- **G12 RELEASE REVIEW**: validación de assets, diffs, due diligence, rollback y aprobación final. Gate sin prueba = pendiente, no verde.

## G. Dependencias que no pueden saltarse

1. **PARAR expansión estética antes de G2** si ni siquiera sabemos escribir un asset Wii. El carril artístico canónico puede avanzar independientemente, pero nunca se marca integrado.
2. Crear **golden sample** de una textura facial y un cabello rígido con sustitución de mesh y round-trip **en versión Wii**. Describir públicamente que BactaTank Classic soporta PC, no Wii.
3. Validar transformaciones locales/world, orientación de ejes, unidades, jerarquía, vertex winding, normales, handedness, pesos y referencias a materiales; ejecutar importer/exporter differential test.
4. Convertir solo piezas para las que tenemos correspondencia de esqueleto, bindings y materiales; si un cambio altera la cantidad de vértices, validar todos los índices/referencias antes de escribir.
5. Preservar seis puertas y scripts originales; diseñar el séptimo nodo de navegación/trigger como extensión, no sustitución encubierta.
6. Kitten Call debe apoyarse en mecánicas probadas, sin introducir decenas de entidades hasta disponer de presupuesto de carga y frame time.

## H. Backlog priorizado por riesgo y valor

**P0-A**: Build provenance/hashes/región; capturas baseline alineadas; escena de test neutral y cámara grabable; mapa de archivos.  
**P0-B**: Parser/serializer Wii reversible; textura facial sentinel; cabello rígido sentinel; validación en Dolphin nativa y Wii real.  
**P0-C**: Jacobo & Madzia master orthos (primera aprobación por figura); retratos faciales en UV con checksum; mallas capilares; materiales, rigs y clips.  
**P0-D**: Séptima puerta completa, escena, geometría, cartel, textura espacial, trigger, transición, save/return.  
**P1-A**: Kitten silhouette → UV → rig → material → anims → summon → follow → enemies → co-op.  
**P1-B**: UI/hints/controller icons; escenas cinemáticas y coherent art style.  
**P2**: ornamentación secundaria, emoticones, secretos, brillo y pulido fino.

## I. Organización de tareas y evidencia

Cada tarea incluye:
- **Input**: referencia inmutable y asset preciso; build hash y restricciones.
- **Hipótesis**: qué cambio medible debería provocar en pantalla.
- **Superficie**: archivo/material/mesh/ejecutable exacto; impacto estimado y rollback.
- **Prueba**: script de entrada/cámara y assets esperados; caso positivo, caso negativo, regresiones.
- **Output**: binarios parcheados, originales backup, prueba nativa, capturas, vídeo, informe y diff.
- **Criterio de kill**: archivo incompatible, corrupción visual, clipping grave, carga inestable o rendimiento peor que tolerancia calibrada.
- **Status**: `NOT_STARTED | EXPLORING | ASSET_READY | FORMAT_READY | DOLPHIN_LOAD | DOLPHIN_BEHAVIOR | WII_TESTED | OWNER_APPROVED | BLOCKED`.

No usar etiquetas A/B/C aisladas sin explicación. Un `A` de render no equivale a `WII_PASS`. Toda excepción requiere justificante explícito; sin pruebas de ejecución no puede avanzar a terminado.

## J. Matrix de tests mínimos

**Jacobo/Madzia**: idle 30s, walk, sprint, jump, attack, block, build, weapon equip/unequip, death, switch, co-op near/far, cutscene entry/exit. Cada uno con face zoom, side and back.  
**Cabello/capa**: 360° look, giro brusco, brazos elevados, cámara baja, intersección cuello/hombros, pruebas de animaciones concurrentes.  
**Hub**: entrar/salir por I–VI + TTB, unión de cámara/colisión, usar panel de puerta, interrumpir transición, save/load cerca del trigger, dos jugadores simultáneos.  
**Kitten**: load solo, spawn múltiple, despawn, pelea, sin enemigos, límites de tracking, lucha en rincón, escenas con bajo espacio, cambio de personaje, muerte, pausa y nuevo mapa.  
**Persistencia**: tres sesiones de juego independientes con saves duplicados; verificar que no se altera la partida original.  
**Hardware**: sesión sostenida del hub con dos mandos reales, test del peor caso con Kitten Call, entrada TTB y regreso; reportar mínimo y percentiles de frame-time cuando sea medible; registrar abortos/crashes.

## K. Recomendaciones técnicas de calidad para Wii

- Wii dispone de 24 MB MEM1 + 64 MB MEM2 brutos, no memoria libre garantizada para el juego; medir antes de presupuestar geometría o texturas.
- Preferir pocos materiales y pequeñas atlases, reuse sin artefactos, mipmaps coherentes, albedo facial de alto contraste y geometría capilar que lea bien a resolución nativa.
- No usar texturas DDS de PC directamente suponiendo compatibilidad: determinar el formato Wii de cada recurso y su empaquetado/ordenamiento real antes de exportar.
- Retratos/imagen dentro de la puerta pueden ser prerenderizados *dentro* del juego; gameplay debe cumplir sus propias normas 3D; no falsificar captura de juego mediante overlay posterior.
- Generar LOD solo si el motor/asset correspondiente lo admite y comprobar switching; no inventar presupuesto de triángulos sin perf profiling.
- Capturas 1920×1080 generadas por Dolphin pueden verse mucho mejor que 480p nativo por upscale; separar de forma explícita.

## L. Diagnóstico de 14 runs disponibles

| Unidad | Observación de capturas | Acción correctora | Estado |
|---|---|---|---|
| F2A | Hub sin séptima puerta TTB convincente; frame negro en otra captura | Escena siete puertas + trigger verificable, recoger vídeo | FAIL_VISUAL |
| F2B/F2B2/F2B3 | HUD/hints superpuestos y de dev, menú visible | Distinción UI debug/final y safe area | UNVERIFIED_FINAL |
| F2C/F2C2 | Co-op visible, marcador y cortes de cámara no demostrados | Replay de dos mandos y camera acceptance suite | UNVERIFIED |
| F3A/F3B | Gato ausente o monstruo multicolor | Separar geometry / UV / atlas / materiales y refactor | FAIL_VISUAL |
| F3C | Silueta blanca con orejas; cuerpo sin identidad felina | Ref model + silhouette QA | FAIL_VISUAL |
| F4B | Entidad blanca/red de prueba; reproducción aislada | Animación propia y vídeo continuo | PARTIAL |
| F6A/F6A2 | Cambio de escenas/pausa, sin secuencia Kitten Call de 5 estados demostrada | Telemetría de estado y vídeo guiado | UNVERIFIED |
| F6B/F6B2 | Seguimiento no demostrable, hub/cámara interrumpen | Prueba de pathing/target lock y vídeo | UNVERIFIED |
| F6C | Sin capturas | Crear ejecución y evidencia | NO_EVIDENCE |

**No inferir ausencia de código por ausencia de captura**: tratar pruebas no visibles como `UNVERIFIED`.

## M. Definition of Done (no negociable)

1. Jacobo y Madzia reconocibles en *captura auténtica del juego a resolución equivalente Wii*, cara/cabello/apariencia aprobados desde vistas controladas.
2. Compatibilidad con animaciones originales y co-op, cero errores bloqueantes/corrupciones/clipping crítico.
3. Siete puertas del hub, con TTB nueva y seis originales funcionales; composición general y puerta individual aprobadas.
4. Gato visualmente correcto, animado y Kitten Call verificada por vídeo y estado del runtime.
5. Capturas nativas de Dolphin + registros reproducibles + **prueba Wii física**; las imágenes marketing no sirven como prueba.
6. Lista de limitaciones pendientes y excepciones aprobadas, sin afirmaciones de fidelidad pixel-perfect imposibles.
7. Paquete de distribución como parches diferenciales y assets originales propios, no incluir datos propietarios completos del juego; reversión y restauración probadas.

## N. Primera orden de ejecución recomendada (72h de ingeniería, no cronograma garantizado)

**Bloque A — 0–1:** Preservar refs/42 capturas, manifest, status, identificar build Wii exacta, grabar nativa sin mejoras HD, unificar cámaras e inventario de recursos.  
**Bloque B — 1–2:** Localizar un modelo de personaje de Wii y un cabello/cara, inspeccionar estructura y round-trip sin cambio; si falla, investigar parser/compresión hasta un resultado demostrable.  
**Bloque C — 2–3:** Un cambio mínimo reversible de textura/rigid mesh y foto/vídeo en Dolphin Wii + Wii física cuando disponible; construir página de evidence con un mini informe comparativo.  
**Condición de salida:** `G0/G1/G2` aprobados, o bloqueo formal con causa, experimento y siguiente hipótesis. No continuar simulando éxitos visuales si G2 está bloqueado.

---

## Fuentes técnicas contrastadas

- BactaTank Classic (PC-only explícito): https://github.com/AlubJ/BactaTank-Classic
- LEGO Modding Tool, reemplazo de `.PLY` y restricción skinning: https://github-wiki-see.page/m/AlubJ/LEGO-Modding-Tool/wiki/Mesh-Importing
- TTGames Workshop (investigación de formatos, experimental): https://github.com/Loomirr/TTGames-Workshop
- Riivolution, patch format: https://riivolution.github.io/wiki/Patch_Format/
- Memoria Wii: https://wiibrew.org/wiki/Memory_map
- Dolphin, resoluciones y ajustes: https://github.com/dolphin-emu/dolphin/blob/master/Source/Android/app/src/main/res/values/strings.xml

**Última regla:** el pipeline no debe demostrar que *una imagen se ve como el diseño*. Debe demostrar que **el juego de Wii contiene el asset fiel y lo reproduce correctamente en movimiento, con dos jugadores, bajo restricciones de hardware**.
