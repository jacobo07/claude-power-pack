# <module>/tests/e2e_reboot_cycle.py
# Highest-fidelity autonomous proof short of a physical reboot: builds sandbox
# Cursor + Claude settings, runs the REAL install-cursor-profiles.ps1 and
# wire-claude-settings.ps1, then drives the FULL reboot cycle end-to-end by
# invoking exactly what each installed Cursor slot profile would auto-run
# (powershell -File <restore.ps1 path extracted from the installer-produced
# JSON5 config>), proving every restored tab targets its exact chat through
# the installer's own wiring rather than a hand-built command line.
#
# Hermetic: a single tempfile.mkdtemp sandbox, removed at the end. NOTHING
# real is read or written (never the real ~/.claude/settings.json nor real
# Cursor settings). The module-local tests/verdicts.jsonl is the only file
# touched outside the sandbox, matching e2e_continuity.py's contract.
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

MOD = pathlib.Path(__file__).resolve().parents[1]
NODE = r"C:/Program Files/nodejs/node.exe"
REAL_RESTORE = (MOD / "restore.ps1").resolve()


def _ps(args):
    return subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", *args],
        text=True, capture_output=True,
    )


def _slot_block(json5_text, slot):
    # The installer emits JSON5 (// comments) so json.loads is invalid here on
    # purpose. Extract the slotN object literal by brace matching from its key.
    key = f'"{slot}"'
    start = json5_text.index(key)
    brace = json5_text.index("{", start)
    depth = 0
    for i in range(brace, len(json5_text)):
        ch = json5_text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json5_text[brace:i + 1]
    raise AssertionError(f"unterminated {slot} object in installer output")


