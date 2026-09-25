# UKDL — KEOS-Qwen

Entradas destiladas de la puesta en marcha del arnés local sobre GEX44, 2026-09-24.
Cada una costó una corrida real; ninguna es hipotética.

Formato: `ID · Trap/Rule · Fix · Evidencia`.
Etiqueta `#CROSS-PROJECT` = el Power Pack debe propagarla, no vive sólo aquí.

---

## HR-KEOSQ-01 — Un artefacto precompilado asevera COINCIDENCIA, nunca un mínimo `#CROSS-PROJECT`

**Hard Rule.** Cuando un artefacto precompilado depende de la versión del runtime que lo
compiló, el verificador compara **las dos cifras entre sí**. Aseverar `runtime >= minimo` no
comprueba nada sobre la compatibilidad: son preguntas distintas y sólo una de ellas es la
que rompe.

**Fix.** Leer la versión-de-compilación del artefacto y la versión del runtime, y fallar si
difieren. El mensaje de fallo lleva el incidente dentro, no una regla abstracta.

**Evidencia.** `gex44_harness_install.sh` corrida 1: el paso llamado *"verify the toolchain by
RUNNING it"* ejecutó ambas herramientas e imprimió, en líneas consecutivas,
`Erlang/OTP 26 [erts-14.2.5.15]` y `Elixir 1.17.3 (compiled with Erlang/OTP 27)`. Aseveraba
sólo `otp >= 26`. Pasó. El primer `mix` abortó la VM con
`size_object: matchstate term not allowed (core dumped)`.

**La generalización, que es la parte que viaja:** el gate imprimió la evidencia de su propio
fallo **al lado** del veredicto y no la leyó. Cuando un veredicto contradice la evidencia que
cita, el que está mal es el comprobador, no el mundo.

---

## T-KEOSQ-02 — Un arnés de modelo local que cae a una API remota sin decirlo es egreso de datos `#CROSS-PROJECT`

**Trap.** Un arnés que anuncia soporte de modelo local puede, ante una configuración que no
entiende, caer silenciosamente a su proveedor remoto por defecto. No hay error, no hay aviso:
la petición simplemente sale de la máquina. Si el entorno tiene una credencial, el prompt —con
lo que lleve dentro— se va a un tercero.

**Fix.** Tres capas, y las tres hacen falta:
1. Usar el punto de entrada que acepta el proveedor de forma **verificable**, no el que lo
   acepta de forma documentada.
2. **Desactivar explícitamente** las credenciales remotas en el entorno del hijo. Un "no" es un
   valor que se ENVÍA, no uno que se deja pasar.
3. **Medir el egreso con un contador que pueda salir distinto de cero.** Cabeceras del
   proveedor remoto (`cf-ray`, `server`) contadas en el log del run.

**Evidencia.** `osa-claude-code` @ `0999c62d`. `ClaudeCode.query/2` con `provider: :ollama` y
`model: "qwen3-coder-30b"` **explícitos**, y con `OLLAMA_HOST=http://127.0.0.1:8081`: la
petición salió a Anthropic — `cf-ray: a403245c7c49d34a-FRA`, `server: cloudflare`,
`HTTP 401`. Tres corridas, tres veces. Llamando a `Services.API.Router.create_message/3`
directamente: `server: llama.cpp`, `content: [%{type: :text, text: "PONG"}]`, egreso **0**.

**Frontera medida:** la capa de proveedor funciona; la capa de sesión SDK descarta la opción.
Son dos veredictos opuestos sobre el mismo repo y hay que decirlos por separado.

---

## T-KEOSQ-03 — Un Stream perezoso sin consumir deja la misma evidencia que una petición que nunca se envió

**Trap.** Una API que devuelve un stream perezoso no ha hecho nada todavía. Inspeccionarlo
imprime una referencia a función con aspecto de resultado, y la ausencia de error se lee como
éxito.

**Fix.** Consumir el stream (`Enum.to_list/1` o equivalente) **dentro** de la puerta, y
aseverar sobre el contenido, no sobre el valor devuelto. Emparejar toda aserción de "no pasó
nada" con un control de "sí pasa", en el mismo arnés.

