# VP-019 · Banco de 160 combinaciones cinematográficas de escena, luz y color

**Fecha:** 2026-11-17.  **Estado:** IDEACIÓN ESTRUCTURADA / NO IMPLEMENTADA / NO VERIFICADA.  **Fuente:** VP-019 (principio observado en REF-BRAND-LIGHT-001), 160 desarrollos creativos NUEVOS propuestos por análisis, NO 160 efectos observados en el vídeo ni 160 identidades visuales originales registrables.

**Propietarios:** CDIO-06 juzga el encaje; Visual Patterns documenta métodos; DESIGN.md gobierna los colores reales; CCF produce o adquiere arte cuando corresponde; CDICF selecciona herramientas autorizadas; frontend hace la web; el evaluador CDIO y Production Reality validan.

**Contrato:** la paleta de cada fila es ORIENTATIVA, no una recomendación de contraste WCAG ni un sistema de marca aprobado. El fondo, el primer plano, el acento y la composición se validan para el proyecto concreto. Los nombres, escenas y materiales son conceptos inventados para este banco; no autorizan copiar la imagen de referencia ni activos de terceros.

**Alcance real:** 20 familias por 8 recetas = 160 combinaciones distintas. El ledger de promoción se guarda por ID en `../ledgers/VP019_COMBINATION_LEDGER.jsonl`; el dataset es la fuente canónica de las descripciones, el ledger solo registra estado/evidencia y no duplica el contenido visual.

## Reglas de selección y verificación

1. Priorizar imagen optimizada prerenderizada cuando no haya interacción; SVG/máscaras solo cuando haya geometría estable; 3D offline para refracción/reflejos dependientes del material; WebGL solo si es necesario y medido.
2. No permitir que la luz de marca cambie falsamente el color real de un producto, la condición de un inmueble, una señal de seguridad, una estructura, una gráfica o un dato clínico.
3. Separar siempre la imagen de fondo del DOM: titular real, CTA funcional, navegación, prueba social comprobada, etiquetas, enfoque teclado y contenido legible en móvil.
4. Verificar contra peor área iluminada, recorte a 360/390/768/1440 y accesibilidad; no confundir filtros de color con luz física.
5. Dos estados del MISMO inmueble/objeto deben mantener geometría y cámara verificadas; una escena generada desde cero no equivale a una recoloración exacta.
6. Cada elemento empieza como hipótesis, no con la evidencia del vídeo original. Antes de promoción: activo con derechos, render real, evaluación CDIO, comparación con un tinte plano y consumo por un agente futuro.

## Vocabulario de lanes

- STATIC_COMPOSITE: fotografía, composición o imagen final rasterizada; CSS simple para scrim y layout.
- OFFLINE_3D: render físico o artístico de objeto/escena con luces/materiales antes de exportar asset responsive.
- SVG_MASK: geometría enmascarada o trazada sobre activos estáticos; probar alineamiento de pixel/crop.

## Catálogo íntegro

### F01 · Jardines, paisaje y naturaleza

Base #071E18; tipografía orientativa #F7F5E9. Excluir por defecto: formularios densos y mapas de datos.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C001 | Jardín ámbar de ocaso | setos, piedra caliza y escalones | horizonte naranja, peldaños y hojas iluminados | #F59A23 | STATIC_COMPOSITE | halo tras texto |
| VP019-C002 | Bosque de niebla turquesa | pinos, helechos y sendero húmedo | luz fría filtrada entre troncos y reflejada en charcos | #39C8BC | STATIC_COMPOSITE | niebla sobre tipografía |
| VP019-C003 | Invernadero rosado | vidrio curvo, helechos y acero | rosado de contraluz entre marcos con hojas translúcidas | #E87AB2 | OFFLINE_3D | reflejos no registrados |
| VP019-C004 | Olivares en hora azul | olivos viejos y camino de tierra | cálido rasante desde suelo y luna azul de relleno | #DEB16F | STATIC_COMPOSITE | exceso de calidez |
| VP019-C005 | Jardín volcánico de cobre | basalto oscuro, suculentas y agua | bordes cobrizos sobre roca y reflejos en acequia | #C17A4B | STATIC_COMPOSITE | detalle oscuro empastado |
| VP019-C006 | Patio mediterráneo de lima | arcadas crema, macetas y azulejo | rebote verde lima desde una fuente iluminada | #B8D969 | STATIC_COMPOSITE | tonalidad artificial de piedra |
| VP019-C007 | Orquídeas ultravioleta | flores blancas y follaje negro | luz violeta localizada tras pétalos y nervaduras | #AD86F5 | STATIC_COMPOSITE | pétalos sin separación |
| VP019-C008 | Jardín zen de lluvia | grava rastrillada, arce y estanque | contraluz rojo tenue tras el arce, superficie mojada | #E56E63 | STATIC_COMPOSITE | foco visual invasivo |

### F02 · Mar, agua y litoral

