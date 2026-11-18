#!/usr/bin/env python3
"""V-LDG-* -- CDIO-10 publish gate (spec vault/specs/cdio-10-publish-gate.md), both poles, through the real node hook.

Hermetic: sites and the ledger dir are temp. Run: python tools/test_legal_deploy_gate.py  (exit 0 = all pass)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "legal_deploy_gate.js"
_TMP = tempfile.mkdtemp(prefix="v-ldg-")
STATE = os.path.join(_TMP, "state")
RESULTS: list = []

FOOTER = ('<footer><a href="/privacidad">Privacidad</a> <a href="/terminos">Términos</a> '
          '<a href="/aviso-legal">Aviso legal</a></footer>')
FILLED = "<h1>{t}</h1><p>Mar Azul S.L., NIF B00000000, Calle Mayor 1, Valencia. Actualizado 2026-10-08.</p>"


def ok(name: str, cond: bool, detail="") -> None:
    RESULTS.append((name, bool(cond)))
    print("  %s %-30s %s" % ("PASS" if cond else "FAIL", name, "" if cond else str(detail)[:400]))


def site(files: dict, decl=None) -> str:
    d = tempfile.mkdtemp(dir=_TMP)
    for rel, text in files.items():
        p = os.path.join(d, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        Path(p).write_text(text, encoding="utf-8")
    if decl is not None:
        Path(d, ".cpp-legal.json").write_text(json.dumps(decl), encoding="utf-8")
    return d


def hook(command: str, cwd: str, tool: str = "Bash", **env):
    r = subprocess.run(["node", str(HOOK)], input=json.dumps({"tool_name": tool, "tool_input": {"command": command},
                                                              "cwd": cwd, "session_id": "v-ldg"}),
                       capture_output=True, text=True, encoding="utf-8", timeout=60,
                       env=dict(os.environ, CPP_LEGAL_DEPLOY_STATE_DIR=STATE, **env))
    out = json.loads(r.stdout) if r.stdout.strip() else {}
    hs = out.get("hookSpecificOutput") or {}
    return hs.get("permissionDecision") == "deny", hs.get("permissionDecisionReason", "")


def ledger_rows() -> int:
    p = Path(STATE, "ledger.jsonl")
    return len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0


def last_row() -> dict:
    p = Path(STATE, "ledger.jsonl")
    rows = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    return json.loads(rows[-1]) if rows else {}


def main() -> int:
    try:
        page_only = {"index.html": "<html><body><h1>Hola</h1></body></html>"}
        bare = site(page_only)
        n0 = ledger_rows()
        quiet = [hook(c, bare)[0] for c in ('git commit -m "ship it with vercel --prod later"', "npm test",
                                            "vercel dev", "npx vercel", "firebase deploy --only functions",
                                            "cat > run.sh <<'EOF'\nvercel --prod\nEOF")]
        ok("V-LDG-SILENT-NON-DEPLOY", not any(quiet) and ledger_rows() == n0, quiet)
        d, why = hook("npx vercel --prod", bare)
        ok("V-LDG-DENY-UNDECLARED", d and ".cpp-legal.json" in why and ledger_rows() == n0 + 1, why)
        es = site(page_only, {"jurisdiction": "es"})
        d, why = hook("vercel deploy --prod", es)
        ok("V-LDG-DENY-MISSING-PAGES", d and "legal-page-present" in why and "privacy" in why and "legal_notice" in why,
           why)
        full = site({"app/layout.tsx": FOOTER, "app/page.tsx": "<h1>Inicio</h1>",
                     "app/privacidad/page.tsx": FILLED.format(t="Política de privacidad"),
                     "app/terminos/page.tsx": FILLED.format(t="Términos de uso"),
                     "app/aviso-legal/page.tsx": FILLED.format(t="Aviso legal")}, {"jurisdiction": "es"})
        d, why = hook("netlify deploy --dir out --prod", full)
        # an allow must be a judged allow, not the fail-open path: read the ledger row it left
        last = last_row()
        ok("V-LDG-ALLOW-COMPLETE", not d and last.get("decision") == "allow" and "privacy" in last.get("pages", {}),
           [why, last])
        ex = site(page_only, {"exempt": "internal QA mirror behind basic auth, never indexed"})
        d = hook("wrangler pages deploy dist", ex)[0]
        ok("V-LDG-ALLOW-EXEMPT", not d and last_row().get("why") == "exempt", last_row())
        short = site(page_only, {"exempt": "demo"})
        d, why = hook("surge ./dist", short)
        ok("V-LDG-REFUSE-SHORT-EXEMPT", d and "real reason" in why, why)
        d, _ = hook("Set-Location x; npx vercel --prod", bare, tool="PowerShell")
        ok("V-LDG-POWERSHELL", d)
        parent = tempfile.mkdtemp(dir=_TMP)
        os.makedirs(os.path.join(parent, "web"))
        Path(parent, "web", ".cpp-legal.json").write_text(json.dumps({"jurisdiction": "es"}), encoding="utf-8")
        Path(parent, "web", "index.html").write_text("<h1>x</h1>", encoding="utf-8")
        d, why = hook("vercel --cwd web --prod", parent)
        ok("V-LDG-CWD-ARG", d and "legal-page-present" in why, why)
        ok("V-LDG-KILL", not hook("vercel --prod", bare, CPP_LEGAL_DEPLOY_GATE="off")[0])
        ok("V-LDG-FIREBASE-HOSTING", hook("firebase deploy --only hosting", bare)[0])
        disp = (ROOT / "hooks" / "hook-dispatcher.js").read_text(encoding="utf-8")
        i = disp.find("'PreToolUse-Bash-chain': [")
        chain = disp[i:disp.find("\n  ],", i)] if i >= 0 else ""
        ok("V-LDG-WIRED", "hooks/legal_deploy_gate.js" in chain)
    except Exception as exc:  # noqa: BLE001 -- a crash is a FAIL
        ok("V-LDG-CRASH", False, "%s: %s" % (type(exc).__name__, exc))
    finally:
        shutil.rmtree(_TMP, ignore_errors=True)
    passed = sum(1 for _, c in RESULTS if c)
    print("V-LDG: %d passed, %d failed" % (passed, len(RESULTS) - passed))
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
