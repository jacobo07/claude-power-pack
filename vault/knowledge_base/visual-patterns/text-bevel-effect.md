---
id: VP-001
name: Text Bevel Effect
type: pattern
domain: visual-patterns
status: active
---

# VP-001 — Text Bevel Effect (efecto bisel de texto via CSS)

Reusable branding pattern for differentiating two words in one title that carry
distinct roles or identities (e.g. a base product name plus a qualifier/variant).

## Cuando usar

Diferenciar semanticamente dos palabras en un mismo titulo cuando tienen roles
o identidades distintas (producto + calificador).

- Ej: "InfinityOps" (nombre base) + "Social" (variante/calificador).
- Ej futuro: cualquier proyecto del Owner con dos tokens de nombre donde el
  segundo merece identidad visual propia.

## Cuando NO usar

- Cuerpo de texto, parrafos, UI funcional (botones, labels, inputs).
- Solo aplica a titulos hero, logotipos, headings de producto.
- No usar si el fondo es variable o el contraste no puede garantizarse.

## Implementacion (sin codigo)

`background-clip: text` + gradiente vertical sobre el token de color.

- Requiere: token dark + token light del mismo hue.
- Gradiente: dark (top) -> light (50%) -> dark (bottom).
- El color base es el token "dark" — el light solo aparece en el centro.

## Tokens requeridos

Dos tokens por color: `--color-[nombre]` y `--color-[nombre]-light`.
El gradiente NUNCA es hardcoded — solo tokens.

## WCAG

Verificar contraste en light y dark mode antes de declarar done. El teal claro
sobre fondo oscuro puede perder contraste — la variante dark debe garantizar
legibilidad minima.

## Componente

Siempre encapsular en un componente reutilizable (`SocialBrand`, etc). El
gradiente vive en el componente, nunca copiado en cada pagina.

## Evidence

Implementado en `infinity_ui/components/SocialBrand.tsx`. Verificado en
produccion (VPS) con light y dark mode.

## Applicability

Proyectos del Owner con UI publica (infinity_ui, CostaLuz, etc). No aplicar
en CLI tools, dashboards internos o herramientas de dev.
