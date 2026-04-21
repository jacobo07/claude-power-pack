# Overlay: Rust (MC-OVO-30 partial — 1 of 8 language overlays)

Loads when CWD contains `Cargo.toml`, `rust-toolchain.toml`, or `*.rs` files. ~200 tokens.

- **Framework routing:** web → Axum (preferred) or Actix-web; CLI → `clap` (derive API); async runtime → Tokio (single runtime, no mixing with async-std). Embedded → `embedded-hal` + RTIC or Embassy.
- **Error handling:** `thiserror` for libraries (typed errors), `anyhow` for binaries (boxed errors). Never `unwrap()` or `expect()` on hot paths; use `?` + context via `anyhow::Context::with_context`. Panics are for invariants that should crash, not for recoverable input.
- **Async:** `async fn` + `tokio::spawn` for concurrent tasks. NEVER block the runtime with `std::thread::sleep` or sync I/O inside an async context — use `tokio::time::sleep` and `tokio::fs`. (Ties to Mistake #39 — Synchronous Default Trap.)
- **Lifetimes & ownership:** prefer owned types in public APIs unless profiling proves borrowing wins. `&str` over `String` only in tight loops. Avoid `Rc<RefCell<T>>` outside single-threaded contexts — use `Arc<Mutex<T>>` or `Arc<RwLock<T>>` for shared state, and strongly prefer channels (`tokio::sync::mpsc`) over shared state.
- **Unsafe:** every `unsafe` block needs a `// SAFETY:` comment stating the invariant. `unsafe fn` is banned in new code unless interop with C. Run `cargo miri test` on any module containing `unsafe`.
- **Types:** no `as` casts on integer widening (lossy cast risk on platform differences) — use `TryFrom` + `.map_err(...)`. Use `NonZeroU32` / `NonZeroUsize` for invariant-carrying values. Newtype wrappers for domain IDs (`struct UserId(u64)`).
- **Testing:** `#[cfg(test)]` modules co-located with code. `cargo test --all-features` in CI. Property tests via `proptest` for pure logic. Integration tests in `tests/`. Target ≥70% line coverage via `cargo-llvm-cov`.
- **Dependencies:** pin major versions in `Cargo.toml`, run `cargo audit` before every release, `cargo deny` for license + vulnerability gates. Minimum supported Rust version (MSRV) declared in `rust-toolchain.toml` or `Cargo.toml [package.rust-version]`.
- **Formatting & lint:** `cargo fmt --check` + `cargo clippy -- -D warnings` in CI. Pre-commit hook must run both. Any clippy allow must carry a `// clippy:allow justified-by: <one-line>` comment.
- **Build profiles:** `release` profile with `lto = "thin"`, `codegen-units = 1`, `panic = "abort"` for binaries; `debug = true` only when size cost justified. Debug binary should stay under 5× release for CI cache economy.
- **Unsafe + FFI:** every C binding goes through `bindgen` + a hand-written safe wrapper layer. Document owner of every raw pointer (who frees, who borrows).
- **Verification gate:** `cargo check --all-targets && cargo clippy --all-targets -- -D warnings && cargo test --all-features && cargo audit` must ALL pass — non-zero exit on any → delivery-blocking. For no_std / embedded, add `cargo build --target <triple>` for each supported target.

### Fragile-language note (Ley 25 context)

Rust IS in the "fragile" band *only* when used for async daemons with heavy concurrency — Tokio gives you the primitives but supervision trees are hand-rolled. For daemon/service code with ≥4 fragility-criteria matches (per execution.md T), the Elixir-First directive still applies: Rust is OK when the task is CPU-bound (codecs, parsers, compute kernels, embedded) and loses to Elixir when the task is "many independent supervised actors."
