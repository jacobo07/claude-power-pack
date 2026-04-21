# Overlay: PHP (MC-OVO-30-LANG — 6 of 8 language overlays)

Loads when CWD contains `composer.json`, `composer.lock`, `*.php`, `artisan` (Laravel), `bin/console` (Symfony), or `wp-config.php` (WordPress). ~260 tokens.

- **PHP version:** require `^8.3` or newer in `composer.json` `require.php`. Pin in `.php-version` (for `asdf`/`phpenv`). PHP 7.x is EOL — refuse to ship new code targeting it.
- **Framework routing:** Laravel for convention-driven monoliths; Symfony for explicit configuration + Flex recipes; Slim / Mezzio for micro-services; WordPress ONLY when extending an existing WordPress install (never for green-field APIs). For CLI → Symfony Console component (even in non-Symfony projects).
- **Composer discipline:** `composer.json` declares every dep with tilde or caret pinning; `composer.lock` committed for apps, NOT for libraries. `composer install --no-dev --optimize-autoloader` in production; `composer update` ONLY in a dedicated upgrade PR. Platform requirements (`ext-pdo`, `ext-mbstring`, etc.) declared explicitly so deployment fails fast on missing extensions.
- **Type discipline:** `declare(strict_types=1);` at top of EVERY new PHP file (forces strict parameter/return-type coercion). Type-hint every parameter and return. Use `?Type` for nullable, `Type|null` only for Psalm/PHPStan compatibility. No `mixed` without an inline comment stating why.
- **Static analysis:** PHPStan or Psalm at level 8 (max) or 9 (Psalm) in CI. `phpstan analyse` as part of `composer test`. New projects start at level 8; legacy projects ratchet up one level per sprint.
- **Exceptions over false:** throw typed `\Exception` subclasses for errors, NEVER return `false` from functions that logically have a successful T return. Legacy PHP APIs that return false-on-error (e.g., `fopen`) should be wrapped: `$fh = @fopen(...); if ($fh === false) throw new IOException("...");`.
- **`@` error suppression banned:** only acceptable pattern is the wrapper above (suppress + check + throw); bare `@` hides bugs.
- **Autoloading:** PSR-4 via `composer.json` `autoload.psr-4`. No `require_once` in new code — composer's autoloader handles it. `classmap` entries only for legacy non-namespaced code migration.
- **Secrets:** `.env` via `vlucas/phpdotenv`; NEVER commit `.env`. `.env.example` committed with placeholder values. Laravel's `config:cache` in production pre-compiles env reads for perf.
- **Laravel specifics (if artisan detected):** Eloquent's `firstOrFail()` over `first()` + null-check; queued jobs via `ShouldQueue` interface + explicit queue name (NEVER default queue); Form Requests for validation at controller boundary; policies for authorization (not inline `if` checks); `php artisan migrate --force` in deploy (non-interactive).
- **Symfony specifics (if bin/console detected):** DI container with autowiring + autoconfiguration; `#[Route]` attributes over YAML/annotations (PHP 8+); event subscribers over listeners (explicit methods); Doctrine Migrations with `doctrine:migrations:migrate --no-interaction` in deploy.
- **Testing:** PHPUnit 11+ or Pest. Dataset providers for table-driven tests. `@covers` annotations required so coverage shows class-level scope correctly. Integration tests via Laravel's `RefreshDatabase` trait or Symfony's `KernelTestCase`.
- **Dependencies:** `composer outdated -D` weekly; `composer audit` (8.2+) for CVE checks. Disable Packagist signed packages ONLY via explicit opt-out — default is secure.
- **Verification gate:** `composer install --no-dev --optimize-autoloader` + `./vendor/bin/phpstan analyse --level=8` + `./vendor/bin/phpunit` (or `pest`) + `composer audit` must ALL exit 0. For Laravel add `php artisan test` which wraps PHPUnit with Laravel helpers.

### Fragile-language note (Ley 25 context)

PHP-FPM with a per-request shared-nothing model gives you free isolation (each request is its own process, crash = one 500, not cascading). That's a structural advantage over Node/Python/Ruby for naïve scaling. But: long-running workers (Laravel Queue, Symfony Messenger) lose that advantage and need the same supervision discipline as any fragile-language daemon. For those, score fragility criteria and apply Elixir-First if ≥4. PHP wins on: classic request/response web stacks, CMS integrations, LAMP-shop familiarity. Prefer Elixir for WebSocket servers, long-lived workers, and fault-tolerant background processing.
