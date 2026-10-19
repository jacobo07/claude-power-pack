---
covers: [ttb-wii-sdk, two-builders, pc-edition, character-fidelity, feature-contract]
tier: T1
status: DRAFT, awaiting Owner confirmation of critical features and allowed deviation
date: 2026-10-19
---

# TTB PC edition: character feature contracts (Jacobo, Madzia)

Evidence level of the references: REFERENCE (Owner-provided concept renders). Nothing here is BUILT or APPROVED.
Owner statement 2026-10-19: the blonde girl is Madzia, the black-haired one is Jacobo; the images in Downloads are the truth.

## Reference registry (SHA-256, originals in `C:\Users\User\Downloads`, never overwritten)
| Role | File | SHA-256 |
|---|---|---|
| Jacobo sheet | file_00000000c1c48211809fb06364900755.png | 83726127cf90843b808da561a8977ca97e00daccb18d5be0840a3b63bf67f1fc |
| Madzia sheet | file_00000000ce4081f4a5ab024223bac3a8.png | 736f4be9b2cd55298a775a94b771a36dfaacbcf9c25b8fd02092a8ceaa871a67 |
| Cantina hub concept (not a character ref) | IMG-20261014-WA0020(1).jpg | 8fd3e987ce661f0df2387add28c6ec5d997c859c77f592574ba91d473567515d |

Discrepancy: `vault/tower/sources/ttb-fidelity-v3/TTB_Evidence_Manifest_v3.json` lists the two sheet filenames with different hashes
(9d47e8a8..., 8c28238b...). Only the Cantina file matches. The three files `1000521199/170/173.png` are not in Downloads. Treat the
Downloads files as the references; the audit's hashes describe other bytes under the same names.

## Jacobo (observed in the sheet; Owner to confirm criticality)
- Hair: dark brown/black, short messy and spiky, fringe falling over the forehead, uneven tufts on top and sides.
- Face: thick dark eyebrows, brown eyes, small closed smile, light skin tone.
- Torso: cream/white Jedi tunic, dark brown cross-over vest, brown belt with a silver buckle.
- Back: dark brown cape; the hair is visible from behind with the same spiky outline.
- Lower: white trousers with brown seam lines.

## Madzia (observed in the sheet; Owner to confirm criticality)
- Hair: long straight blonde, centre part, falls past the shoulders, smooth, no fringe over the eyes.
- Face: green-grey eyes with lashes, thin eyebrows, light pink lips, smile.
- Torso: white tunic, brown belt with brown rectangular buckles.
- Back: dark brown cape; long blonde hair over it.
- Lower: white trousers with black seam lines.

## Owner standard (2026-10-19): "no acepto ninguna desviación"
Recorded as the Owner's stated acceptance threshold: zero allowed deviation, for both characters. Agent note, not an Owner decision:
the references are painted renders (soft light, depth, strand-level hair, expressive eyes); the game draws a low-poly minifig with a fixed
head print and rigid molded hair. Literal pixel identity is not reachable by construction, so the gate is judged feature by feature, with
the Owner as the only judge, and every capture is a candidate until the Owner signs. Open question to the Owner: is "the reference design
translated into the game's LEGO style, every critical feature present and recognisable" the bar, or something stricter?

## Per asset, to fill with the Owner
| Field | Jacobo | Madzia |
|---|---|---|
| Critical features | (proposal: hair silhouette, eyebrows, face, vest) | (proposal: long hair, eyes, face, belt) |
| Known unknowns | hair geometry on PC (S2 mesh half, S3 untested) | same |
| Allowed deviation | OWNER TO STATE | OWNER TO STATE |
| Required captures | front, 3/4, back, face close-up in game | same |
| Status | REFERENCE only | REFERENCE only |
