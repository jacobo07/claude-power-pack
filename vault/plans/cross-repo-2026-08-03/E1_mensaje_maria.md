Operator action: mensaje consolidado a María — A1 (LiveChat CLS) + B1 (§72 review queue)
Status: SEND-READY
Redactado: 2026-08-03
Fuentes: docs/operator-actions/{livechat-greeting-runbook-R179, cwv-final-runbook-R204,
         cls-emergency-runbook-R218, MARIA-S72-REVIEW-QUEUE-CONSOLIDATED-R188}.md

CONTEXT
=======
A1 — LiveChat auto-greeting. Escrito tres veces (R179 06-2026, R204 26-07-2026,
R218 03-08-2026) sin que se haya ejecutado nunca. 17 meses abierto desde la
primera detección en GSC (21-mar-2025). El agente NO puede hacerlo: el App
Password de WordPress llega a WordPress, no a los servidores de LiveChat — no
existe ruta API desde este repo a ese ajuste. Verificado de nuevo en R218.

Por qué un cuarto runbook no serviría: los tres anteriores son correctos y
completos. El cuello de botella nunca fue el análisis, fue la entrega. Este
mensaje existe para que la acción salga del repo y llegue a quien puede
ejecutarla.

B1 — Cola §72. Páginas LIVE con marcador COSTALUZ-72-UNREVIEWED. La cola
R163→R169 sigue abierta y la R188 la consolida. Aviso de alcance del propio
R188: no se ha corrido un barrido site-wide de marcadores, así que la ausencia
de una página de esta lista NO prueba que esté revisada. El barrido es barato
si María lo quiere antes de sentarse con esto.

Cambio de registro respecto a los runbooks: se pide UNA acción primero (el
toggle) y se separa visualmente de la cola legal, que es trabajo de otro tipo
y otro ritmo. Mezclarlas es lo que hizo que A1 se perdiera tres veces dentro
de documentos largos.


MENSAJE (verbatim, enviar tal cual)
====================================
Hola María 👋

Te escribo con dos cosas: una que son literalmente 60 segundos y lleva 17
meses pendiente, y otra que es revisión legal tuya y va a su ritmo.

────────────────────────────────
1) EL MINUTO QUE MÁS IMPACTO TIENE (por favor, esto primero)

Desactivar el saludo automático del chat de LiveChat.

  1. https://www.livechat.com/dashboard/ → Engage → Greetings
  2. Busca el saludo que salta solo al cargar la página
     ("Welcome to Costaluz Lawyers!" — emoji de mano, botón "Chat now")
  3. Apágalo. (O si prefieres conservarlo: cambia el disparador a
     "after user interaction" o "exit intent" — igual de válido.)
  4. Guardar.

Por qué importa: ese saludo se abre solo y redimensiona el widget cinco veces
seguidas sin que nadie lo toque. Eso es el 72% de todo el "salto visual" de la
web — más que todo lo demás junto. Google lo usa como señal de posicionamiento,
y ahora mismo el 61,7% de las visitas móviles reales lo sufren. Son 493 URLs
afectadas, pero es un solo widget heredado por todas: un toggle las mueve todas.

El chat NO se rompe. El botón se queda donde está, el visitante lo pulsa y se
abre igual. Lo único que se quita es que se abra solo antes de que nadie lo pida.

Honestamente, para que no haya sorpresas: esto nos saca de "Poor" en la mayoría
de páginas, pero probablemente nos deje en "Needs Improvement", no en "Good".
Quedan dos causas menores que aún estamos investigando y sobre las que no vamos
a tocar nada hasta entenderlas. Aun así, es de largo la acción con mejor
relación esfuerzo/impacto que tenemos.

Cuando lo guardes, dímelo y lo re-medimos y te paso el antes/después. (El
número de laboratorio se mueve al instante; el de campo, que es el que cuenta
para ranking, tarda ~28 días.)

────────────────────────────────
2) REVISIÓN §72 — páginas ya publicadas esperando tu visto bueno

Estas están LIVE con marcador de "sin revisar". Van ordenadas por cuánto te
necesitan: primero las que afirman cifras, al final las que solo son enfoque.