Base #061C2B; tipografía orientativa #EEF9FA. Excluir por defecto: información de seguridad marítima que exija colores fieles.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C009 | Bahía bioluminiscente | cala oscura y espuma | cian suave entre rompientes y bordes de ola | #45D8DE | STATIC_COMPOSITE | glow confundido con naturaleza real |
| VP019-C010 | Yate en amanecer coral | cubierta de teca, vidrio y mar | sol coral bajo sobre espejo de agua y barandillas | #FF776D | STATIC_COMPOSITE | reflejo inconsistente |
| VP019-C011 | Arrecife de aguamarina | corales, arena y luz filtrada | caústicas verdes desde superficie hacia fondo | #5BE2C1 | OFFLINE_3D | color biológico engañoso |
| VP019-C012 | Puerto violeta nocturno | amarres, velas y luces lejanas | lámparas magenta puntuales y estelas en agua | #A48DFF | STATIC_COMPOSITE | destellos por exceso |
| VP019-C013 | Ola cromada de plata | ola congelada y cielo tormentoso | reflejo plateado en cresta con espuma oscura | #CED8E6 | OFFLINE_3D | falta de contraste de borde |
| VP019-C014 | Isla volcánica cobre | rocas negras y mar espumoso | contraluz terracota desde horizonte en lava seca | #EF9460 | STATIC_COMPOSITE | lectura falsa de actividad |
| VP019-C015 | Submarino azul glacial | ventana panorámica y profundidad | haz frío atravesando partículas hacia la ventana | #84C7FF | OFFLINE_3D | volumetría demasiado densa |
| VP019-C016 | Piscina esmeralda nocturna | piscina infinita, piedra y cielo | línea verde reflejada bajo borde desbordante | #42BF9D | STATIC_COMPOSITE | perspectiva del borde |

### F03 · Arquitectura y construcción

Base #101316; tipografía orientativa #F5F4F0. Excluir por defecto: planos técnicos con cotas o inspecciones de defectos.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C017 | Cubierta roja en tormenta | tejado pizarra y muro de madera | línea emisiva roja sobre vértice del frontón | #CB3048 | SVG_MASK | contorno desalineado |
| VP019-C018 | Fachada dorada nocturna | ladrillo negro y ventanas | luz ámbar vertical entre lamas de fachada | #DFAD62 | STATIC_COMPOSITE | ventanas demasiado saturadas |
| VP019-C019 | Puente azul eléctrico | acero estructural y río oscuro | recorrido azul por cables tensores y vigas | #4C9DFA | SVG_MASK | geometría del cable |
| VP019-C020 | Hormigón verde musgo | volúmenes brutalistas y lluvia | wash verde difuso desde suelo ajardinado | #78A58A | STATIC_COMPOSITE | tinte indiscriminado del hormigón |
| VP019-C021 | Escalera magenta suspendida | escaleras flotantes de madera | iluminación inferior en canto de peldaños | #D16BD7 | OFFLINE_3D | sombra sin apoyo |
| VP019-C022 | Rascacielos ámbar | vidrio oscuro y patrón de ventanas | fachada salpicada de celdas cálidas controladas | #F2A14D | STATIC_COMPOSITE | patrón demasiado artificial |
| VP019-C023 | Túnel de cobre | hormigón curvo y suelo húmedo | cinta de luz cobriza en continuidad de la bóveda | #C88059 | SVG_MASK | recorrido no creíble |
| VP019-C024 | Cúpula celeste | piedra clara y óculo central | luz azul suave entrando desde abertura superior | #85CFE0 | OFFLINE_3D | iluminación invertida |

### F04 · Hoteles, espacios e interiores

Base #151412; tipografía orientativa #F9F1E6. Excluir por defecto: pantallas de reserva con pasos críticos en imagen.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C025 | Lobby champán | mármol marfil, latón y cortinas | lámparas doradas con reflejos en suelo pulido | #D9B97A | STATIC_COMPOSITE | iluminación excesivamente amarilla |
| VP019-C026 | Suite azul petróleo | terciopelo azul, nogal y cristal | banda de luz cian en cabecero y espejo | #55AFC4 | STATIC_COMPOSITE | cristal con reflejo erróneo |
| VP019-C027 | Spa terracota | piedra travertino, vapor y piscina | rebote naranja suave desde lámparas sumergidas | #C98062 | STATIC_COMPOSITE | lectura del vapor |
| VP019-C028 | Bar esmeralda | botellas, latón y piedra negra | brillos verdes controlados detrás del vidrio | #56B78E | STATIC_COMPOSITE | etiquetas de botellas alteradas |
| VP019-C029 | Biblioteca berenjena | nogal, cuero y lámpara | luz violeta rebotada tras estantería | #AE89C7 | STATIC_COMPOSITE | fatiga visual |
| VP019-C030 | Restaurante glaciar | vidrio ahumado y metal cepillado | línea azul hielo siguiendo mobiliario | #9BCDEA | STATIC_COMPOSITE | reflejos en cubertería |
| VP019-C031 | Recepción arena rosa | yeso cálido, lino y espejo | ocaso coral filtrado a través de celosías | #EA968C | STATIC_COMPOSITE | pérdida de tono marfil |
| VP019-C032 | Salón cobre minimalista | microcemento y mobiliario negro | spot cobre sobre pieza escultórica central | #CD9268 | STATIC_COMPOSITE | saturación por encima de la marca |

