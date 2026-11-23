"""heroes.py through the Owner's Codex CLI (ChatGPT login) instead of the OpenAI Images API. Local addition.

    python -X utf8 -I heroes_codex.py <check|render|fix|review|board> --project <folder>   (same commands as heroes.py)

heroes.py is imported unchanged; only its two network seams are replaced: `openai_key` (no key is needed) and `call`
(one `codex exec` per render, using Codex's built-in image_generation tool). Every prompt, claim, sidecar, log line,
check, review and board stays upstream's.

How a render works: `codex exec --json` names its thread in the first event (`thread.started`), and Codex saves the
image it generated as `<CODEX_HOME>/generated_images/<thread_id>/*.png`. That file is copied to the render's name.
With a reference (or for `fix`) the source image is attached with `-i`, and the model is told to edit it.

Environment:
  CHM_CODEX_MODEL     orchestrating model (default gpt-5.6-luna). The image comes from the image tool, not this model.
                      The Owner's config default (gpt-5.5) is refused for a ChatGPT login, so it is always passed.
  CHM_CODEX_PARALLEL  concurrent codex processes (default 2); heroes.py itself fans out to 12 threads.
  CHM_CODEX_CMD       JSON list overriding the codex command (tests use a fake).
  CODEX_HOME          Codex's home (default ~/.codex), where generated_images lives.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heroes as H  # noqa: E402

_DEFAULT_EXE = r"C:\Users\User\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"
CODEX = (json.loads(os.environ["CHM_CODEX_CMD"]) if os.environ.get("CHM_CODEX_CMD")
         else [shutil.which("codex") or _DEFAULT_EXE])
MODEL = os.environ.get("CHM_CODEX_MODEL", "gpt-5.6-luna")
GATE = threading.Semaphore(max(1, int(os.environ.get("CHM_CODEX_PARALLEL", "2"))))
TIMEOUT_S = 600

ASK = ("Use your built-in image generation tool to create exactly one image, landscape 3:2 (1536x1024). {mode}"
       "Do not run any shell commands and do not write any files. When the image exists, reply with the single word DONE."
       "\n\nImage prompt:\n{text}")
EDIT = ("Edit the attached image rather than starting from nothing: it is the source, and the result follows the prompt "
        "below. ")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def codex_call(project, key, text, dest, src=None, meta=None, tries=2):
    """Drop-in for heroes.call: same arguments, same sidecar, same log, same return strings."""
    # An npm `codex.cmd`/`.bat` shim runs through cmd.exe, which re-parses the argv: a `"` in the prompt flips its
    # quoting and a following `&` runs as a command (BatBadBut). Refuse it; the native codex.exe takes argv as is.
    # Pre-push review of 2f2d977f.
    # Also an explicit CHM_CODEX_CMD that goes through cmd.exe itself (["cmd", "/c", "codex.cmd"]).
    if (Path(CODEX[0]).stem.lower() == "cmd"
            or any(Path(str(a)).suffix.lower() in (".cmd", ".bat") for a in CODEX)):
        return (f"{dest.name}: FAILED codex resolves to a batch shim ({CODEX[0]}); install the native codex.exe "
                f"or set CHM_CODEX_CMD to it")
    for attempt in range(1, tries + 1):
        t0 = time.time()
        try:
            with GATE, tempfile.TemporaryDirectory() as wd:
                # The prompt goes BEFORE -i: -i takes several values and would swallow a prompt placed after it.
                cmd = [*CODEX, "exec", "-m", MODEL, "--skip-git-repo-check", "--json", "-s", "read-only", "-C", wd,
                       ASK.format(mode=EDIT if src else "", text=text)]
                if src is not None:
                    cmd += ["-i", str(src)]
                r = subprocess.run(cmd, capture_output=True, timeout=TIMEOUT_S)
            events, unparsed = [], 0
            for line in r.stdout.decode("utf-8", "replace").splitlines():
                if line.lstrip().startswith("{"):
                    try:
                        events.append(json.loads(line))
                    except ValueError:
                        unparsed += 1  # reported below if no image came back; a stray line alone is not a failure
            thread = next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None)
            folder = codex_home() / "generated_images" / thread if thread else None
            pngs = sorted(folder.glob("*.png"), key=lambda p: p.stat().st_mtime) if folder and folder.is_dir() else []
            if not pngs:
                why = [str(e.get("message") or e.get("error"))[:200] for e in events if e.get("type") in ("error", "turn.failed")]
                raise RuntimeError(f"no image from codex (exit {r.returncode}, thread {thread}, {unparsed} unparsed lines):{why or r.stderr.decode('utf-8', 'replace')[-200:]}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(pngs[-1], dest)
            side = {"provider": "codex", "model": MODEL, "seconds": round(time.time() - t0, 1), "usage": {}, "prompt": text,
                    "src": str(src) if src else None, "codex_thread": thread, "codex_image": str(pngs[-1]), **(meta or {})}
            dest.with_suffix(".json").write_text(json.dumps(side, indent=1))
            H.log(project, {"t": t0, "dest": str(dest), "seconds": side["seconds"], "provider": "codex",
                            "codex_thread": thread, **(meta or {})})
            return f"{dest.name}: ok {side['seconds']}s (codex)"
        except Exception as e:  # same contract as heroes.call: retried once, then reported; the batch keeps going
            H.log(project, {"t": t0, "dest": str(dest), "error": str(e)[:400], "attempt": attempt, "provider": "codex",
                            **(meta or {})})
            if attempt == tries:
                return f"{dest.name}: FAILED {str(e)[:200]}"


H.openai_key = lambda project: "codex-cli"
H.call = codex_call

if __name__ == "__main__":
    H.main()
