# Apple Ecosystem Overlay — macOS + iOS (MC-OVO-33)

> Loaded when CWD contains `.xcodeproj`, `.xcworkspace`, `Package.swift`, `Podfile`, `fastlane/`, or `*.swift` files at top level. ~280 tokens.
>
> **Platform prerequisite:** macOS host with Xcode ≥15 installed. Linux CI can run SPM builds headless but cannot run xcodebuild / simulator — route those gates to a macOS runner (or defer with honest label per Ley 28).

## Project shape detection

| Signal | Project type | Primary build tool |
|---|---|---|
| `.xcodeproj` or `.xcworkspace` | App / framework (GUI) | `xcodebuild` |
| `Package.swift` | Swift Package (library or CLI) | `swift build` / `swift test` |
| `Podfile` | CocoaPods deps | `pod install` before build |
| `fastlane/Fastfile` | Release automation | `bundle exec fastlane <lane>` |
| `.xcconfig` | Build-config override layer | read first, never inline secrets |

Prefer SPM over CocoaPods for NEW projects (2020+ Apple direction). CocoaPods stays for legacy repos and pods without SPM manifests.

## Code signing — non-negotiable checklist

Before any `xcodebuild archive` / fastlane `gym`:
- [ ] Dev team set in project settings (`DEVELOPMENT_TEAM` build setting)
- [ ] Provisioning profile exists and matches bundle ID + entitlements
- [ ] Entitlements file (`*.entitlements`) present and matches App ID capabilities (push, iCloud, HealthKit, etc.)
- [ ] Signing identity in Keychain (use `security find-identity -v -p codesigning`)
- [ ] For CI: `fastlane match` with an encrypted git repo is the SSoT; never check `.mobileprovision` into the project repo
- [ ] Notarization (macOS apps, not iOS): app must pass `spctl --assess --type execute` before DMG distribution

## fastlane lanes — minimum three

```ruby
# fastlane/Fastfile
lane :test do
  run_tests(scheme: "<AppScheme>", devices: ["iPhone 15"])
end

lane :beta do
  match(type: "appstore")  # or "adhoc" for internal
  build_app(scheme: "<AppScheme>")
  upload_to_testflight(skip_waiting_for_build_processing: true)
end

lane :release do
  ensure_git_status_clean
  match(type: "appstore")
  build_app(scheme: "<AppScheme>")
  upload_to_app_store(submit_for_review: false)  # Owner manual submit
end
```

Never auto-submit for review without Owner sign-off — App Store review rejection has cooldown cost.

## Simulator vs device — Reality Contract

A test that passes on simulator but not device is NOT verified (Mistake #17 variant). Simulator uses host CPU (x86_64 or Apple Silicon) and differs from device ARM64 on: memory limits, file system case sensitivity, background task lifecycle, push notifications, HealthKit, camera/LiDAR, Apple Pay, biometrics. Ship-blocking verification must include at least one device build per release.

## Verification gates (run ALL applicable)

```
SPM:         swift build && swift test                     → 0 errors, all tests pass
Xcode unit:  xcodebuild -scheme <X> -destination '...' test → exit 0
Xcode build: xcodebuild -scheme <X> archive                → .xcarchive produced
SwiftLint:   swiftlint --strict                            → 0 violations
fastlane:    bundle exec fastlane test                     → exit 0
Podfile:     pod install --deployment                      → 0 warnings
Notarize:    xcrun notarytool submit --wait                → status=Accepted
```

## Honest deferral for Linux-only hosts (VPS context)

On a Linux VPS (no Xcode), you CAN:
- Run `swift build` / `swift test` on SPM packages via `swiftlang/swift:latest` docker image
- Lint Swift via SwiftLint in docker
- Run fastlane dry-run for syntax validation

You CANNOT:
- Run `xcodebuild`, simulator, or device deploys
- Sign for distribution (needs Keychain + Apple ID on macOS)
- Notarize (Apple service needs macOS network identity)

Label any Linux-only run as **"static-verified on Linux; runtime/signing deferred to macOS host"** — never collapse the two claims (Ley DNA-400 + Mistake #51).