### F05 · Cristal, agua y objetos transparentes

Base #0D1422; tipografía orientativa #F5F8FA. Excluir por defecto: productos donde el color real debe demostrarse.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C033 | Gota coral refractiva | gota de vidrio sobre piso oscuro | rim coral y cáustica difusa en suelo | #FF6859 | OFFLINE_3D | refracción físicamente falsa |
| VP019-C034 | Esfera turquesa | cristal óptico con burbujas | luz turquesa lateral y caústicas focalizadas | #53D9D0 | OFFLINE_3D | luminancia quemada |
| VP019-C035 | Prisma índigo | prisma triangular sobre negro | caústica azul y espectro contenido en la mesa | #647EF5 | OFFLINE_3D | dispersión arbitraria |
| VP019-C036 | Vaso jade | copa tallada y agua | refracción verde localizada a contraluz | #5AAF9A | OFFLINE_3D | imposibilidad del agua |
| VP019-C037 | Gotas ámbar | tres gotas sobre placa de vidrio | pequeños highlights miel y sombra coloreada | #F0AF4A | OFFLINE_3D | aspecto de plástico |
| VP019-C038 | Anillo de hielo rosa | escultura translúcida en anillo | gradiente fucsia en canto y núcleo blanco | #EF94C8 | OFFLINE_3D | contorno aliasing |
| VP019-C039 | Botella azul eléctrico | frasco transparente sin marca | rim azul oscuro y refracción de etiqueta neutra | #3593F4 | OFFLINE_3D | etiqueta ilegible |
| VP019-C040 | Burbuja de mercurio | esfera reflectante cromada | reflejo plateado y pequeño hotspot violeta | #B4A5F5 | OFFLINE_3D | cromo con entorno incoherente |

### F06 · Relojería y joyería

Base #08090B; tipografía orientativa #F6F0E7. Excluir por defecto: fichas de producto en que una gema o metal debe reproducirse fielmente.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C041 | Reloj de oro negro | caja metálica y cristal zafiro | luz miel en bisel y reflejo de canto | #E7B86A | OFFLINE_3D | material oro exagerado |
| VP019-C042 | Diamante hielo | piedra facetada sobre seda negra | destellos azules controlados en aristas | #9FCFF6 | OFFLINE_3D | facetas inventadas |
| VP019-C043 | Rubí carmesí | piedra roja montada en oro blanco | contraluz rubí con brillo focal sobre garra | #C73B56 | OFFLINE_3D | color de gema engañoso |
| VP019-C044 | Pulsera cobre | pulsera de eslabones y mármol | reflejo cobre suave por intersticios | #CC895A | OFFLINE_3D | geometría de eslabones |
| VP019-C045 | Perla lavanda | perla iridiscente y lino oscuro | halo violeta perimetral de baja intensidad | #B8A0D9 | OFFLINE_3D | perla sin volumen |
| VP019-C046 | Reloj verde oliva | correa cuero, esfera oscura | luz verde rebota desde superficie lateral | #A8BC78 | OFFLINE_3D | correa mal coloreada |
| VP019-C047 | Pendiente champagne | metal pulido y piedra transparente | reflejo dorado solo en metal | #D4B38B | OFFLINE_3D | borde imperceptible |
| VP019-C048 | Anillo azul medianoche | platino y gema oscura | rim azul profundo más highlight blanco | #537ABE | OFFLINE_3D | pierde contorno en negro |

### F07 · Belleza, perfumería y cosmética

Base #1C1217; tipografía orientativa #FFF5F1. Excluir por defecto: muestras de tonos de maquillaje donde prima precisión cromática.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C049 | Perfume rosa humo | frasco de vidrio esmerilado | luz rosa que atraviesa atomizador y base | #F3A7C1 | OFFLINE_3D | color real del líquido |
| VP019-C050 | Crema marfil dorada | tarro de cerámica y seda | halo miel sobre tapa metálica | #D9B073 | STATIC_COMPOSITE | producto fuera de foco |
| VP019-C051 | Sérum jade | pipeta de vidrio y agua | reflejo verde jade en gota, no etiqueta | #81CBAA | OFFLINE_3D | etiqueta ilegible |
| VP019-C052 | Bálsamo terracota | lata aluminio y lino | luz lateral terracota sobre bordes | #D17E68 | STATIC_COMPOSITE | textura artificial |
| VP019-C053 | Mascarilla azul nube | tarro blanco sobre agua | luz celeste desde superficie líquida | #99CDEA | OFFLINE_3D | halo falso en agua |
| VP019-C054 | Lápiz malva | metal de cosmético y superficie piedra | rim magenta sutil sobre cilindro | #C58DCC | OFFLINE_3D | tono de producto incorrecto |
| VP019-C055 | Jabón botánico lima | pastilla translúcida y hojas | luz verde lima a través de jabón | #B7D988 | STATIC_COMPOSITE | apariencia antinatural |
| VP019-C056 | Textura de seda coral | pliegues de tejido y frasco | ocaso coral acariciando pliegue diagonal | #EF7F79 | STATIC_COMPOSITE | sombras demasiado rosadas |

