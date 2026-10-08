---
id: VP-022
name: Scramble Text Reveal (revelado cifrado accesible)
type: pattern
domain: visual-patterns
status: active
motion:
  applies_to: [landing, hero, product-tour]
  excluded_from: [checkout, auth, form, destructive, docs, settings, admin, dashboard]
  min_expressiveness: moderate
  min_motion_budget: medium
  requires_reduced_motion: equivalent
  evidence_level: research
  provenance: REF-KITCHEN-001
  purpose: "que un valor que cambia (enlace generado, codigo, titular) muestre que es nuevo, sin que el lector de pantalla oiga caracteres basura"
---

# VP-022 — Scramble Text Reveal

## Eje

Movimiento (B7) — revelado de texto caracter a caracter.

## Tecnica (sin codigo)

Cuando el texto cambia, los caracteres aun no revelados se sustituyen en cada
tick por simbolos aleatorios y el valor nuevo aparece de izquierda a derecha.

Contrato observado en REF-KITCHEN-001 (OBSERVED):

1. **Duracion acotada por construccion**: tick de 32 ms y un maximo de 48 pasos
   de revelado, de modo que un texto largo revela varios caracteres por tick en
   lugar de alargar la animacion. INFERRED: ~1.5 s como maximo.
2. **Graphemes, no unidades de codigo**: segmentar por grafema (Intl.Segmenter
   cuando existe) para no romper emojis ni letras acentuadas compuestas.
3. **Los espacios nunca se cifran**: la forma de las palabras se mantiene y el
   texto no "salta" de ancho.
4. **Primer render estable**: el cifrado inicial es determinista (por hash), no
   aleatorio, para que servidor y cliente pinten lo mismo.
5. **Accesibilidad por duplicado**: la capa animada esta oculta a tecnologias de
   apoyo y una copia visualmente oculta con `aria-live="polite"` y
   `aria-atomic="true"` contiene solo el valor final.
6. **Se omite** si no hay texto, si el intervalo es 0 o si el usuario pide
   movimiento reducido.

## Cuando usar

- Valores generados que el usuario va a copiar (enlace de invitacion, token de
  ejemplo, codigo): el cifrado dice "esto es nuevo".
- Titulares de marketing con una sola palabra que rota.

## Cuando NO usar

- Datos que el usuario lee mientras cambian (precios, saldos, estados de
  pedido): durante ~1.5 s el valor visible es falso.
- Texto de cuerpo o parrafos: fatiga y no aporta.
- Productos de seguridad o pagos: imitar "cifrado" sobre un valor real sugiere
  una proteccion que no existe (colision de confianza).
- Mas de un elemento cifrandose a la vez en la misma vista.

## Movimiento reducido (equivalente, no ausente)

El valor final aparece directamente. La copia accesible no cambia, asi que el
anuncio es identico con y sin animacion.

## Soporte de navegador

Intl.Segmenter: navegadores actuales; con alternativa por puntos de codigo
cuando no existe. Usar una fuente monoespaciada o tabular si el ancho no debe
oscilar.

## Contraste y WCAG

Los simbolos de relleno se pintan con el mismo color que el texto final: el
contraste no cambia durante el revelado. WCAG 2.3.3 cubierto por la omision con
movimiento reducido.

## Coste de mantenimiento

Bajo: un temporizador que se limpia al terminar y al desmontar.

## Evidence

Investigacion: REF-KITCHEN-001 componente 2.

## Fuentes

- https://www.dqnamo.com/experiments/scramble-text (solo principios; sin licencia declarada).
