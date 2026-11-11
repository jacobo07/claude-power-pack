"""Write prompts/GNN.txt for G08-G27 from the doc's prompt bodies + one shared tail.

The tail fixes the evidence scale (G01-G06 answers inverted it) and pins the id prefix.
Usage: python make_prompts.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "prompts"

TAIL = """
Investiga con búsqueda web real y abre cada página que cites. No inventes URLs: si no abriste la página, no la cites.
Restricciones: solo fuentes primarias cuando existan; nunca código filtrado del SDK de Nintendo ni enlaces a él; marca lo no verificado.

ESCALA DE EVIDENCIA (obligatoria, no uses otra): E1 = sin fuente o inferencia propia; E2 = fuente secundaria (blog, foro, curso, gist, resumen); E3 = fuente primaria abierta y leída (paper, repo oficial, manual del fabricante); E4 = reproducido compilando con mwcc. Tú nunca puedes poner E4.

FORMATO DE SALIDA: (1) informe de máx. {words} palabras; (2) un único bloque ```jsonl con un objeto por línea con estos campos: {schema}. Todos los ids deben empezar por {gid}. evidence_grade solo puede ser E1, E2 o E3.
"""

CTX = "Contexto: hago matching decompilation clean-room de juegos de Wii compilados con Metrowerks CodeWarrior (mwcceppc, PowerPC Broadway). Herramientas: decomp-toolkit (dtk), objdiff, m2c, decomp-permuter. Una función solo cuenta si mi C compila a bytes idénticos."

P = {}
P["G08"] = (1500, '{"gap":"G08","id":"G08-001","error_class":"","error_text":"","trigger_c":"","fix_c":"","codegen_preserved":true,"m2c_cause":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Compilo salida de m2c con mwcceppc y obtengo errores agrupados en 7 clases: "pointer expected" sobre long, conversión implícita void*->long, "not a struct/union", operandos ilegales void*+long y void*+int, identificador no definido, declaración de tipo desconocido. Editar función por función con un LLM tuvo un éxito de 0-2%.

Investiga a fondo:
1. Texto exacto y significado de estos mensajes de error de mwcceppc (y sus códigos), y qué construcciones de C los disparan.
2. Para cada clase, la reparación que preserva el codegen original (cast explícito, typedef de puntero, struct mínimo con campos en sus offsets, extern con prototipo) y cuáles cambian el asm.
3. Defectos conocidos de m2c que producen estas clases (issues del repo matt-kempster/m2c) y flags de m2c que los evitan (--valid-syntax, --void, --struct-field-inference, contexto de tipos).
4. Si los proyectos decomp usan un fichero de contexto compartido (ctx.c, headers por TU) y cómo lo generan.""")
P["G09"] = (1500, '{"gap":"G09","id":"G09-001","claim":"","pattern":"","conflict_signal":"","resolution":"","example_project_file":"","source_url":"","evidence_grade":""}', CTX + """ Cuando arreglo el tipo de un campo en una TU para que una función matchee, otra TU que usa el mismo struct deja de compilar o de matchear (112 conflictos). Necesito un modelo único de tipos para todo el programa.

Investiga a fondo:
1. Cómo gestionan los proyectos decomp grandes (tp, mkw, ssbm, pikmin2) los headers compartidos y las definiciones provisionales de structs (unk_0x10, pad[]).
2. Patrones legítimos para que un struct parcialmente conocido sirva a varias TUs (campos unk, unions, tipos opacos, forward declarations).
3. Cuándo un conflicto de tipos entre TUs indica que son dos structs distintos y no uno (herencia C++, versiones de un mismo struct, structs locales a una TU).
4. Algoritmos para fusionar evidencias de layout de muchas funciones en un solo struct (unificación, lattice de tipos).""")
P["G10"] = (1200, '{"gap":"G10","id":"G10-001","m2c_case":"","binary_signal":"","local_fix":"","global_side_effect":"","source_url":"","evidence_grade":"","test":""}', CTX + """ m2c deja tipos `?` (desconocidos) en su salida. Una reescritura global de `?` hace compilar 253 de 336 funciones, pero altera 178 funciones que ya matcheaban, así que solo puedo usarla función por función.

Investiga a fondo:
1. Qué significa exactamente `?` en m2c, en qué casos lo emite y qué opciones o contexto lo reducen.
2. Estrategias publicadas para resolver `?` (contexto de tipos, --globals, inferencia de struct, preferencia por s32/void*/f32 según uso).
3. Cómo aplicar una reparación de forma local (scope de función, casts) sin cambiar declaraciones compartidas.
4. Issues y PRs relevantes del repo de m2c.""")
P["G11"] = (2000, '{"gap":"G11","id":"G11-001","topic":"mangling|vtable|ctor_dtor|rtti|extab|template","claim":"","cpp_example":"","asm_or_symbol_effect":"","compiler":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Los juegos están en C++. Mi lane C++ certifica pocas funciones y no tengo bien resueltos mangling, vtables, constructores/destructores ni tablas de excepciones.

Investiga a fondo:
1. Esquema de mangling de CodeWarrior (no Itanium): reglas, ejemplos, demanglers existentes (cwdemangle, dtk) y diferencias entre versiones.
2. Layout de clases: vtable pointer al final o al principio, herencia múltiple, thunks, RTTI (__RTTI__), destructores con flag (__dt con parámetro short), __ct, new/delete.
3. extab y extabindex: cuándo se generan, cómo afectan al match y cómo los tratan dtk y objdiff.
4. Templates e inlines de clase: dónde se emiten (weak, COMDAT), duplicados entre TUs, orden.
5. Guías de C++ de proyectos decomp (tp, mkw, ogws, spm, pikmin2).""")
P["G12"] = (2000, '{"gap":"G12","id":"G12-001","claim":"","dtk_feature_or_file":"","binary_signal":"","failure_mode":"","fix":"","dtk_version":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Uso dtk v1.8.x. Mi stage de build fijado solo incluía 304 de los 877 objetos que dtk genera, y 2,837 funciones quedaron sin objeto objetivo. Quiero dominar el splitting para cualquier juego de Wii.

Investiga a fondo:
1. Cómo funciona el análisis y splitting de dtk: config.yml, splits.txt, symbols.txt, detección de límites de función y de TU, .init, .ctors/.dtors, extab, REL modules.
2. Cómo inferir límites de TU y orden de enlace desde el binario (alineación, padding, cambio de pools de constantes, orden de .sdata2, cadenas del linker map si existe).
3. Flujo de dtk-template (configure.py, objetos Matching/NonMatching, progress) y cómo añadir objetos sin romper los ya matcheados.
4. Errores comunes de splitting y cómo los detectan otros proyectos (huecos, funciones partidas, data mal asignada).""")
P["G13"] = (1200, '{"gap":"G13","id":"G13-001","claim":"","objdiff_behavior":"","safe_condition":"","unsafe_condition":"","source_url":"","evidence_grade":"","test":""}', CTX + """ A veces una función matchea solo si renombro un símbolo (extern, data label) o lo trato como alias de otro. Necesito una regla segura para aceptar eso sin fake matches.

Investiga a fondo:
1. Cómo compara objdiff las relocaciones y los símbolos (por nombre, por destino, por sección+offset) y qué opciones de config lo cambian. Incluye el issue encounter/objdiff#393 si sigue abierto.
2. Cuándo dos símbolos son el mismo objeto (aliases del linker, weak, COMDAT, static duplicados) y cuándo no.
3. Prácticas de proyectos decomp para nombrar símbolos desconocidos (fn_8001..., lbl_, @1234) y migrarlos sin romper matches.""")
P["G14"] = (1500, '{"gap":"G14","id":"G14-001","section":"","c_pattern":"","emission_rule":"","verification":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Hoy certifico por función (.text). Quiero llegar a match de objeto completo, incluyendo .data, .rodata, .sdata, .sdata2, .bss, strings y tablas de salto.

Investiga a fondo:
1. Cómo emite mwcceppc tablas de switch (jumptable en .data), strings (pooling, @stringBase0), constantes float y arrays const.
2. Orden de los datos dentro de la sección según orden de declaración, uso o inicialización; efecto de static vs global.
3. Cómo verifican los proyectos decomp el match de datos (objdiff data diff, sha1 del DOL final) y qué trucos usan (#pragma section, __declspec(section)).""")
P["G15"] = (2000, '{"gap":"G15","id":"G15-001","operator":"","c_before":"","c_after":"","targets_residual":"regalloc|order|insert_delete|branch|type","in_permuter":true,"compiler_specific":"","source_url":"","evidence_grade":""}', CTX + """ Tengo un motor de búsqueda con 11 operadores de reescritura de C (swap if/else, invertir comparación, conmutar operandos...) a profundidad 3. En la mitad de los casos agota el espacio sin ganancia. Necesito ampliar el vocabulario de operadores, no reordenar la búsqueda.

Investiga a fondo:
1. Lista completa de transformaciones de decomp-permuter (simonlindholm/decomp-permuter): cada randomización, su peso y su efecto típico; cómo puntúa candidatos. Lee el código de los randomizers.
2. Transformaciones manuales que los matchers aplican y no están en el permuter (introducir temporales, mover declaraciones, cambiar tipo de índice, for<->while, do{}while(0), casts de signo, reordenar campos de expresión, macros inline).
3. Trabajo académico relacionado: síntesis guiada por contraejemplo, superoptimización, equality saturation (egg) aplicada a matching.
4. Qué operadores son específicos de PPC/mwcc frente a IDO/GCC.""")
P["G16"] = (1500, '{"gap":"G16","id":"G16-001","residual_class":"","diff_signature":"","discriminating_feature":"","recommended_fix_family":"","source_url":"","evidence_grade":""}', CTX + """ Quiero clasificar automáticamente por qué una función compilada no matchea (registros, orden, instrucción extra, tipo, relocación, constante, stack frame) para elegir la reparación correcta. Mi primer selector sobreajustó (5/5 en un grupo, 1/4 en otro).

Investiga a fondo:
1. Qué información de diff expone objdiff (CLI, JSON, tipos de diferencia: arg mismatch, opcode, insert/delete, replace) y cómo calcula el porcentaje.
2. Taxonomías de diferencias usadas por herramientas decomp (asm-differ, decomp.me scoring, permuter scoring).
3. Señales que distinguen un residuo de regalloc de uno de scheduling o de tipo.
4. Métodos para validar un clasificador sin sobreajuste (holdout por familia/TU, no por fila).""")
P["G17"] = (1500, '{"gap":"G17","id":"G17-001","construct":"","asm_signature":"","c_reproduction":"","compiler":"","source_url":"","evidence_grade":"","test":""}', CTX + """ En 55 funciones mi motor no encuentra ningún operador aplicable o el camino nunca se alcanza: el asm original sugiere una forma de fuente que mi gramática no genera.

Investiga a fondo:
1. Construcciones de C/C++ que producen asm característico en mwcceppc y que un decompilador no suele emitir: inline asm (asm{} y asm functions), volatile, goto, comma operator, do{}while(0), asignación dentro de condición, ternarios anidados, macros con efectos, bool vs int, enums de 8 bits, struct copy, alloca, __builtin, intrínsecas (__fabs, __frsqrte, __cntlzw, __lhbrx).
2. Para cada una: patrón de asm que la delata y fuente que lo reproduce.
3. Funciones "asm" escritas a mano en el SDK y librerías: cómo reconocerlas y cómo las tratan los proyectos (asm functions en C, .s).""")
P["G18"] = (1500, '{"gap":"G18","id":"G18-001","project":"","repo_url":"","game":"","platform":"wii|gc","version":"","progress_pct":null,"license":"","compiler":"","libraries":[],"reuse_policy":"","source_url":"","evidence_grade":""}', CTX + """ Construyo un índice de donantes cross-title: si una función de librería o motor ya está matcheada en un proyecto público clean-room, quiero reutilizar esa fuente (con su licencia y procedencia) en otro juego.

Investiga a fondo:
1. Inventario de proyectos de decompilación públicos de Wii y GameCube (doldecomp, zeldaret, decomp.dev y otros): nombre, repo, juego, región/versión, % de progreso, licencia, compilador, librerías incluidas (RVL SDK, NW4R, EGG, MSL, Runtime, TRK, HBM, JSystem).
2. Cuáles comparten librerías con Wii Sports / Wii Sports Resort / Wii Play / Wii Fit (EGG, NW4R, RP*).
3. Política legal de cada proyecto sobre reutilizar su código y sobre fuentes del SDK.
4. Recursos agregados (decomp.dev, decomp.me presets) que listen compilador y flags por proyecto.""")
P["G19"] = (1800, '{"gap":"G19","id":"G19-001","library":"","module":"","version_string":"","games":[],"matched_in_project":"","detection_method":"","source_url":"","evidence_grade":""}', CTX + """ Una gran parte del DOL es código de librería (RVL SDK: OS, GX, VI, PAD, WPAD, KPAD, DVD, NAND, AX, SC, WENC; NW4R: g3d, lyt, snd, ut, math, ef; EGG; MSL_C; Runtime.PPCEABI.H; MetroTRK; HomeButtonMenu; RVLFaceLib). Quiero restar esa masa conocida antes de gastar esfuerzo en código de juego.

Investiga a fondo:
1. Versiones de cada librería distribuidas a lo largo de la vida de la Wii (2006-2012), cómo se identifica la versión desde cadenas embebidas en el DOL (p. ej. "<< RVL_SDK - OS release build: ... >>") y qué juegos usan cuál.
2. Qué proyectos públicos clean-room tienen matcheadas esas librerías y en qué versión.
3. Herramientas para detectar librerías por firma (dtk signatures, FLIRT-like, Ghidra FID) y su precisión.
4. Estimación de qué fracción típica del .text de un juego Wii es librería.""")
P["G20"] = (1500, '{"gap":"G20","id":"G20-001","technique":"","normalization":"","reported_precision":"","ppc_applicable":true,"false_positive_mode":"","source_url":"","evidence_grade":""}', CTX + """ Quiero emparejar funciones entre distintos juegos Wii y entre versiones del mismo juego para reutilizar fuentes ya matcheadas, sin aceptar donantes falsos.

Investiga a fondo:
1. Cómo genera y aplica firmas dtk (signatures, normalización de relocaciones, máscaras) y su tasa de falsos positivos.
2. Técnicas de function matching binario: BinDiff, Diaphora, FunctionSimSearch, Ghidra BSim/FID, hashing de CFG, embeddings (Asm2Vec, jTrans, SAFE). Precisión en PPC.
3. Normalizaciones correctas para PPC/mwcc: direcciones, registros, offsets de relocación, orden de bloques.
4. Protocolo para validar un donante (compilar su fuente con el perfil del juego destino y exigir bytes idénticos).""")
P["G21"] = (1500, '{"gap":"G21","id":"G21-001","game":"","subsystem":"","evidence":"símbolo|rtti|formato|doc","claim":"","source_url":"","evidence_grade":""}', CTX + """ Reconstruyo de forma clean-room funciones de Wii Sports Resort (Tennis y otros deportes). Necesito un mapa de módulos y librerías internas para agrupar funciones por subsistema.

Investiga a fondo:
1. Qué se sabe públicamente de la arquitectura de Wii Sports, Wii Sports Resort, Wii Play y Wii Fit: librerías internas (EGG, prefijos RP*, Sp*), nombres de clases visibles en símbolos o RTTI, formatos de recursos (BRRES, BRLYT, BRSAR, archivos .arc/.szs). Incluye el proyecto doldecomp/ogws (Wii Sports).
2. Proyectos públicos de decompilación o modding de esos juegos (repos, wikis, Tockdom, Custom Mario Kart wiki para formatos compartidos) y su estado.
3. Qué subsistemas comparten los deportes (escena, cámara, Mii, input/MotionPlus, física de pelota, IA).""")
P["G22"] = (1200, '{"gap":"G22","id":"G22-001","criterion":"","scope":"function|object|binary","project":"","how_verified":"","source_url":"","evidence_grade":""}', CTX + """ Tengo un certificador propio (bytes idénticos por función + controles negativos). Debo decidir si certificar funciones contra un stage de build nuevo y si aceptar overrides de declaraciones. Quiero alinear mis criterios con los de la comunidad.

Investiga a fondo:
1. Qué consideran "matching" los proyectos decomp Wii/GC: objdiff 100% por función, objeto completo, sha1 del DOL final, categorías de progreso en decomp.dev y dtk-template (Matching, NonMatching, Equivalent).
2. Cómo tratan funciones "equivalentes" o "non-matching pero funcionales".
3. Requisitos de reproducibilidad (compilador fijado, wibo/WINE, sha de herramientas).
4. Cómo versionan el cambio de configuración de build sin invalidar matches previos.""")
P["G23"] = (1500, '{"gap":"G23","id":"G23-001","technique":"","example":"","detection_rule":"","community_policy":"","source_url":"","evidence_grade":""}', CTX + """ Puedo lograr bytes idénticos cambiando declaraciones (aridad de un prototipo extern, retipar un campo de struct local) en vez de la función. Sospecho que muchos son fake matches.

Investiga a fondo:
1. Definición de "fake match" en la comunidad decomp (N64, GC, Wii) y ejemplos concretos.
2. Técnicas de fake match conocidas (casts absurdos, variables dummy, uniones, prototipos incorrectos, `register`, inline asm) y cómo se detectan en revisión.
3. Políticas de proyectos (marcadores // FAKEMATCH, // fake, tags) y si cuentan en el progreso.
4. Criterios automáticos para distinguir un fix de declaración legítimo de un fake match (consistencia con otras TUs, con los callers, con la semántica).""")
P["G24"] = (1800, '{"gap":"G24","id":"G24-001","work":"","year":null,"arch":"","compiler":"","metric":"","result":"","split_strategy":"","source_url":"","evidence_grade":""}', CTX + """ Uso un LLM para editar fuente hasta lograr match y obtengo ~0.09 funciones certificadas por millón de tokens. Quiero construir un dataset grande para mejorar eso en PowerPC/mwcc.

Investiga a fondo:
1. Datasets y modelos publicados de decompilación neural: LLM4Decompile, Nova, DecGPT, ExeBench, Decompile-Bench, trabajos de "neural matching decompilation", y si alguno cubre PowerPC o compiladores no-GCC.
2. Formato de los datasets (pares asm/fuente, flags, métricas de re-ejecutabilidad vs re-compilabilidad vs byte-match).
3. Resultados con bucles de feedback del compilador (iterative refinement, RL con recompensa por match).
4. Riesgos de contaminación train/test y cómo los particionan (por proyecto, por función, por familia).""")
P["G25"] = (1500, '{"gap":"G25","id":"G25-001","c_pattern":"","asm_signature":"","pragma_or_flag":"","compiler":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Las funciones matemáticas (física, cámara, movimiento) tienen residuos en código de coma flotante.

Investiga a fondo:
1. Cómo genera mwcceppc: conversiones int<->float (constante mágica 0x4330000080000000, xoris, __cvt_fp2unsigned), frsp, fmadds/fmsubs (contracción, #pragma fp_contract), fabs/fneg, comparaciones fcmpu/fcmpo.
2. Paired singles (ps_*, psq_l/psq_st, GQR): cuándo los emite el compilador y cuándo son asm manual (PSVEC/PSMTX, nw4r math).
3. float vs double en literales y parámetros, y cómo afecta al match.
4. Guías de proyectos decomp para matchear código de vectores/matrices.""")
P["G26"] = (1800, '{"gap":"G26","id":"G26-001","construct":"","c_pattern":"","asm_signature":"","threshold_or_rule":"","compiler":"","source_url":"","evidence_grade":"","test":""}', CTX + """ Necesito el patrón de fuente exacto para construcciones con codegen poco obvio.

Investiga a fondo, para cada una: asm generado, fuente que lo reproduce y variantes por versión/flags:
1. switch: umbral de jumptable vs cadena de comparaciones vs búsqueda binaria.
2. bitfields: orden de bits en PPC big-endian, rlwinm/rlwimi.
3. varargs: va_list, __va_arg, guardado de registros.
4. copia y retorno de structs por valor (lwz/stw en bloque, memcpy implícito).
5. long long: __shl2i, __shr2i, __div2i, __mod2u y similares del runtime.
6. división y módulo por constante (mulhw + constante mágica, srawi + addze).""")
P["G27"] = (1500, '{"gap":"G27","id":"G27-001","quantity":"","units_or_range":"","algorithm":"","numeric_signature":"","source_url":"","evidence_grade":""}', CTX + """ Reconstruyo de forma clean-room las ~50 funciones de movimiento de un juego deportivo de Wii que usa Wii MotionPlus. Necesito entender la semántica para nombrar tipos y validar hipótesis, no copiar código.

Investiga a fondo:
1. Datos que entregan el Wii Remote y MotionPlus: acelerómetro (ejes, rango, calibración), giroscopio (tasas, modos lento/rápido, escalas), formato de reportes, según documentación pública (WiiBrew, Dolphin, wiiuse, papers).
2. Algoritmos típicos de fusión y orientación con esos sensores (integración de giróscopo, corrección por gravedad, cuaterniones, filtros complementarios) y su firma numérica en código (constantes, normalizaciones).
3. Detección de gestos de swing (fase, impacto, velocidad angular) en la literatura.
4. Cómo emula Dolphin MotionPlus (para generar trazas de prueba).""")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for gid, (words, schema, body) in P.items():
        text = body.strip() + "\n" + TAIL.format(words=words, schema=schema, gid=gid)
        (OUT / f"{gid}.txt").write_text(text, encoding="utf-8")
    print(f"wrote {len(P)} prompts to {OUT}")


if __name__ == "__main__":
    main()
