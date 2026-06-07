---
paths:
  - "**/*.php"
  - "**/composer.json"
  - "**/phpstan.neon"
  - "**/phpstan.neon.dist"
  - "**/psalm.xml"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# PHP Hooks

> This file extends [common/hooks.md](../common/hooks.md) with PHP specific content.

## PostToolUse Hooks

Configure in `~/.claude/settings.json`:

- **Pint / PHP-CS-Fixer**: Auto-format edited `.php` files.
- **PHPStan / Psalm**: Run static analysis after PHP edits in typed codebases.
- **PHPUnit / Pest**: Run targeted tests for touched files or modules when edits affect behavior.

## Warnings

- Warn on `var_dump`, `dd`, `dump`, or `die()` left in edited files.
- Warn when edited PHP files add raw SQL or disable CSRF/session protections.
