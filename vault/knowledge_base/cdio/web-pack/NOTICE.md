# NOTICE -- Creative Web Pack (CDIO-13)

## Method

The method in `../CDIO-13-creative-web-pack.md` (three reference websites, build flow, three
recipes, four checks, build prompt) is absorbed from **"The WEB Pack"** by **Sanjai Builds**
(@sanjai.builds, codeconstellation.in), a free resource published in 2026 with the instruction
"FREE · SHARE IT". The build prompt is quoted verbatim with attribution. The pack states that its
skill suggestions "are learning recommendations, not claims that the original creators used
them"; this dataset keeps that statement. The three reference websites (sweet-tape.com,
era-residence.com, nickho-motorsports.nl) are named as references only; nothing from them is
copied here.

## Vendored skills

`vendor/<owner>__<repo>/` holds a text-only copy of each repo below at the pinned commit
(`manifest.json`: commit, licence, and the upstream sha256 of every file). Each copy keeps its
own licence file; that file governs the copy.

| Repo | Commit | Licence | Licence file in this copy |
|---|---|---|---|
| greensock/gsap-skills | aed9cfd3277740755f6bfc1155c7aa645403b760 | MIT | `vendor/greensock__gsap-skills/LICENSE` |
| nateherkai/scroll-craft | 75d81f74e83692add18cd7a8a8e078b8a887a579 | MIT | `vendor/nateherkai__scroll-craft/LICENSE` |
| MengTo/Skills | see `manifest.json` | MIT | `vendor/MengTo__Skills/LICENSE` |
| iart-ai/web-animation-skills | ed3a045192679b24d32090ee7a983871311ababd | MIT | `vendor/iart-ai__web-animation-skills/LICENSE` |
| iart-ai/webgl-animation-skills | 0041933813688c357804f7b13dcb85095c5a3210 | MIT | `vendor/iart-ai__webgl-animation-skills/LICENSE` |
| JustineBijuPaul/frontend-ai-skills | f52d23c5b8f51caefccb97ea2bc88f6db7bc6120 | MIT | `vendor/JustineBijuPaul__frontend-ai-skills/LICENSE` |
| anthropics/skills (frontend-design, docx, pdf, pptx, xlsx) | e4bb5d960d87126ff3b3a8af1a104b7db67560ba | Apache-2.0 | `vendor/anthropics__skills/skills/<skill>/LICENSE.txt` |

## Live skills (installed by install.ps1 / install.sh)

`live/<name>/` holds the complete upstream skill folder, every file, at the pinned commit
(`live/live-manifest.json`: commit, upstream path and sha256 per file).
`tools/install_cdio_live_skills.py` copies each into `~/.claude/skills/<name>` unless that skill
is already installed or provided by a plugin.

| Skill | Repo and folder | Commit | Licence | Licence file in this copy |
|---|---|---|---|---|
| impeccable | pbakaus/impeccable `.claude/skills/impeccable` | b49177d32788f2dc585c42831d845dacf1ebed2c | Apache-2.0 | `live/impeccable/LICENSE` (repo root licence, added because the folder has none) |
| ui-ux-pro-max | nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/ui-ux-pro-max` | f2f7266b07805025421611656045e9b44b41e2eb | MIT | `live/ui-ux-pro-max/LICENSE` (repo root licence, added because the folder has none) |
| anydesign | uxKero/anydesign (root) | d81bd8957a21c2d7fba8d2a8f4f60050d09368b5 | MIT | `live/anydesign/LICENSE` |

The older `vendor/skills/ui-ux-pro-max/` at the repo root is an archival stub (its `data/` and
`scripts/` are placeholders) and is left as it was; the working copy is `live/ui-ux-pro-max/`.

## Modifications

None to any vendored file's content. Files were **omitted**, never edited: images, GIFs, video,
fonts, minified library copies and files over 200 KB (OOXML `.xsd` schemas exempt). Every omitted
path is listed under `skipped` in `manifest.json`. Demo pages that referenced omitted media will
not render their images; the SKILL.md guidance does not depend on them.

## Not vendored

Lenis (darkroomengineering/lenis), Drei (pmndrs/drei) and React Three Fiber
(pmndrs/react-three-fiber), all MIT, are runtime libraries: a site installs them from npm. They
are never copied into this pack.
