---
id: VP-002
name: Gradient Text
type: pattern
domain: visual-patterns
status: active
---

# VP-002 — Gradient Text (patron padre)

Patron base de relleno de texto via gradiente. [[text-bevel-effect]] (VP-001,
A2) es la variante vertical dark->light->dark de este mismo patron — no lo
duplica, lo especializa.

## Eje

Relleno-texto (A1)

## Tecnica (sin codigo)

`background-clip: text` (+ prefijo `-webkit-`) con `color: transparent` sobre
un elemento con `background: linear-gradient(...)`. El texto queda relleno
por el gradiente en vez de un color solido.

## Cuando usar

- Cualquier titulo/wordmark donde dos o mas tonos de marca deban convivir en
  el mismo bloque de texto sin recurrir a `<span>` por color.
- Base tecnica antes de aplicar cualquier variante (bisel, metalico, stroke).

## Cuando NO usar

- Cuerpo de texto o parrafos largos — el ojo pierde el ancla de lectura
  cuando el color cambia dentro de una linea.
- Fondos variables/impredecibles donde el contraste del gradiente no puede
  garantizarse en cada punto del texto.

## Variantes

- Horizontal, diagonal o radial (en vez de vertical).
- [[text-bevel-effect]] (VP-001): vertical dark->light->dark — la variante ya
  implementada en produccion.

## Tokens requeridos

`--color-[nombre]`, `--color-[nombre]-alt` (minimo 2 stops del gradiente,
nunca valores hardcoded).

## Soporte de navegador

`background-clip: text` esta soportado en todos los navegadores modernos;
Safari (incluyendo versiones WebKit antiguas) requiere el prefijo
`-webkit-background-clip` + `-webkit-text-fill-color: transparent` para
funcionar — omitirlo deja el texto invisible en Safari viejo, no con color
solido de respaldo.

## Contraste y WCAG

El contraste debe verificarse en el punto MAS CLARO del gradiente contra el
fondo, no en el promedio — un gradiente que "parece" tener buen contraste
en su tono medio puede fallar WCAG AA en el extremo mas claro.

## Coste de mantenimiento

Bajo — CSS puro, 2 tokens, sin JS, sin asset externo.

## Evidence

Patron base sin implementacion propia; ver [[text-bevel-effect]] (VP-001)
para la variante en produccion (`infinity_ui/components/SocialBrand.tsx`).

## Fuentes

- [30 Modern CSS Text Effects (2026)](https://veebilehed24.ee/en/blog/modern-css-text-effects-2026/)
- [20 CSS Gradient Text Designs — CodeFronts](https://codefronts.com/design-styles/css-gradient-text/)
- [Latest CSS Gradient Features and Trends for 2026 — CSS-Zone](https://css-zone.com/blog/css-gradient-trends-2026)
