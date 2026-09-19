# ingest-agent

Small internal service. This file is the project reality a planner may inspect.
It states facts about the environment. It does not state requirements.

## What exists today

Nothing is implemented. This directory carries the environment description and
a working probe; the service itself has not been written.

## Deployment environment

- Runs unattended on one Windows box in the equipment room, started at boot,
  restarted by nobody. Nobody logs into it for weeks at a time.
- `D:\incoming` is written to by a camera controller, continuously, while
  recordings are in progress. The controller is a third-party appliance: it is
  not ours, it cannot be modified, and it emits no completion signal.
- Recordings are `.mp4`, between 200 MB and 2 GB. A long session writes for
  20-40 minutes.
- `D:` is 500 GB. At current recording volume it fills in roughly 3 days.
- Uplink is a shared 40 Mbps business line. A 2 GB file takes ~7 minutes on an
  idle link and considerably longer during the working day.
- The link drops. Measured by the site's own router logs: 3 to 12 short
  outages per week, most under 90 seconds, the longest recorded 4 hours.

## Object storage

- AWS S3, bucket `acme-site-recordings`, region `eu-west-1`.
- Credentials are on the box in the standard AWS profile.
- Bucket versioning is **off**. Lifecycle rules: none.

## Downstream

- An analytics job lists the bucket every night at 02:00 and processes
  whatever it finds. It has no state of its own; it treats every object
  present as a complete recording.

## Probe

`python probe_env.py` reports live disk and incoming-folder facts. It is real
and runnable; it is the only code in this directory.
