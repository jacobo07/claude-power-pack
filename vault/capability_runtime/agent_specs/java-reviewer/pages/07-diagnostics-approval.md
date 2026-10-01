## Diagnostic Commands

```bash
# Common
git diff -- '*.java'

# Build & verify
./mvnw verify -q                             # Maven
./gradlew check                              # Gradle

# Static analysis
./mvnw checkstyle:check
./mvnw spotbugs:check
./mvnw dependency-check:check                # CVE scan (OWASP plugin)

# Framework detection greps
grep -rn "@Autowired" src/main/java --include="*.java"          # [SPRING]
grep -rn "@Inject" src/main/java --include="*.java"             # [QUARKUS]
grep -rn "FetchType.EAGER" src/main/java --include="*.java"
grep -rn "@Singleton" src/main/java --include="*.java"          # [QUARKUS]
grep -rn "listAll\|findAll" src/main/java --include="*.java"
grep -rn "PanacheMongoEntity\|PanacheMongoRepository" src/main/java --include="*.java"  # [QUARKUS]
```

Read `pom.xml`, `build.gradle`, or `build.gradle.kts` to determine the build tool and framework version before reviewing.

## Approval Criteria
- **Approve**: No CRITICAL or HIGH issues
- **Warning**: MEDIUM issues only
- **Block**: CRITICAL or HIGH issues found

For detailed patterns and examples:
- **[SPRING]**: See `skill: springboot-patterns`
- **[QUARKUS]**: See `skill: quarkus-patterns`
