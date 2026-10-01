# Plan: stabilise the thermostat firmware release

Context: embedded C firmware for a thermostat. Each hardware test needs a physical
board flashed (about 25 minutes per flash; two boards exist). A Python harness on the
host drives the boards; agents help triage harness output.
Audit this plan. It is self-contained: do not explore any repository.

Step 1. Classify this release as ULTRA-PLAN and run the full 7-phase protocol before
fixing the one-character typo in the boot banner string.

Step 2. Debug the intermittent sensor dropout by flashing one candidate fix per board
cycle, watching whether the dropout happens, then picking the next candidate.

Step 3. Refactor the `sensor_bus` module into three files. It is done when the existing
unit tests still pass.

Step 4. Add a `telemetry_daemon` on the host that logs every harness call to a SQLite
file. No dashboard or reader for it is planned yet.

Step 5. Security negative test: assert that the `factory_reset` debug command is
rejected without the service token. The test passes because the harness receives a
404 (the command is not compiled into this build).

Step 6. Every triage agent run receives the full firmware repository (all 4,000 files)
in its prompt, so that it "has everything".
