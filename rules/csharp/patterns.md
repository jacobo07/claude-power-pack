---
paths:
  - "**/*.cs"
  - "**/*.csx"
---
<!-- Source: ECC v2.0.0-rc.1 (github.com/affaan-m/ECC), MIT License (c) 2026 Affaan Mustafa. Mirrored into the claude-power-pack rules taxonomy during the ECC absorption gap pass (2026-06-06). Adapt in place as PP doctrine evolves. -->

# C# Patterns

> This file extends [common/patterns.md](../common/patterns.md) with C#-specific content.

## API Response Pattern

```csharp
public sealed record ApiResponse<T>(
    bool Success,
    T? Data = default,
    string? Error = null,
    object? Meta = null);
```

## Repository Pattern

```csharp
public interface IRepository<T>
{
    Task<IReadOnlyList<T>> FindAllAsync(CancellationToken cancellationToken);
    Task<T?> FindByIdAsync(Guid id, CancellationToken cancellationToken);
    Task<T> CreateAsync(T entity, CancellationToken cancellationToken);
    Task<T> UpdateAsync(T entity, CancellationToken cancellationToken);
    Task DeleteAsync(Guid id, CancellationToken cancellationToken);
}
```

## Options Pattern

Use strongly typed options for config instead of reading raw strings throughout the codebase.

```csharp
public sealed class PaymentsOptions
{
    public const string SectionName = "Payments";
    public required string BaseUrl { get; init; }
    public required string ApiKeySecretName { get; init; }
}
```

## Dependency Injection

- Depend on interfaces at service boundaries
- Keep constructors focused; if a service needs too many dependencies, split responsibilities
- Register lifetimes intentionally: singleton for stateless/shared services, scoped for request data, transient for lightweight pure workers
