"""Send each prompts/GNN.txt to Codex (web search on) and land its JSONL in raw/gap-GNN.jsonl.

Sequential on purpose: one ChatGPT-account quota, and a quota error must stop the run,
not be recorded as an empty answer. A gap is skipped when codex-out/GNN.md already exists.

Usage: python run_codex.py [G08 G09 ...]      (default: every prompt without an answer)
Env:   CODEX_MODEL (default gpt-6-astra), CODEX_EFFORT (default high), CODEX_TIMEOUT_S (default 1800)
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODEX = r"C:\Users\User\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"
MODEL = os.environ.get("CODEX_MODEL", "gpt-6-astra")
EFFORT = os.environ.get("CODEX_EFFORT", "high")
TIMEOUT = int(os.environ.get("CODEX_TIMEOUT_S", "1800"))
QUOTA = re.compile(r"rate.?limit|quota|usage limit|429|model_not_found|unauthorized|401", re.I)
JSONL_BLOCK = re.compile(r"```jsonl\s*\n(.*?)```", re.S)


def extract(gid: str, md: str) -> tuple[list[dict], list[str]]:
    rows, bad = [], []
    blocks = JSONL_BLOCK.findall(md)
    for line in "\n".join(blocks).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            bad.append(line[:80])
            continue
        row["gap"] = gid
        row["grade_scale"] = "doc"
        rows.append(row)
    return rows, bad


def run_one(gid: str) -> str:
    prompt = HERE / "prompts" / f"{gid}.txt"
    out_md = HERE / "codex-out" / f"{gid}.md"
    log = HERE / "codex-out" / f"{gid}.log"
    cmd = [CODEX, "--search", "exec", "-m", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"',
           "--skip-git-repo-check", "-s", "read-only", "-C", str(HERE), "-o", str(out_md), "-"]
    with prompt.open("rb") as fin, log.open("wb") as flog:
        try:
            rc = subprocess.run(cmd, stdin=fin, stdout=flog, stderr=subprocess.STDOUT, timeout=TIMEOUT).returncode
        except subprocess.TimeoutExpired:
            return f"{gid}: TIMEOUT after {TIMEOUT}s"
    log_text = log.read_text(encoding="utf-8", errors="replace")
    if rc != 0 or not out_md.exists():
        if QUOTA.search(log_text):
            raise SystemExit(f"{gid}: PROVIDER STOP rc={rc} (quota/auth/model) - see {log.name}; nothing recorded")
        return f"{gid}: FAILED rc={rc}, no answer - see {log.name}"
    md = out_md.read_text(encoding="utf-8", errors="replace")
    rows, bad = extract(gid, md)
    if not rows:
        return f"{gid}: answer has no parseable jsonl block ({len(bad)} bad lines) - kept {out_md.name}, raw not written"
    (HERE / "raw" / f"gap-{gid}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return f"{gid}: OK {len(rows)} rows, {len(bad)} unparsable lines"


def main() -> int:
    (HERE / "codex-out").mkdir(exist_ok=True)
    wanted = sys.argv[1:] or sorted(p.stem for p in (HERE / "prompts").glob("G*.txt"))
    todo = [g for g in wanted if not (HERE / "codex-out" / f"{g}.md").exists()]
    print(f"model={MODEL} effort={EFFORT} todo={todo}", flush=True)
    for gid in todo:
        print(run_one(gid), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
