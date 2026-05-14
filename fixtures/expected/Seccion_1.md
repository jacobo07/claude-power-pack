## 1. Ingestor Atómico (IRE Stage 1-2)

El Ingestor Atómico es la puerta de entrada del sistema. Acepta entradas crudas y emite sidecars chunked, redacted y size-capped que la Capa de Destilación consume sin volver a leer el original. Tres modalidades caen dentro del alcance v1 — la primera es la única que materializa output en este ciclo; las otras dos quedan reservadas para `/ultra` cycles futuros.

1. **Texto masivo.** Segmentación automática de archivos > 1 MB para evitar el colapso de contexto en LLMs. El cap duro de `ingest.py` es 1 MB; el flag `--force` lo levanta a cambio de un registro auditable.
2. **Transcripción de audio/vídeo.** Integración tipo Whisper para destilar gameplays de 40 min en texto. Fuera de alcance v1.
3. **Vision-to-Data.** Extracción de metadatos arquitectónicos de imágenes (DNA v2 de estadios). Fuera de alcance v1.

Antes de que un chunk toque el LLM, el ingestor aplica tres gates no-negociables: rechazo de placeholders (`TODO`, `FIXME`, `Coming Soon`, `<TU_URL_REAL>`), redacción de secretos por regex (Discord webhooks, claves SSH, paths `~/.ssh/<name>`, tokens `kobicraft_*`, AWS keys, GitHub PATs, Bearer JWTs) y chunking por encabezado `^## ` con fallback a bloques de 50 KB. El original NUNCA se muta; el resultado redactado se escribe a un sidecar `.ingest.json` junto al input.

El ingestor es el primer eslabón del Contrato de Realidad: lo que entra impuro no llega al LLM. Si el operador pasa `--force` para superar el cap, la decisión queda registrada en el sidecar para auditoría posterior.

### 🧮 Calculadora de ROI

- **Tipo:** Temporal / Riesgo
- **ROI Temporal:** 50×–100× (minutos futuros / minuto invertido en pre-cleaning manual).
- **ROI Riesgo:** Crítico. Bloquea fugas de secretos antes de que el LLM los vea — el coste de una sola filtración de webhook supera el ahorro de doce sesiones limpias.
- **Escenario:** Agresivo (gate obligatorio para el 11 de junio).
- **Explicación:** El ingestor convierte el flujo "leer-limpiar-pegar" manual en una llamada idempotente. El operador deja de ser el filtro humano de seguridad y el sistema gana superficie auditable.

🏁 Cierre patrimonial — **Acelera.** Cada minuto que el ingestor opera limpio es un minuto que el Owner no gasta como guardia de seguridad de su propio dataset. Es la primera capa de soberanía: el sistema decide qué entra al cerebro.

🦅 Comentario del Oráculo — Si la puerta de entrada no es férrea, ninguna pureza posterior compensa el ruido inicial. El Ingestor es la diferencia entre destilar agua de manantial y destilar agua de charco.