### F08 · Gastronomía y bebidas

Base #17110D; tipografía orientativa #FFF4E6. Excluir por defecto: fotografía de plato donde se necesite comunicar color real.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C057 | Copa ámbar nocturna | copa de vidrio y barra oscura | brillo miel de líquido y fondo bokeh | #DB9A42 | STATIC_COMPOSITE | bebida parece distinta |
| VP019-C058 | Marisco azul profundo | concha sobre piedra mojada | luz cian localizada sobre humedad | #65BCD2 | STATIC_COMPOSITE | alimento con color falso |
| VP019-C059 | Panadería al amanecer | pan, harina y ventana | sol naranja difuso en corteza | #EFB26A | STATIC_COMPOSITE | pan demasiado saturado |
| VP019-C060 | Café cobre | taza negra, espresso y vapor | rim cobre en vapor y reflejo cerámico | #B97848 | STATIC_COMPOSITE | vapor contaminando texto |
| VP019-C061 | Coctelería violeta | copa martini, hielo y neón | reflejo violeta por cristal y barra | #A26FD5 | STATIC_COMPOSITE | reflejos irreales |
| VP019-C062 | Restaurante verde oliva | plato de cerámica y hojas | luz oliva ambiental tras mesa | #A2B879 | STATIC_COMPOSITE | comida verde artificial |
| VP019-C063 | Chocolate terciopelo | praliné oscuro y espátula | highlight cálido sobre textura de cacao | #CE8D61 | STATIC_COMPOSITE | textura plastificada |
| VP019-C064 | Vino rosado al atardecer | copa vacía de marca ficticia | halo coral en copa y mantel | #E68588 | STATIC_COMPOSITE | publicidad de alcohol y contexto |

### F09 · Automoción y movilidad

Base #090F16; tipografía orientativa #F1F4F7. Excluir por defecto: fichas de estado de vehículos e informes de seguridad.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C065 | Carrocería cian en túnel | coupé genérico y pared hormigón | bandas de luz cian reflejadas en chapa | #28BCD2 | OFFLINE_3D | reflejo incongruente con túnel |
| VP019-C066 | Motocicleta rojo cereza | moto custom sobre suelo mojado | rim rojo en depósito y charcos | #E34155 | OFFLINE_3D | forma de la moto alterada |
| VP019-C067 | Bicicleta verde lima | bici urbana y sombra de árboles | reflejos lima en llantas y pavimento | #C4DF67 | STATIC_COMPOSITE | geometría de ruedas |
| VP019-C068 | Cabina azul cielo | interior de coche futurista | luz azul de tablero en vidrio lateral | #77C1E8 | OFFLINE_3D | pantallas ilegibles |
| VP019-C069 | Furgoneta cobre | vehículo de reparto sin marca | luz cálida bajo carrocería y chapa | #C48762 | OFFLINE_3D | marca inventada |
| VP019-C070 | Tren plateado noche | tren moderno en estación | línea blanca en borde y reflejo gris | #C3D0DF | STATIC_COMPOSITE | línea de seguridad |
| VP019-C071 | Vehículo eléctrico amatista | sedán con suelo espejo | contraluz violeta y halo bajo ruedas | #9A7EEE | OFFLINE_3D | sombras flotantes |
| VP019-C072 | Superficie carbono ámbar | detalle de tejido de carbono | rasante ámbar sobre fibra y metal | #E79C42 | OFFLINE_3D | patrón fibra falso |

### F10 · Viajes, aviación y experiencias

Base #11192A; tipografía orientativa #F5F5F4. Excluir por defecto: información de navegación/horarios de transporte.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C073 | Ala de avión coral | ala abstracta sobre nubes | ocaso coral reflejado sobre perfil metálico | #EF8B80 | STATIC_COMPOSITE | logo de aerolínea ajena |
| VP019-C074 | Tren a través de Alpes | ventanal panorámico y montañas | rayos dorados cruzan vidrio y asiento | #E7B763 | STATIC_COMPOSITE | nieve amarillenta |
| VP019-C075 | Montaña índigo nocturna | cima nevada y firmamento | luz azul sobre arista y cielo profundo | #779EFB | STATIC_COMPOSITE | cielos físicamente falsos |
| VP019-C076 | Hotel en desierto rojo | hotel conceptual de adobe | luz rojiza rasante en arcos | #DD795B | STATIC_COMPOSITE | arquitectura sin escala |
| VP019-C077 | Terminal cobalto | silueta de pasarela y pista | luz cobalto en líneas de horizonte | #4989DD | STATIC_COMPOSITE | señalización confundida |
| VP019-C078 | Barco vintage de cobre | cubierta de madera y vapor | cobre cálido contra mar oscuro | #CB8C5B | STATIC_COMPOSITE | época incongruente |
| VP019-C079 | Teleférico lavanda | cabina transparente sobre bosque | vapor violeta en cables y sol bajo | #C1A2E7 | STATIC_COMPOSITE | cable irreal |
| VP019-C080 | Sendero ártico jade | camino de nieve y aurora | verde jade de aurora en montaña distante | #6CC6A1 | STATIC_COMPOSITE | ausencia aurora diurna |