DECISIÓN TUYA (no es §72, es criterio del despacho)
  • #26529 — Fuerza mayor y retrasos en la entrega de vivienda
    https://www.costaluzlawyers.com/wp-admin/post.php?post=26529
    → Lee las cinco preguntas/respuestas del FAQ y dinos si dicen lo que el
      despacho sostiene sobre fuerza mayor. Si sí, las hacemos visibles; si no,
      las quitamos. No vamos a adivinar una posición sobre fuerza mayor.

CIFRAS — necesitan confirmación antes que nada
  • #29131 — Buying Property in Spain (guía completa) · ~2.391 impr/28d
    https://www.costaluzlawyers.com/buying-property-in-spain-complete-legal-guide-2026/
    → Corregimos dos datos fiscales y YA ESTÁN EN VIVO. Confírmanos ambos:
      (a) alquiler: 19% residentes UE/EEE, 24% fuera (Reino Unido incluido
          desde el Brexit). Antes decía 19% y luego "aclaraba" 19%, así que un
          lector de fuera de la UE concluía que le aplicaba el 19%.
      (b) Modelo 210: anual desde el ejercicio 2024, presentación del 1 al 20
          de enero del año siguiente. Antes decía "trimestral" — ese es el error
          de mayor consecuencia, porque quien lo siguiera presentaba en un
          calendario que ya no existe.
    → Y una que NO hemos tocado y queremos tu criterio: la página sigue
      diciendo que los no residentes UE no pueden deducir gastos. Hay
      sentencias de 2025 extendiendo ese derecho para evitar discriminación,
      así que lo dejamos como está por ser posición en evolución. Tu decisión
      aquí arregla tres páginas de golpe (#29131, #34513 y #34514 comparten
      la misma frase).

  • #37375 — Requisito de ingresos NLV (IPREM + multiplicador 400%)
    https://www.costaluzlawyers.com/wp-admin/post.php?post=37375

  • #37360 — Sentencia sobre seguro de vida de prima única en hipotecas
    https://www.costaluzlawyers.com/wp-admin/post.php?post=37360
    → Confirmarla desbloquea además el espejo en español de esta misma página.

ENFOQUE — sin cifras, solo revisar cómo está planteado
  • #29191 — Mudarse a España desde Francia · 878 impr/28d
    https://www.costaluzlawyers.com/moving-to-spain-from-france-residency-tax-property-guide-2026/
    → Cuatro secciones nuevas escritas a propósito sin cifras (SCI, regímenes
      matrimoniales, réserve héréditaire vs legítima, IFI vs Patrimonio).
      Una en concreto: decimos que la elección Brussels IV es "el fallo de
      planificación más común que vemos en herencias francesas".
      ¿Confirmas que esa afirmación es nuestra para hacerla?

  • #37364 — Hub de cláusulas abusivas en hipotecas
    https://www.costaluzlawyers.com/wp-admin/post.php?post=37364

VOZ Y CLAIMS — lo más ligero
  • #37291 — Honorarios de notaría (publicado con horquillas, sin cifras
    inventadas; el arancel es escala regulada RD 1426/1989)
    https://www.costaluzlawyers.com/wp-admin/post.php?post=37291
  • #37392 y los otros dos ítems de R167/R169

En cuanto apruebes cada una, le quitamos el marcador. No hace falta que las
mandes todas juntas — según vayas cerrando, nos lo dices y las vamos soltando.

Un aviso honesto: no hemos barrido la web entera buscando marcadores, así que
puede haber alguna página con marcador que no esté en esta lista. Si quieres,
lo corremos antes de que te sientes con esto — es barato.

Gracias 🙏
────────────────────────────────


VERIFICACIÓN (tras confirmación de María)
==========================================
A1: scripts/r218_throttled_trace.py — re-medir contra el baseline de hoy
    (data/costaluz/cls-throttled-R218.json, p75 CrUX 0.62 en
     docs/measurement/cls-pre-fix-R218.json).
B1: por cada página aprobada, retirar el marcador COSTALUZ-72-UNREVIEWED.

SI A1 SIGUE SIN EJECUTARSE
===========================
No escribir un quinto runbook. La superficie técnica está agotada y
documentada tres veces. Escalar como decisión de Owner: o Jacobo obtiene
acceso al dashboard de LiveChat, o se acepta explícitamente el coste de CLS
y se registra esa aceptación para dejar de re-abrirlo cada ronda.