def main():
    sb = pathlib.Path(tempfile.mkdtemp(prefix="lzreboot-"))
    try:
        # 1. Sandbox settings. cursor_settings.json is real JSON5: a // comment
        #    plus one genuine setting, exactly the shape Cursor ships.
        cursor_settings = sb / "cursor_settings.json"
        cursor_settings.write_text(
            "{\n"
            '  // user comment that the JSON5-safe installer MUST preserve\n'
            '  "editor.fontSize": 14\n'
            "}\n",
            encoding="utf8",
        )
        claude_settings = sb / "claude_settings.json"
        claude_settings.write_text(
            json.dumps({"hooks": {"SessionStart": [], "PreToolUse": []}}),
            encoding="utf8",
        )

        # 2. Run the REAL installers against the sandbox files.
        r1 = _ps([str(MOD / "install-cursor-profiles.ps1"),
                  "-SettingsPath", str(cursor_settings), "-NumSlots", "3"])
        assert r1.returncode == 0, (
            f"install-cursor-profiles.ps1 failed rc={r1.returncode}: "
            f"{r1.stderr.strip()}")
        r2 = _ps([str(MOD / "wire-claude-settings.ps1"),
                  "-SettingsPath", str(claude_settings)])
        assert r2.returncode == 0, (
            f"wire-claude-settings.ps1 failed rc={r2.returncode}: "
            f"{r2.stderr.strip()}")

        # 3. Assert the installer-produced cursor_settings.json. Both real
        #    installers persist via `Set-Content -Encoding UTF8`, which on
        #    Windows PowerShell 5.1 prepends a UTF-8 BOM. That BOM is exactly
        #    the byte stream Cursor (and below, Claude Code's hook loader)
        #    actually ingests, so we decode it the same forgiving way they do:
        #    "utf-8-sig" strips a leading BOM if present, no-ops if absent.
        #    This mirrors real ingestion bytes; it does not weaken any assert.
        cur = cursor_settings.read_text(encoding="utf-8-sig")
        assert "// user comment that the JSON5-safe installer MUST preserve" in cur, \
            "installer destroyed the JSON5 // comment"
        assert '"editor.fontSize": 14' in cur, "installer dropped the real setting"
        assert '"terminal.integrated.restoreTerminals": true' in cur, \
            "restoreTerminals not written by installer"

        installer_restore_path = None
        installer_slot2_env = None
        for n in (1, 2, 3):
            slot = f"slot{n}"
            block = _slot_block(cur, slot)
            assert '"LAZARUS_TERMINAL_KEY"' in block and f'"{slot}"' in block, \
                f"{slot} missing LAZARUS_TERMINAL_KEY env: {block}"
            # args is ["-NoExit","-ExecutionPolicy","Bypass","-File","<restore>"]
            args = re.search(r'"args"\s*:\s*\[(.*?)\]', block, re.S).group(1)
            tokens = re.findall(r'"((?:[^"\\]|\\.)*)"', args)
            assert "-File" in tokens, f"{slot} args has no -File: {tokens}"
            restore_arg = tokens[tokens.index("-File") + 1].replace("\\\\", "\\")
            assert restore_arg.lower().endswith("restore.ps1"), \
                f"{slot} -File does not point at restore.ps1: {restore_arg}"
            assert pathlib.Path(restore_arg).resolve() == REAL_RESTORE, \
                f"{slot} -File is not the real restore.ps1: {restore_arg}"
            if n == 2:
                # The literal command line + env Cursor will execute for tab 2.
                installer_restore_path = restore_arg
                env_blk = re.search(r'"env"\s*:\s*\{(.*?)\}', block, re.S).group(1)
                installer_slot2_env = re.search(
                    r'"LAZARUS_TERMINAL_KEY"\s*:\s*"([^"]+)"', env_blk).group(1)
        assert installer_slot2_env == "slot2", \
            f"slot2 env key wrong: {installer_slot2_env}"
        assert installer_restore_path, "could not extract slot2 -File arg"

        # 4. Assert the installer-produced claude_settings.json (valid JSON,
        #    exactly one recorder.js SessionStart + one governance-guard.js
        #    PreToolUse hook).
        cj = json.loads(claude_settings.read_text(encoding="utf-8-sig"))

        def _cmds(arr):
            out = []
            for entry in arr or []:
                for h in entry.get("hooks", []) or []:
                    out.append(h.get("command", ""))
            return out

        ss = _cmds(cj["hooks"]["SessionStart"])
        pt = _cmds(cj["hooks"]["PreToolUse"])
        assert sum("recorder.js" in c for c in ss) == 1, \
            f"expected exactly 1 recorder.js SessionStart hook: {ss}"
        assert sum("governance-guard.js" in c for c in pt) == 1, \
            f"expected exactly 1 governance-guard.js PreToolUse hook: {pt}"

        # 5. Sandbox chats + REAL recorder.js x3 (one per slot).
        reg_root = sb / "reg"
        proj = sb / "proj"
        proj.mkdir()
        slot_sid = {"slot1": "AAA", "slot2": "BBB", "slot3": "CCC"}
        for n, sid in enumerate(["AAA", "BBB", "CCC"], 1):
            (proj / f"{sid}.jsonl").write_text(
                json.dumps({"type": "summary", "summary": f"chat {sid}"}) + "\n",
                encoding="utf8")
            rec = subprocess.run(
                [NODE, str(MOD / "recorder.js")],
                input=json.dumps({"session_id": sid, "cwd": str(proj)}),
                env={**os.environ,
                     "LAZARUS_REG_ROOT": str(reg_root),
                     "LAZARUS_TERMINAL_KEY": f"slot{n}"},
                text=True, capture_output=True)
            assert rec.returncode == 0, f"recorder slot{n} rc={rec.returncode}: {rec.stderr}"
        rows = json.loads(
            (reg_root / "terminal_registry.json").read_text(encoding="utf8"))["rows"]
        assert {r["slot"]: r["session_id"] for r in rows} == \
            {"slot1": "AAA", "slot2": "BBB", "slot3": "CCC"}, rows

        # 6. SIMULATE THE REBOOT: every in-memory variable about the registry
        #    is discarded; the only surviving state is the on-disk sandbox reg.
        #    For each slot invoke EXACTLY what the installed Cursor profile
        #    runs: powershell -ExecutionPolicy Bypass -File <restore.ps1 path
        #    pulled out of the installer-produced JSON5> with the slot's
        #    LAZARUS_TERMINAL_KEY env (restore.ps1's -Slot defaults to that
        #    env var) plus -RegRoot/-DryRun, and assert the revived command
        #    targets that slot's exact chat.
        del rows
        for n in (1, 2, 3):
            slot = f"slot{n}"
            # slot2's path is the literal captured in step 3; the others are
            # re-extracted from the same installer-produced JSON5 the same way.
            restore_path = (installer_restore_path if n == 2
                            else _installed_restore_path(cur, slot))
            rb = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File",
                 restore_path, "-RegRoot", str(reg_root), "-DryRun"],
                env={**os.environ, "LAZARUS_TERMINAL_KEY": slot},
                text=True, capture_output=True)
            assert rb.returncode == 0, f"{slot} restore rc={rb.returncode}: {rb.stderr}"
            expected = f"claude --resume {slot_sid[slot]}"
            assert expected in rb.stdout, \
                f"{slot} revived wrong target (want '{expected}'): {rb.stdout!r}"

        # 7. REAL mark.js on the 3 sids; filename set unchanged, no shadow,
        #    each summary now carries the yellow PRE-REBOOT marker.
        before = sorted(p.name for p in proj.glob("*"))
        mk = subprocess.run(
            [NODE, "-e",
             f"require(String.raw`{MOD/'mark.js'}`)"
             f".mark(String.raw`{proj}`,['AAA','BBB','CCC'],new Date())"],
            text=True, capture_output=True)
        assert mk.returncode == 0, f"mark.js rc={mk.returncode}: {mk.stderr}"
        after = sorted(p.name for p in proj.glob("*"))
        assert before == after, f"files renamed by mark.js: {before} -> {after}"
        assert not list(proj.glob("*.jsonl.live")), \
            "shadow .jsonl.live created - INVARIANT VIOLATION"
        for sid in ("AAA", "BBB", "CCC"):
            line = (proj / f"{sid}.jsonl").read_text(
                encoding="utf8").splitlines()[0]
            summ = json.loads(line)["summary"]
            assert summ.startswith("\U0001f7e1 [PRE-REBOOT"), \
                f"{sid} missing yellow PRE-REBOOT marker: {summ!r}"

        # 8. Success.
        print("e2e_reboot_cycle OK")
        v = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "audit": "lazarus-v4-reboot-cycle",
            "grade": "A",
            "invariants": [
                "installer preserves JSON5 comment + real setting",
                "3 slot profiles, each -File -> real restore.ps1 + slotN env",
                "claude_settings: exactly 1 recorder + 1 governance-guard hook",
                "reboot via installer-produced restore path resumes exact sid",
                "mark.js: 0 jsonl renamed, no shadow, yellow PRE-REBOOT marker",
            ],
        }
        with (MOD / "tests" / "verdicts.jsonl").open("a", encoding="utf8") as fh:
            fh.write(json.dumps(v) + "\n")
        return 0
    finally:
        shutil.rmtree(sb, ignore_errors=True)


def _installed_restore_path(cur, slot):
    # Re-extract a slot's -File restore path from the installer-produced JSON5
    # so every reboot tab uses the INSTALLER'S wiring, not a hand-built path.
    block = _slot_block(cur, slot)
    args = re.search(r'"args"\s*:\s*\[(.*?)\]', block, re.S).group(1)
    toks = re.findall(r'"((?:[^"\\]|\\.)*)"', args)
    return toks[toks.index("-File") + 1].replace("\\\\", "\\")


if __name__ == "__main__":
    sys.exit(main())