### F11 · Salud, bienestar y servicios humanos

Base #102024; tipografía orientativa #F7FAF6. Excluir por defecto: información clínica donde decoración afecte comprensión o exactitud.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C081 | Ondas de agua salvia | superficie de agua muy calma | luz salvia difusa sobre ondas | #9CBFA7 | STATIC_COMPOSITE | tono sanitario sin evidencia |
| VP019-C082 | Consulta serena azul | interior clínico luminoso | rebote azul pálido desde ventana | #A4CCDF | STATIC_COMPOSITE | contraste insuficiente |
| VP019-C083 | Textil de lino arena | cortinas, lino y luz lateral | sol arena sobre fibras, fondo limpio | #E1CBA7 | STATIC_COMPOSITE | texto sobre fibras |
| VP019-C084 | Bosque terapéutico | troncos y sombra verde | rayos verdes de follaje sin neón | #7EAE96 | STATIC_COMPOSITE | simular efectos médicos |
| VP019-C085 | Botella de agua coral | objeto transparente sobre piedra | halo coral tenue junto a base | #D98E85 | OFFLINE_3D | promesas de eficacia |
| VP019-C086 | Jardín de hospital | patio con sombras uniformes | luz verde lima suave en muro lejano | #BCD68E | STATIC_COMPOSITE | vistas demasiado oscuras |
| VP019-C087 | Yoga ultramar claro | siluetas genéricas en estudio | luz azul indirecta en pared, sin foco en rostro | #8CADD8 | STATIC_COMPOSITE | retrato artificial |
| VP019-C088 | Cerámica blanca amatista | cuenco y vela apagada | luz malva en borde cerámico | #B29DCB | STATIC_COMPOSITE | ambiente lúgubre |

### F12 · Deporte, fitness y rendimiento

Base #0D1212; tipografía orientativa #FCFFFA. Excluir por defecto: gráficas de métricas deportivas y botones destructivos.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C089 | Estadio verde eléctrico | césped oscuro y focos | línea verde en túnel de salida | #A8E96A | STATIC_COMPOSITE | marcado de campo falso |
| VP019-C090 | Atleta rojo cinético | silueta anónima de corredor | rim rojo en hombro y suelo | #FF565A | STATIC_COMPOSITE | contorno de persona |
| VP019-C091 | Pista azul ultravioleta | pista de atletismo nocturna | azul en carriles lejanos no oficiales | #678DFC | STATIC_COMPOSITE | señalización competitiva falsa |
| VP019-C092 | Gimnasio cobre | pesas de hierro y concreto | halo cobre detrás de mancuernas | #C6814A | STATIC_COMPOSITE | peso real deformado |
| VP019-C093 | Balón plateado | balón sin marca sobre piso oscuro | plata en textura y reflejo redondo | #C5D7D8 | OFFLINE_3D | pentágonos inventados |
| VP019-C094 | Piscina azul glacial | nadador anónimo bajo agua | cáusticas azul hielo sobre carril | #60BFE5 | OFFLINE_3D | carril mal alineado |
| VP019-C095 | Pared escalada coral | presa, cuerda y roca artificial | luz coral localizada desde costado | #FF8E73 | STATIC_COMPOSITE | cuerda invisible |
| VP019-C096 | Deporte urbano violeta | cancha nocturna y aro | neón violeta detrás del tablero | #A177E5 | STATIC_COMPOSITE | lectura de líneas reglamentarias |

### F13 · Software, IA y tecnología

Base #090F1B; tipografía orientativa #F1F7FF. Excluir por defecto: interfaces de operación críticas, logs y diagnósticos.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C097 | Nodo holográfico cian | objeto abstracto de malla de datos | filamentos cian iluminados desde centro | #40C9E2 | OFFLINE_3D | sensación falsa de datos reales |
| VP019-C098 | Chip de cobre | silicio genérico y pistas | resplandores cobre en circuitos sobre PCB | #DB9A5D | OFFLINE_3D | arquitectura de chip inventada |
| VP019-C099 | Cristal de cómputo amatista | bloque cristalino poligonal | bordes lavanda y volumen interior | #A68BEF | OFFLINE_3D | exceso de abstracción |
| VP019-C100 | Anillo de señal lima | anillo flotante y niebla oscura | luz lima desde ranura perimetral | #B2EA65 | OFFLINE_3D | confundido con estado de éxito |
| VP019-C101 | Servidor azul índigo | pasillo de servidores genéricos | líneas azules a ras de racks | #6789FA | STATIC_COMPOSITE | inducir falsas capacidades |
| VP019-C102 | Superficie de datos coral | placas negras en perspectiva | franja coral sobre relieve sintético | #E67B7A | OFFLINE_3D | texto de UI fingido |
| VP019-C103 | Fibras ópticas doradas | cables de fibra y vidrio | puntos ámbar en extremos de fibra | #E4B45C | STATIC_COMPOSITE | cableado imposible |
| VP019-C104 | Malla metálica esmeralda | hilos metálicos entrelazados | luces verde jade en cruces materiales | #62CAA9 | OFFLINE_3D | patrón que se repite visiblemente |

