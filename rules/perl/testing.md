---
paths:
  - "**/*.pl"
  - "**/*.pm"
  - "**/*.t"
  - "**/*.psgi"
  - "**/*.cgi"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# Perl Testing

> This file extends [common/testing.md](../common/testing.md) with Perl-specific content.

## Framework

Use **Test2::V0** for new projects (not Test::More):

```perl
use Test2::V0;

is($result, 42, 'answer is correct');

done_testing;
```

## Runner

```bash
prove -l t/              # adds lib/ to @INC
prove -lr -j8 t/         # recursive, 8 parallel jobs
```

Always use `-l` to ensure `lib/` is on `@INC`.

## Coverage

Use **Devel::Cover** — target 80%+:

```bash
cover -test
```

## Mocking

- **Test::MockModule** — mock methods on existing modules
- **Test::MockObject** — create test doubles from scratch

## Pitfalls

- Always end test files with `done_testing`
- Never forget the `-l` flag with `prove`

## Reference

See skill: `perl-testing` for detailed Perl TDD patterns with Test2::V0, prove, and Devel::Cover.