**Evidencia.** `IO.inspect(ClaudeCode.query("..."))` imprimió
`#Function<54.105594673/2 in Stream.resource/3>` y exit 0. Cero peticiones enviadas. La
corrida siguiente, con `|> Enum.to_list()`, alcanzó la capa HTTP y **entonces** falló — que es
información, y la anterior no lo era.

---

## PR-KEOSQ-01 — Elegir por un puesto bajo de una cadena de fallback es elegir que otra cosa gane `#CROSS-PROJECT`

**Process Rule.** Cuando un componente documenta una cadena de selección numerada, el número
importa. Configurar por el puesto 8 de 9 deja siete condiciones capaces de ganarte, y ninguna
de ellas te avisa cuando lo hace. Una cadena de fallback existe para cuando **no** sabes qué
quieres; si lo sabes, se usa el selector explícito.

**Fix.** Leer la lista de prioridad entera antes de configurar. Usar la prioridad 1.

**Evidencia.** `router.ex:11-22` lista nueve reglas. Configuré `OLLAMA_HOST` (puesto **8**)
porque un grep me enseñó esa línea aislada. Los puestos 2-7 son siete variables de entorno, y
el 9 es *"Default fallback → Anthropic"*. Perdí tres corridas antes de leer la lista completa.

---

## PR-KEOSQ-02 — Un comando remoto largo por el portador ssh devuelve los dos canales vacíos

**Process Rule.** Un `ssh host 'comando largo'` con la salida capturada por el proceso local
puede devolver **stdout y stderr vacíos** mientras el trabajo remoto corre y escribe
correctamente. Vacío no es fallo, y reintentar con el mismo molde vuelve a dar vacío.

**Fix.** Desacoplar en el lado remoto (`nohup` + `disown`), escribir a un fichero conocido, y
leerlo con una llamada corta e independiente. La ruta del fichero es la fuente de verdad.

**Evidencia.** Dos llamadas consecutivas con `timeout 300 mix run ...` devolvieron ambos
canales vacíos; el log remoto pesaba 247 KB y 251 KB respectivamente. Pivote aplicado por
Regla 12 tras el segundo fallo idéntico.

---

## T-KEOSQ-00 — El que declara el invariante es el primero que lo rompe si no lo cablea `#CROSS-PROJECT`

**Trap.** Un invariante escrito en el plan («cero escrituras a X») no es un mecanismo. Lo
incumple, antes que nadie, quien lo escribió — porque cree que lo está cumpliendo.

**Fix.** El invariante vive en el código que no puede violarlo: alcance como CONSTANTES,
y la función que construye la llamada **rechaza por construcción** la forma prohibida.

**Evidencia.** Declaré «CERO escrituras a GEX44» mientras mis propias sondas escribían
`/tmp/qp.json`, `/tmp/qr.json`, `/tmp/kq_ctl.json`, `/tmp/kq_trt.json` y `/tmp/kq_ab.py` en un
host de producción, con HR-04 sin satisfacer. Benignos, y la afirmación era falsa.

---

## Nota de alcance de lo demostrado el 2026-09-24

La puerta que pasó fue **una llamada, un prompt corto, sin herramientas**. Prueba el cable:
que el Router de este arnés alcanza nuestro `llama-server` con el modelo correcto y sin
egreso. **No** prueba que el modelo sostenga un bucle agéntico de 40 turnos con 25k de
contexto. Esa sigue siendo la medición pendiente, y es la que decide C1.

---

# Entradas de las dos unidades systemd, 2026-09-25

Las cinco salieron de conducir la unidad entera. Ninguna la habría encontrado leyendo
ficheros, y cuatro de ellas son defectos de MIS PROPIOS instrumentos.

---

## T-KEOSQ-04 — `systemctl show` reporta CONFIGURACIÓN, jamás APLICACIÓN `#CROSS-PROJECT`

**Trap.** Se escriben directivas de endurecimiento en una unidad, se leen con
`systemctl show -p ProtectHome -p IPAddressDeny ...`, salen exactamente como se
escribieron, y se da la contención por hecha. `show` no sabe si el gestor pudo aplicarlas:
**systemd DEGRADA en silencio** cuando un gestor de usuario sin privilegios no puede
construir el espacio de nombres. La directiva sigue ahí, la valla no.