### F14 · Finanzas, asesoría y servicios jurídicos

Base #0E1920; tipografía orientativa #F8F5ED. Excluir por defecto: trámites, simuladores de crédito y resultados legales.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C105 | Biblioteca legal azul petróleo | estanterías y luz de ventana | luz azul tenue en molduras posteriores | #4F9FBD | STATIC_COMPOSITE | apariencia de despacho ajeno |
| VP019-C106 | Columna de mármol champán | arquitectura clásica sin insignias | canto ámbar sobre columna y escalón | #CFAD79 | STATIC_COMPOSITE | símbolos oficiales implícitos |
| VP019-C107 | Puerta de nogal oliva | puerta tallada genérica | luz verde oliva rasante en umbral | #9BB483 | STATIC_COMPOSITE | demasiada oscuridad |
| VP019-C108 | Volumen de piedra gris plata | piedra labrada y sombra | franja plateada en textura lejana | #AFBBC7 | STATIC_COMPOSITE | gris sin diferenciación |
| VP019-C109 | Pluma de metal azul | pluma estilográfica sin marca | reflejo azul profundo solo en metal | #79A9CE | OFFLINE_3D | alegoría demasiado genérica |
| VP019-C110 | Escritorio de cuero cobre | mesa de cuero y papeles en blanco | cobre tenue de lámpara lateral | #C78D65 | STATIC_COMPOSITE | papeles falsos o sensibles |
| VP019-C111 | Ventanal de ciudad verde | rascacielos abstractos a distancia | luz verde salvia entre cristales | #88B9A9 | STATIC_COMPOSITE | falsa sede real |
| VP019-C112 | Reloj de pared oro mate | reloj sin sello y pared oscura | reflejo oro en bisel, cero glow | #CDB275 | STATIC_COMPOSITE | promesas de puntualidad engañosas |

### F15 · Ciberseguridad y defensa digital

Base #050C12; tipografía orientativa #F4FAFF. Excluir por defecto: pantallas reales con alarmas, severidades o indicadores de seguridad.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C113 | Bóveda azul de acero | puerta abstracta de acero pulido | rim cobalto en bisagra | #4E9AE8 | OFFLINE_3D | parece certificación oficial |
| VP019-C114 | Escudo de vidrio ámbar | forma original sin insignias | luz ámbar en canto y suelo | #E7B763 | OFFLINE_3D | similitud con insignias protegidas |
| VP019-C115 | Malla de vigilancia lima | red geométrica no técnica | nodos lima aislados sobre grafito | #B4E86A | OFFLINE_3D | métricas inventadas |
| VP019-C116 | Centro de datos rojo | pasillo vacío con cableado | rojo tenue en una arista física | #CB4257 | STATIC_COMPOSITE | parece alerta crítica |
| VP019-C117 | Frontera de luz turquesa | planos de metal y hueco central | rayo turquesa cruzando rendija | #43B8C1 | OFFLINE_3D | hueco demasiado brillante |
| VP019-C118 | Tejido de carbono violeta | superficie de fibra oscura | trazo violeta en una sola fibra | #9D8AEC | STATIC_COMPOSITE | decoración por encima del mensaje |
| VP019-C119 | Faro de datos plateado | torre abstracta sin marca | foco plateado entre humo y acero | #C2D4DF | OFFLINE_3D | densidad volumétrica |
| VP019-C120 | Cerco de cobre | anillo de grafito con ranuras | luz cobre emitida por ranura interna | #CE925F | OFFLINE_3D | parece gadget físico inexistente |

### F16 · Energía, industria e infraestructura

Base #111714; tipografía orientativa #F5F6F1. Excluir por defecto: diagramas de planta, avisos de seguridad y representaciones regulatorias.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C121 | Turbina viento amanecer | aerogenerador sin marca y bruma | contraluz dorado en pala y suelo | #E7BF6B | STATIC_COMPOSITE | borde de pala incorrecto |
| VP019-C122 | Panel solar turquesa | filas de paneles y cielo azul | reflejo cian en vidrio, no iluminación artificial | #57C1CC | STATIC_COMPOSITE | rendimiento simulado |
| VP019-C123 | Fábrica de cobre | tuberías limpias y metal | cobre en soldaduras y reflejos | #CB8558 | STATIC_COMPOSITE | maquinaria inventada |
| VP019-C124 | Central térmica naranja | silueta industrial conceptual | luz ámbar en interior de rejillas | #F3A351 | STATIC_COMPOSITE | simular emisiones |
| VP019-C125 | Robot industrial lima | brazo mecánico genérico | luz lima en articulaciones protectoras | #B9D868 | OFFLINE_3D | seguridad de brazo falso |
| VP019-C126 | Laboratorio azul hielo | instrumental y superficies inox | reflejo azul frío en pared y metal | #8CC9E2 | STATIC_COMPOSITE | instrumento ficticio |
| VP019-C127 | Grúa portuaria roja | grúa en niebla y muelle | trazo rojo en viga de elevación | #E55C59 | STATIC_COMPOSITE | señales operativas alteradas |
| VP019-C128 | Infraestructura subterránea jade | túnel y cables protegidos | halo jade bajo luminaria del techo | #7DC49D | STATIC_COMPOSITE | confundir vías de emergencia |

