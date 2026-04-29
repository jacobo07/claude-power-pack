#!/usr/bin/env python3
"""Merge local settings.json hooks into VPS settings.json (path-translated).

Preserves VPS-specific fields (permissions, enabledPlugins, auth tokens),
imports local hooks block with paths translated Windows -> Linux. Output:
prints merged JSON to stdout for piping over ssh.
"""
import json
import sys

LOCAL = r"C:\Users\kobig\.claude\settings.json"

with open(LOCAL, encoding="utf-8-sig") as f:
    local = json.load(f)


def translate(s):
    if not isinstance(s, str):
        return s
    return (
        s.replace("C:/Users/kobig/.claude", "/home/kobicraft/.claude")
        .replace(r"C:\Users\kobig\.claude", "/home/kobicraft/.claude")
        .replace("C:/Users/kobig", "/home/kobicraft")
        .replace(r"C:\Users\kobig", "/home/kobicraft")
    )


new_hooks = {}
for event, entries in local.get("hooks", {}).items():
    new_entries = []
    for ent in entries:
        new_ent = dict(ent)
        new_ent_hooks = []
        for hk in ent.get("hooks", []):
            new_hk = dict(hk)
            if "command" in new_hk:
                new_hk["command"] = translate(new_hk["command"])
            new_ent_hooks.append(new_hk)
        new_ent["hooks"] = new_ent_hooks
        new_entries.append(new_ent)
    new_hooks[event] = new_entries

# Preserve known VPS-base fields. Add hooks block from translated local.
vps_base = {
    "permissions": {"allow": ["*"], "defaultMode": "bypassPermissions"},
    "enabledPlugins": {
        "superpowers@claude-plugins-official": True,
        "github@claude-plugins-official": True,
        "code-review@claude-plugins-official": True,
        "claude-md-management@claude-plugins-official": True,
        "agent-sdk-dev@claude-plugins-official": True,
        "feature-dev@claude-plugins-official": True,
    },
    "autoUpdatesChannel": "latest",
    "skipDangerousModePermissionPrompt": True,
    "hooks": new_hooks,
}

if "statusLine" in local:
    sl = json.loads(json.dumps(local["statusLine"]))
    if isinstance(sl, dict) and "command" in sl:
        sl["command"] = translate(sl["command"])
    vps_base["statusLine"] = sl

print(json.dumps(vps_base, indent=2))
