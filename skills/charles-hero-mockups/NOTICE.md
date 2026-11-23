# NOTICE: charles-hero-mockups

Source: https://github.com/LemonFace0309/charles-skills, path `skills/drops/charles-hero-mockups`.
Commit: 738e27ffecda9e8ac37279cfc37446d7ef22794d (2026-11-23). Fetched and installed 2026-11-22 (local time) at the
Owner's request.

License: MIT, Copyright (c) 2026 Charles Liu. The full text follows.

## Copied verbatim
`README.md`, `references/craft.md`, `scripts/heroes.py`, `scripts/ocr.swift`, and `SKILL.md` above its last section.

## Deliberate divergences
1. `SKILL.md` has a local "Power Pack (this host)" section at the end. It covers the Windows interpreter and the
   `-X utf8` requirement, the no-key path, the spend gate, the skipped macOS word check, and how the design router
   loads the skill. Upstream text is untouched.
2. `scripts/heroes_codex.py` is a local file, not upstream. It imports `heroes.py` unchanged and replaces only
   `openai_key` and `call`, so renders go through the Owner's Codex CLI (`codex exec`, built-in image generation,
   ChatGPT login) instead of the OpenAI Images API. This is the default path on this host (Owner, 2026-11-23).
3. `gallery/` (six example JPEGs, about 1 MB) is not copied. `README.md` still points at it, so those images do not
   display. Nothing the skill runs reads them.

## Wiring
- Router: kind `hero_mockup` in `vault/config/design_routes.json`.
- Activation criteria: project `CLAUDE.md`.
- Mirror: `~/.claude/skills/charles-hero-mockups/`.
- Gate: `python tools/test_charles_hero_mockups.py` (V-CHM-*).

## MIT License

Copyright (c) 2026 Charles Liu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