### F17 · Editorial, cultura y artes

Base #171320; tipografía orientativa #F7F1E8. Excluir por defecto: lectura prolongada sobre imágenes ruidosas.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C129 | Escultura azul medianoche | escultura original de piedra | luz azul desde pedestal, sombras definidas | #5E92CE | STATIC_COMPOSITE | obra ajena sin licencia |
| VP019-C130 | Galería terracota | cuadros abstractos y pared yeso | luz terracota de ventana lateral | #CF8168 | STATIC_COMPOSITE | cuadros derivados de artistas |
| VP019-C131 | Teatro violeta | butacas vacías y telón oscuro | spot violeta en pliegue del telón | #A58BE8 | STATIC_COMPOSITE | teatro demasiado oscuro |
| VP019-C132 | Libro con polvo ámbar | libro original sin título y mesa | banda ámbar entre hojas y partículas | #E1B15F | STATIC_COMPOSITE | contenido falso en páginas |
| VP019-C133 | Vinilo coral | vinilo negro sin sello | reflejo coral en ranuras circulares | #E67478 | OFFLINE_3D | textura del disco falsa |
| VP019-C134 | Archivo de papel verde | cajas de archivo y papel | rebote salvia en bordes de hojas | #8EB89E | STATIC_COMPOSITE | documentos ilegibles |
| VP019-C135 | Pincel plata | pinceles y estudio oscuro | línea plateada en cerdas húmedas | #BEC4D1 | STATIC_COMPOSITE | obra de artista no acreditada |
| VP019-C136 | Museo oro viejo | salón de museo abstracto | luz dorada suave detrás de pedestal | #C6A06A | STATIC_COMPOSITE | obra o museo no real |

### F18 · Videojuegos, esports y entretenimiento

Base #090812; tipografía orientativa #FAF7FF. Excluir por defecto: menús funcionales donde el efecto visual compita con opciones.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C137 | Portal violeta | arco de piedra original y niebla | aura púrpura desde hueco, sombras a contraluz | #9B6CF4 | OFFLINE_3D | efecto tapa la interfaz |
| VP019-C138 | Arena roja infernal | arena ficticia y roca negra | luz roja bajo grietas, nunca textos de UI | #EB4C5B | OFFLINE_3D | sobresaturación agresiva |
| VP019-C139 | Mundo flotante cian | isla baja poligonal en nubes | cian bajo borde de isla y niebla | #4CDDE3 | OFFLINE_3D | isla flota sin sombra |
| VP019-C140 | Controlador cromado verde | mando original sin marcas | reflejo lima en botones no funcionales | #B6F06E | OFFLINE_3D | semántica falsa de botones |
| VP019-C141 | Ciudad cyberpunk rosa | edificios ficticios y lluvia | neón rosa en fachadas y charcos | #F07ABE | STATIC_COMPOSITE | imitación de IP visual |
| VP019-C142 | Caverna de cristales azul | cristales hexagonales y oscuridad | emisión azul y rebote en roca | #6EACF2 | OFFLINE_3D | cristales como UI falsas |
| VP019-C143 | Nave espacial cobre | hull abstracto, sin franquicia | cobre en rejillas de motor apagado | #C98A5B | OFFLINE_3D | franquicia reconocible |
| VP019-C144 | Escenario laser dorado | tarima vacía y humo | haz oro en lateral, escenario principal limpio | #E3BC66 | OFFLINE_3D | parpadeo o fotosensibilidad |

### F19 · Educación, ciencia y descubrimiento

