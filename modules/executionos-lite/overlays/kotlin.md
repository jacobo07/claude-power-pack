# Overlay: Kotlin (MC-OVO-30 — 3 of 8 language overlays)

Loads when CWD contains `build.gradle.kts`, `settings.gradle.kts`, `*.kt`, `*.kts`, `gradle/libs.versions.toml`, or a `Podfile` referencing Kotlin Multiplatform. ~280 tokens.

Covers **JVM server Kotlin** (Spring Boot / Ktor / Vert.x) AND **Kotlin Multiplatform** (KMP library / shared module). Android-specific guidance lives in `overlays/android-native.md` — prefer it for Android app code; use this file when the target is JVM backend or KMP shared code.

- **Build system:** Gradle Kotlin DSL (`build.gradle.kts`) is canonical — never mix with Groovy DSL in the same repo. Version catalog (`gradle/libs.versions.toml`) for dep versions. `./gradlew wrapper --gradle-version 8.x` pinned per repo. JDK version declared in `gradle.properties` (`org.gradle.java.home`) or `toolchain {}` block — never rely on the CI default.
- **Null safety:** `!!` (non-null assertion) is a delivery-blocker in non-test code. Every `!!` needs an inline `// SAFETY:` comment explaining the invariant that makes it safe. Prefer `?.let { ... }`, `?: throw`, or explicit `checkNotNull(x) { "reason" }`. Platform types (unmarked Java interop) MUST be narrowed to `T?` or `T` at the boundary, never propagated.
- **Coroutines:** `suspend fun` for all I/O and blocking calls. NEVER call `runBlocking` outside `main`/`@Test` — it blocks the thread and defeats the purpose. `CoroutineScope` is structured concurrency: cancel the scope on shutdown, children cancel too. Use `supervisorScope` when one child's failure should NOT cancel siblings (e.g., parallel HTTP fetches where partial results are acceptable).
- **Dispatchers:** `Dispatchers.IO` for blocking I/O (JDBC, file I/O, legacy sync APIs). `Dispatchers.Default` for CPU-bound. `Dispatchers.Main` ONLY on Android / JavaFX. NEVER `GlobalScope.launch` in library code — leaks context and lifecycle.
- **Flow:** `Flow<T>` over `Sequence<T>` for anything that crosses a suspend boundary. `SharedFlow` / `StateFlow` for hot event streams (replace `BehaviorSubject` / `BroadcastChannel`). Cold `Flow` is single-consumer — use `shareIn(scope)` or `stateIn(scope)` when multiple collectors need it.
- **Error handling:** `Result<T>` or typed sealed classes over thrown exceptions for RECOVERABLE errors. Exceptions for INVARIANT violations. Never catch `Throwable` — catch the specific type. `CancellationException` must be re-thrown in `catch` blocks (structured concurrency depends on it).
- **Data classes & immutability:** `data class` for records (equals/hashCode/copy generated). `val` over `var` by default — `var` requires a comment justifying mutation. `List` over `MutableList` in public APIs. `@JvmRecord` for Java interop at JDK 16+.
- **Null-correct interop:** when calling Java APIs, assume every return is `T?` until you've verified the Java source's `@NotNull`/`@Nullable` annotations OR test-inputted null. `Iterable<T>` from Java may contain null elements — use `filterNotNull()` defensively.
- **Testing:** `kotest` (assertions + property tests) or JUnit 5 + `kotlin.test`. `runTest {}` for coroutine tests (virtual time, instant cancellation). `MockK` for mocking — prefer real fakes or in-memory implementations. `@ParameterizedTest` for table-driven cases.
- **Dependency injection:** Koin (pure Kotlin DSL, no annotation processing) for smaller projects, Spring/Micronaut (JVM-standard) for larger backends. Dagger/Hilt ONLY for Android. NEVER service-locator (`ServiceLocator.get()`) in new code.
- **Compilation & lint:** `./gradlew compileKotlin compileTestKotlin` + `ktlint` (or `detekt` for structural rules) in CI. `-Werror` on the compiler for production modules. `-Xjsr305=strict` flag enables JSR-305 nullability annotations as errors.
- **Verification gate:** `./gradlew clean build` (includes test) AND `./gradlew detekt` (or `ktlintCheck`) AND `./gradlew dependencyCheckAnalyze` (OWASP dep vuln scan) must ALL pass. On KMP projects, also `./gradlew allTests` to run iOS/JS/native-targets locally — deferred to CI if cross-toolchain unavailable.

### KMP-specific (if `expect`/`actual` seen in source)

- `expect` declarations in `commonMain` — `actual` implementations per target (`androidMain`, `iosMain`, `jvmMain`, `jsMain`, `nativeMain`).
- Platform-specific code stays in its target dir; `commonMain` may only reference stdlib + multiplatform libraries (kotlinx.coroutines, kotlinx.serialization, ktor-client).
- iOS target requires macOS + Xcode — route to `apple-ecosystem.md` overlay for Xcode-specific guidance. Linux/Windows CI can build common + jvm + js targets but not iOS (same constraint as Swift native: Apple toolchain is macOS-only).

### Fragile-language note (Ley 25 context)

Kotlin on JVM inherits JVM's strengths (mature GC, JIT, library ecosystem) and weaknesses (startup latency, memory footprint vs native). Coroutines close the "callback hell" gap but do NOT deliver OTP-style supervision — for highly-concurrent actor systems with fault-tolerance requirements, Elixir still wins. Kotlin wins on JVM-native interop (Spring Boot, Android, existing Java codebases) and on developer ergonomics over raw Java.
