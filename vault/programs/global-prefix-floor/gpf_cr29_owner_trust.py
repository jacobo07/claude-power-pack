"""OWNER-RUN ONLY (HR-001). Trusts the single fixed CR-29 probe root so gpf_cr29_kclear.py can run past the trust dialog.

The agent may not write hasTrustDialogAccepted (the auto-mode classifier denied it as self-modification, 2026-11-02); this
script is the documented Owner-side half. It touches exactly one key: projects["<TEMP>/gpf-cr29-probe"].hasTrustDialogAccepted.
Backup first, merge (never replace: live Claude sessions write this file too), temp file + os.replace, read back.

usage (Owner, in the Claude prompt):  ! python vault/programs/global-prefix-floor/gpf_cr29_owner_trust.py
revert: delete that one project key, or copy the printed backup over ~/.claude.json.
"""
import json, os, sys, time
from pathlib import Path

root = Path(os.environ["TEMP"]) / "gpf-cr29-probe"
root.mkdir(exist_ok=True)
(root / ".gpf-cr29-probe").write_text("marker: owned by gpf_cr29_kclear.py; contents are reset every run\n", encoding="utf-8")
cfg = Path.home() / ".claude.json"
key = str(root).replace("\\", "/")
bak = cfg.with_name(f".claude.json.gpf-cr29-{time.strftime('%Y%m%dT%H%M%S')}.bak")
bak.write_bytes(cfg.read_bytes())
for attempt in range(1, 4):
    d = json.loads(cfg.read_text(encoding="utf-8"))
    d.setdefault("projects", {}).setdefault(key, {})["hasTrustDialogAccepted"] = True
    tmp = cfg.with_name(f".claude.json.gpf-cr29.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
    os.replace(tmp, cfg)
    time.sleep(2)
    if json.loads(cfg.read_text(encoding="utf-8")).get("projects", {}).get(key, {}).get("hasTrustDialogAccepted") is True:
        print(f"TRUSTED {key} (attempt {attempt}); backup {bak}")
        sys.exit(0)
print(f"NOT VERIFIED after 3 attempts (a live session rewrote the file); backup {bak}")
sys.exit(1)
