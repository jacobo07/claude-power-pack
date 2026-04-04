# Android/Native Optimization Overlay

> Loaded when CWD contains `android`, `pojav`, `jni`, `ndk`, or `gradle`. ~200 tokens.

## Big Core Affinity (C Layer)
When initializing graphics or compute-heavy native code on Android:
- Call `bigcore_set_affinity()` early in the C init path (e.g., `egl_bridge.c` in `pojavInitOpenGL`)
- Guard with environment variable: `if(getenv("POJAV_BIG_CORE_AFFINITY")) { bigcore_set_affinity(); }`
- Include proper header (`bigcoreaffinity.h`) or forward-declare: `void bigcore_set_affinity(void);`
- Why: ARM big.LITTLE schedulers don't prioritize graphics threads without explicit affinity

## Android Thread Priority (Java Layer)
Before entering any heavy game/render loop (e.g., `runCraft()`):
- `android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_DISPLAY);`
- Call BEFORE the loop entry, not inside it
- Why: Default priority is 0 (NORMAL), display is -4 — closer to real-time scheduling

## GC Thread Sizing (JVM Arguments)
When building JVM arguments (e.g., `JREUtils.buildGCArguments()`):
```java
int gcThreads = Math.max(1, Math.min(Runtime.getRuntime().availableProcessors() / 2, 4));
int concThreads = Math.max(1, gcThreads / 2);
// Inject into args:
// -XX:ParallelGCThreads={gcThreads}
// -XX:ConcGCThreads={concThreads}
```
- Why: Default GC threads often equals CPU count — too high on mobile, causes contention with game threads

## NIO Buffer Hints (JVM System Properties)
For Java apps doing heavy file I/O (world loading, resource packs):
- `-Dsun.nio.ch.disableSystemWideOverlappingFileLockCheck=true` — avoids lock contention on shared storage
- `-Djdk.nio.maxCachedBufferSize=262144` — cap buffer cache at 256KB (mobile memory constraint)
- Why: Default NIO assumes server workloads with abundant RAM

## Verification Gate
`./gradlew clean assembleDebug --warning-mode all` must pass with 0 errors.
If C compilation fails (missing headers), fix the include path — do NOT skip the native build.