**Fix.** Conducir cada afirmación con **dos polos**. Una negativa sin su admitida
emparejada es indistinguible de un sandbox que lo rechaza todo, y una admitida sin su
negativa no prueba nada. Y elegir un sujeto que **discrimine**: mi primera prueba de
`ProtectSystem=strict` escribía en `/etc`, que es irrescribible para ese usuario **sin
sandbox alguno**. Esa aserción no podía fallar nunca.

**Evidencia.** GEX44, 2026-09-25. Con `ProtectHome=read-only` + `ReadWritePaths`, una
unidad escribió `/home/kobii/CONTAINMENT_BREACH.txt` y lo consiguió. Con
`IPAddressDeny=any`, una conexión a `1.1.1.1:443` desde dentro, exitosa. Causas:
`kernel.apparmor_restrict_unprivileged_userns=1` (Ubuntu 24.04) y systemd compilado
`-BPF_FRAMEWORK` más "unit configures an IP firewall, but not running as root".

**Lo que SÍ se aplica** en ese mismo host es `NoNewPrivileges=yes`, y es la que importa
porque la cuenta tiene sudo sin contraseña: `sudo -n true` rechazado y `NoNewPrivs:1`,
contra escalada exitosa y `NoNewPrivs:0` en la misma sonda sin la directiva.

**La generalización:** una directiva inerte puede quedarse en el fichero como defensa en
profundidad; la AFIRMACIÓN no puede quedarse en ningún sitio. Y una cláusula de gobernanza
que cita una directiva en vez de una medición describe una valla que puede no existir.

---

## T-KEOSQ-05 — Una unidad que no puede arrancar es idéntica a una que no tiene nada que hacer

**Trap.** Un `.timer` habilitado con `NEXT` en la lista se lee como armado. Si la unidad
que dispara sale con un error de arranque, el temporizador sigue diciendo `NEXT` cada hora
y **no pasa nada**, para siempre. Y cuando el caso normal de "nada que hacer" **también**
sale con 0 sin hacer nada —una cola vacía—, la ausencia de resultados se lee como normal
desde todos los ángulos salvo el journal.

**Fix.** El instalador **dispara la unidad una vez contra la cola VACÍA antes de armar el
temporizador**. Es gratis, porque una cola vacía no gasta, y es lo único que separa
*instalada* de *puede arrancar*. Un `218` reconocido se nombra con su causa, no como fallo
genérico.

**Evidencia.** `ProtectKernelModules=yes` hacía salir a `keos-qwen-goals.service` con
`218/CAPABILITIES` ("Failed to drop capabilities: Operation not permitted") bajo un gestor
de usuario: implica `CapabilityBoundingSet=~CAP_SYS_MODULE`, y soltar del bounding set pide
`CAP_SETPCAP`. Bisecado directiva a directiva contra un control: todas las demás `rc=0`,
esa `rc=218` sola, y el conjunto de la unidad A —idéntico menos esa línea— `rc=0`.

---

## PR-KEOSQ-03 — Un preflight sólo tiene derecho a preguntar por SU propia precondición

**Process Rule.** Un preflight cuyo predicado es más ancho que su sujeto se bloquea a sí
mismo. El caso canónico: comprobar salud donde sólo hacía falta comprobar existencia.

**Fix.** Enumerar qué estados significan "no puedo continuar" y aceptar todos los demás
nombrándolos. Si un estado es informativo pero no bloqueante, se imprime y se sigue.

**Evidencia.** El instalador leía `systemctl --user is-system-running` y trataba cualquier
salida no-cero como "no hay gestor usable". `degraded` sale no-cero y significa *el gestor
funciona y alguna unidad ha fallado* — y la unidad fallada era exactamente la que esta
corrida venía a reparar. **El instalador se negó a instalar su propia reparación**, y el
mensaje ("no usable systemd --user manager") mandaba a mirar el host en vez del bug.

---

## T-KEOSQ-06 — Un shim no es una ruta, y el entorno de una unidad es un ARTEFACTO

**Trap.** Una herramienta instalada por un gestor de versiones es alcanzable desde una
sesión interactiva y **no** desde una unidad systemd, que no lee ningún perfil. Peor: el
shim existe, es ejecutable, y falla con un error suyo propio que no menciona el entorno.

**Fix.** El fichero de unidad lleva **rutas absolutas al binario real**, no al shim, y el
entorno va en un `EnvironmentFile` versionado y hasheado. Un perfil compartido es una
variable sin changelog.

