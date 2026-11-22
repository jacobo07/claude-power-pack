---
id: VP-019
name: Local Discovery Assistant Scene (simulated conversation + imagined payoff)
type: pattern
domain: visual-patterns
status: baseline
baseline_scope: local-business sites and sales demos made with CDIO (cafés, restaurants, shops)
baseline_by: Owner, 2026-11-21 ("que esto sea el baseline de las webs que haga CDIO")
evidence_level: local
---

# VP-019 — Local Discovery Assistant Scene

## Eje

Narrativa visual (E1): a single scene that explains why a local business needs a web. It sells being **known**,
not merely located.

## Qué es

One vertical picture, about 9:16, in three parts:

1. **A phone in a generic messaging interface.** Use a generic «Asistente» with a neutral sparkle icon and never name
   a real assistant brand. The header says «Conversación simulada · <momento>».
2. **A short exchange:**
   - A visitor at a real local landmark asks a natural question («Acabo de llegar a la estación de … ¿Dónde puedo
     desayunar algo casero cerca de aquí?»).
   - The assistant recommends the business with its real neighbourhood and street, what kind of place it is, what
     customers mention, and one attribute. It ends by offering directions.
   - The visitor answers «Sí, voy para allá».
3. **The payoff, under a rule:** a small caption, an illustration of the product, and a serif line spoken at the
   counter («Lola, qué bocadillo más bueno. Me lo recomendó el móvil nada más llegar a Algeciras.»). A disclaimer closes
   the picture.

Reference: Lola's Cafetería, `src/demo.html` (`#ia`, `.scene-fig`). The asset is `assets/escena-ia.png`, and
`tools/build.py` refuses the build if its sha256 changes (`SCENE_SHA256`).

## Reglas de construcción (obligatorias)

1. **Every assistant sentence traces to a typed fact**, as in the lesson
   `small-business-site-evidence-gated-release`. In Lola's:
   - Neighbourhood and street → `direccion`.
   - «Desayunos y meriendas» → `rotulo` and `autodescripcion`.
   - «Quienes han ido mencionan…» → `productos`. This is an OPINION_TERCEROS claim, so it is attributed to customers
     and never stated as a fact.
   - «Tiene terraza» → `atributos`.

   Emphasis words are claims too. «Sobre todo», «el mejor» and «famoso por» each need evidence of their own.
2. **The simulation label exists twice.** It appears in the picture and as real page text: a tag, plus a figcaption
   that says what is NOT real (no real conversation, no checked assistant recommendation, no real testimonial). A
   label that exists only in pixels cannot be checked or read by a screen reader.
3. **Raster text gets a transcript.** The `alt` describes the picture, and a visually hidden block repeats every word
   of it, with page data (the street) templated from the data file.
4. **Bind the asset to its transcript.** A sha256 constant in the build stops a new picture shipping with an old
   transcript.
5. **Embed it lightly.** WebP at quality 82 (1.85 MB PNG → 110 KB), with `width`/`height`, `loading="lazy"` and
   `decoding="async"`. It is embedded as a data URI when the demo must be self-contained.
6. **Calm frame.** Centred, at most ~470 px wide, one soft shadow, no motion. The picture carries the story.

## Cuándo usar

- In a sales demo, or in the «why a web» section for a local business whose customers find it by asking a phone
  («dónde desayunar cerca de …»).
- When at least an address, a category and one attributable customer-opinion claim exist as typed facts.

## Cuándo NO usar

- **On the business's own official site.** There a simulated recommendation would read as an endorsement the
  business staged. Use it only in demos and proposals addressed to the owner.
- When the assistant lines would need facts we do not have. Do not invent a dish, a rating or «el mejor de la
  zona»; cut the line instead.
- When the business has not consented to being named in an illustrative scene (instance 4 of the lesson: owner
  declined). Use a fictional name, or skip the scene.
- When the picture imitates a real brand's interface closely enough to suggest that brand endorsed it (a named
  assistant, a real logo). Keep it generic.
- As a substitute for measurement. The scene shows a possibility; whether assistants actually recommend the business
  stays `NO_MEDIDO` in the AI-visibility panel until it is observed.

## Soporte de navegador

WebP is supported by every current browser. The transcript uses the project's `.vh` (visually hidden) class.

## Contraste y WCAG

- 1.1.1: a descriptive `alt` plus a full text transcript.
- 1.4.5: the text is inside the image, which is allowed because the same words are available as text.
- The disclaimer and the tag are real text at body contrast.

## Coste de mantenimiento

Low until a fact changes. If the street, the attributes or what customers mention change, the picture must be
regenerated, its transcript updated and the sha256 constant bumped. The build forces the last two.

## Evidence

- Lola's Cafetería, demo `/demo/#ia`. Gates: `check_demo.py` 18/18, `verify.py` without failures, overflow-free at
  320/390/768/1440. Rendered and checked by eye at 390 and 1440 (2026-11-21).
- `evidence_level: local` means one implementation so far. `status: baseline` is the Owner's decision of
  2026-11-21, not a measured promotion.

## Fuentes

- Owner-supplied picture «Descubrimiento local en Lola's Cafetería» (2026-11-21).
- `~/.claude/knowledge_vault/lessons/small-business-site-evidence-gated-release.md` (evidence gate, instances 1-6).
