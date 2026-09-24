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