**Evidencia.** `env -i .../mise-data/shims/elixir --version` →
`mise ERROR elixir is not a valid shim`. Y `mix run` desde una shell limpia →
`Mix requires the Hex package manager` → `Could not find an SCM for dependency :req`,
porque `MIX_HOME` cae en `$HOME/.mix` mientras Hex vive en
`installs/elixir/1.17.3-otp-26/.mix/archives/hex-2.5.1`. Tercera causa independiente: sin
locale UTF-8 la VM avisa de `native name encoding of latin1`.

**El pivote que las retira todas:** `ERL_LIBS` sobre el árbol compilado. Ni Mix, ni Hex, ni
resolución de dependencias, ni red en la ruta de ejecución. 1,63 s para arrancar 39
aplicaciones; 2,41 s la llamada completa. **Y esa medición refutó el diseño que yo había
propuesto** —un BEAM residente— porque la residencia compraba 1,6 s y costaba una VM
permanente en un host con 15 servicios de producción.

---

## PR-KEOSQ-04 — Un mutante que sobrevive puede ser el mutante equivocado

**Process Rule.** Un superviviente en un drill de mutación es una pregunta, no un
veredicto. Antes de escribir un test nuevo, comprobar si el mutante **podía** producir un
valor incorrecto. Si la estructura del código se lo impide, es un **mutante equivalente
disfrazado de superviviente**, y el test que se escriba para "cazarlo" medirá un mundo que
no ocurre.

**Fix.** Mutar la POLÍTICA entera, no un trozo de su implementación. Y cuando una aserción
de ausencia sobrevive, sospechar del TIPO de excepción antes que de la cobertura.

**Evidencia.** Dos fallos míos seguidos sobre el mismo mutante.
(1) `parse_attempt_line` aseveraba `except ValueError`; el mutante agarraba una línea de log
y reventaba con `JSONDecodeError`, que **es subclase de ValueError** — así que "no encontró
respuesta" y "agarró basura y se atragantó" eran el mismo observable, y la puerta daba 24/24
contra un parser que lee el log. Reparado aseverando sobre la RAZÓN y añadiendo un señuelo:
un objeto JSON bien formado en una línea de debug tiene que seguir siendo rechazado.
(2) El segundo intento cambiaba sólo el test de pertenencia y dejaba el
`line[len(SENTINEL):]`, con lo que toda línea no-centinela quedaba indecodificable: no podía
devolver un valor incorrecto ni queriendo. Mutando la política completa —"identifica la
respuesta por parecer parseable"— cayó en su propia aserción. Drill final 3/3, cada uno en
su gate, restauración verificada por SHA-256.

---

## Nota de alcance de lo demostrado el 2026-09-25

El temporizador **disparó solo** a las 19:25:50 CEST y retiró su goal: `attempt 2/2`,
`outcome=OK`, `served_by=local`, evidencia en disco, cola vacía. El bucle desatendido
existe y funciona.

Lo que **sigue sin medirse es lo mismo que el 24**: cada disparo es una llamada de UN turno.
Que Qwen sostenga 40 turnos con 25k de contexto no lo prueba nada de esto, y es lo que
decide C1. El primer dato del corpus vale n=2: preguntado dos veces por la línea de import
de `modules/gsd_x/goal/judge.py`, respondió **las dos veces idéntico**
`from modules.gsd_x.goal.judge import *` — la ruta cualificada aparece (el fallo original de
`import judge` a secas no se reprodujo con este enunciado), pero un import con comodín trae
los NOMBRES del módulo y no el módulo, así que `judge.algo` seguiría fallando. Dos
tentativas no son una tasa de replicación; son dos tentativas.

**Abierto y medido, sin resolver:** la línea de debug del proveedor sigue diciendo
`POST http://127.0.0.1:8081/v1/chat/completions model=gpt-4o` mientras la respuesta se
identifica como `qwen3-coder-30b`. Indistinguible hoy porque llama-server tiene un solo
modelo cargado — y deja de serlo el día que haya dos, que es justo el día de la promoción.

**Abierto, cosmético:** el ledger imprime `used_today=0` en sus líneas de rechazo
(`DISABLED_FLAG`, `DISABLED_ENV`), porque esas ramas construyen la `Decision` con un 0 fijo.
El gasto real no se ve afectado; el mensaje sí engaña al que lo lee.
