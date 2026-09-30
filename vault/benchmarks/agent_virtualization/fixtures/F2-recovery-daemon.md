# Plan: session recovery daemon (Windows host)

Context: a Node.js daemon restores developer sessions after a crash. The host
runs Node 18.19. Several unrelated Node tools (editors, dev servers) run on the
same machine. Audit this plan. It is self-contained: do not explore any repository.

Step 1. Liveness: the daemon writes its PID to `daemon.pid`; a second launch
treats the daemon as alive if a process with that PID exists.

Step 2. Single instance: on start, check whether `daemon.lock` exists; if it
does not, create it and continue.

Step 3. State: after every change the daemon overwrites `state.json` in place
with `fs.writeFileSync`; after a crash it restores from that file.

Step 4. Cleanup: on start, kill every `node.exe` process that is not the daemon
itself, to remove orphans from the previous crash.

Step 5. Health: the status command reports HEALTHY whenever the daemon process
is running.

Step 6. A prompt hook asks the daemon for state before every prompt; if the
daemon is unreachable the hook exits with code 2, which blocks the prompt.

Step 7. Verification: unit tests against a fake process table.

Step 8. Session discovery uses `fs.globSync` to find transcript files.