Base #101928; tipografía orientativa #F6F9FB. Excluir por defecto: gráficos científicos que necesitan valores medidos y colores normativos.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C145 | Microscopio azul | microscopio genérico de laboratorio | rim azul frío en metal y objetivo | #66BCE4 | OFFLINE_3D | simular un dispositivo real |
| VP019-C146 | Modelo molecular coral | bolas y varillas decorativas | coral en enlaces puramente abstractos | #EB7F7B | OFFLINE_3D | molécula científica falsa |
| VP019-C147 | Biblioteca verde salvia | estanterías y mesa de estudio | salvia de ventana en pared superior | #95C7AC | STATIC_COMPOSITE | libros ilegibles |
| VP019-C148 | Planetario púrpura | cúpula oscura y estrellas sintéticas | halo violeta sobre arco de proyección | #AA87E6 | STATIC_COMPOSITE | cielo ficticio presentado como real |
| VP019-C149 | Laboratorio de prisma ámbar | prisma y haces experimentales | luz ámbar refractada como ilustración | #F1BE68 | OFFLINE_3D | física no representativa |
| VP019-C150 | Tiza cian sobre pizarra | pizarra sin fórmulas y tiza | luz cian sobre borde de marco | #58D1D3 | STATIC_COMPOSITE | inventar fórmulas |
| VP019-C151 | Observatorio rojo | telescopio conceptual y crepúsculo | ocaso rojo bajo el horizonte | #DE6864 | STATIC_COMPOSITE | falsa ubicación histórica |
| VP019-C152 | Libro de ciencia hielo | atlas propio sin páginas identificables | luz azul hielo en contorno de páginas | #9ED4EC | STATIC_COMPOSITE | gráficas falsas |

### F20 · Propiedades exclusivas e inmobiliaria

Base #141A1A; tipografía orientativa #FAF9F3. Excluir por defecto: fotografía de propiedades reales cuando se altere la condición del inmueble.

| ID | Concepto | Escena/material | Propagación de luz | Acento | Producción | Riesgo principal |
|---|---|---|---|---|---|---|
| VP019-C153 | Villa de piedra al ocaso | villa original con piscina y olivos | coral en horizonte y reflejo sobre agua | #E98B72 | STATIC_COMPOSITE | alterar prestaciones reales |
| VP019-C154 | Fachada de vidrio champagne | casa contemporánea con cristal | sol dorado reflejado en muros y suelo | #D7B473 | STATIC_COMPOSITE | falsa iluminación interior |
| VP019-C155 | Escalera esmeralda | escalera volada y patio interior | luz jade debajo de peldaños en sombra | #55B998 | OFFLINE_3D | peldaños arquitectónicamente irreales |
| VP019-C156 | Penthouse azul profundo | balcón con ciudad abstracta | reflejo azul en baranda y piedra negra | #648DBD | STATIC_COMPOSITE | skyline falso de ciudad real |
| VP019-C157 | Casa de bosque ámbar | madera negra y pinos | luz ámbar desde ventana hacia follaje | #DDB35D | STATIC_COMPOSITE | inventar distribución interior |
| VP019-C158 | Piscina negra lavanda | lámina de agua y microcemento | lavanda discreta en borde y rebote | #A69CCD | STATIC_COMPOSITE | color de agua incorrecto |
| VP019-C159 | Portal de acceso cobre | entrada de villa con listones | cobre rasante sobre puerta y pavimento | #C98C63 | STATIC_COMPOSITE | dimensiones inventadas |
| VP019-C160 | Terraza con niebla lima | casa baja y vegetación mediterránea | verde lima como rebote vegetal natural | #B6CD75 | STATIC_COMPOSITE | verdes irreales por filtros |

## Protocolos de selección (no son puntuaciones pre-verificadas)

- Contexto: lujo/servicio/producto/educación/industria vs funcionalidad crítica.
- Sujetos: paisaje/fachada/interior/objeto refractivo/metal/textil/agua/volumen abstracto.
- Luz: contraluz, rasante, borde, rebote, cáustica, reflexión especular, ventana, emisión localizada, bruma/volumetría.
- Intensidad: elegir la menor que exprese el propósito y supere el peor contraste.
- Composición: espacio seguro para HTML y recorte móvil, distinto del contenido de la imagen.
- Coste: medir frente a imagen estática; los lanes son hipótesis técnicas, no evidencias de producción.
- Autorización: los 160 prototipos requieren un nuevo arte propio o con derechos; ninguna captura del vídeo constituye un asset disponible.

## Recorrido de promoción

HYPOTHESIS → SOURCE_ASSET_CLEARED → PROTOTYPED → RENDER_TESTED → APPLICABILITY_TESTED → APPROVED_FOR_PATTERN_USE → BASELINE_CANDIDATE (solo si existe evidencia de transferencia). Los estados no son obligaciones de avanzar; rechazo/retirada son resultados válidos.

## Protocolo de casos negativos

No se considerará logrado si: (a) el modelo produce una imagen bonita sin CTA real; (b) el móvil corta el sujeto; (c) la luz de borde no coincide con arquitectura; (d) no se prueban contraste y tamaño; (e) se crean supuestas fotos reales de propiedades; (f) un agente no puede descubrir el candidato; (g) se aprueban solo imágenes de un gusto subjetivo o una única familia.

## Fuentes verificables de mecanismos, no de las 160 ideas

- [VP-019 y observación del vídeo](../cinematic-brand-lit-hero.md).
- [Blender: render passes, Light Groups y Cryptomatte](https://docs.blender.org/manual/en/latest/render/layers/passes.html).
- [MDN: background-blend-mode](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/background-blend-mode).
- [OpenPBR: material, roughness y refracción](https://experienceleague.adobe.com/en/docs/substance-3d/general-knowledge/openpbr/openpbr-overview).
