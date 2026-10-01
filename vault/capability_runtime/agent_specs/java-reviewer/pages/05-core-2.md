### MEDIUM -- Concurrency and State
- **Mutable singleton fields**: Non-final instance fields in singleton-scoped beans are a race condition
  - **[SPRING]**: `@Service` / `@Component`
  - **[QUARKUS]**: `@ApplicationScoped` / `@Singleton`
- **Unbounded async execution**:
  - **[SPRING]**: `CompletableFuture` or `@Async` without a custom `Executor` — default creates unbounded threads
  - **[QUARKUS]**: `ExecutorService.submit()` or `@ActivateRequestContext` with `@Async` without a managed `ManagedExecutor`
- **Blocking `@Scheduled`**: Long-running scheduled methods that block the scheduler thread
  - **[QUARKUS]**: Use `concurrentExecution = SKIP` or offload to a worker thread
- **[QUARKUS] Reactive stream misuse**: Building `Uni`/`Multi` pipelines that subscribe more than once or share mutable state between subscribers

### MEDIUM -- Java Idioms and Performance
- **String concatenation in loops**: Use `StringBuilder` or `String.join`
- **Raw type usage**: Unparameterised generics (`List` instead of `List<T>`)
- **Missed pattern matching**: `instanceof` check followed by explicit cast — use pattern matching (Java 16+)
- **Null returns from service layer**: Prefer `Optional<T>` over returning null
- **[QUARKUS] Not leveraging build-time init**: Using runtime reflection or classpath scanning that could be replaced by Quarkus build-time extensions or `@RegisterForReflection`

### MEDIUM -- Testing
- **Over-scoped test annotations**:
  - **[SPRING]**: `@SpringBootTest` for unit tests — use `@WebMvcTest` for controllers, `@DataJpaTest` for repositories
  - **[QUARKUS]**: `@QuarkusTest` for unit tests — reserve for integration tests; use plain JUnit 5 + Mockito for units
- **Missing mock setup**:
  - **[SPRING]**: Service tests must use `@ExtendWith(MockitoExtension.class)`
  - **[QUARKUS]**: `@InjectMock` misuse — reserve for CDI integration tests, use plain Mockito for unit tests
- **[QUARKUS] Missing `@QuarkusTestResource`**: Integration tests requiring external services should use Dev Services or `@QuarkusTestResource` with Testcontainers
- **`Thread.sleep()` in tests**: Use `Awaitility` for async assertions
- **Weak test names**: `testFindUser` gives no information — use `should_return_404_when_user_not_found`

