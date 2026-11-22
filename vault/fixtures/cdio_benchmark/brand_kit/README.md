# brand_kit: Miga Común (fixture)

Marca **inventada**, solo para el benchmark CDIO entre sectores. Cooperativa de panadería de barrio ficticia; no representa a ningún negocio real. Comprobación de nombre limitada a una búsqueda web ("Miga Común" panadería cooperativa): sin coincidencia exacta, pero no es una búsqueda de marca registrada.

## Cómo se hicieron los activos
CCF no tiene proveedor de imágenes en este equipo (sin OPENAI_API_KEY), así que **los SVG están escritos a mano**. No se ejecutó `ccf generate`.

- `symbol.svg`: hogaza alargada vista de lado, con tres cortes diagonales como huecos (`evenodd`). Una sola forma, un color, sin texto ni trazos finos.
- `wordmark.svg`: "Miga Común" en Source Serif 4 Bold **convertido a curvas** con fontTools; no depende de fuentes instaladas.
- `lockup.svg` (terracota, para fondos claros) y `lockup-inverse.svg` (crema, para fondos oscuros): símbolo + logotipo, también en curvas.
- `fonts/`: Source Serif 4 Bold e Inter 400/600 en woff2, recortadas a latín (licencia SIL OFL 1.1). La hoja no hace ninguna petición externa.
- `index.html` + `styles.css`: hoja de marca en español, un acento, sin blanco puro.

## Verificado
- Ratios de contraste de la paleta calculados por script (luminancia relativa WCAG 2.x); coinciden con los publicados en la hoja.
- Render y revisión: ver `render_*.txt`, `taste_*.txt`, `review_*.json` y `record_*.txt` en esta carpeta.
