# brand_kit: Miga Común (fixture)

Marca **inventada**, solo para el benchmark CDIO entre sectores. Cooperativa de panadería de barrio ficticia; no representa a ningún negocio real. Comprobación de nombre limitada a una búsqueda web ("Miga Común" panadería cooperativa): sin coincidencia exacta, pero no es una búsqueda de marca registrada.

## Cómo se hicieron los activos
CCF no tiene proveedor de imágenes en este equipo (sin OPENAI_API_KEY, comprobado por el agente padre), así que **los SVG están escritos a mano**. No se ejecutó `ccf generate`.

- `symbol.svg`: hogaza (cúpula + base) con tres cortes como huecos (`evenodd`). Un solo color, sin texto, sin trazos finos.
- `wordmark.svg`: usa **`<text>`**, no trazos convertidos a curvas. Su rasterizado depende de las fuentes instaladas: `Source Serif 4, Georgia, 'Times New Roman', serif`. Sin Source Serif 4 se verá en Georgia, con otras métricas.
- Ambos SVG van en terracota (`#BC4A2D`) para valer sobre fondo claro y oscuro; las versiones en tinta/crema no se entregan como archivos.
- `index.html` + `styles.css`: hoja de marca en español, un acento, sin blanco puro. Google Fonts es la única dependencia externa.

## Sin verificar
Esta ejecución no tenía shell: no se corrieron `design_review_record.py render` ni `modules.cdio.taste`. Los ratios de contraste de la paleta están calculados a mano.
