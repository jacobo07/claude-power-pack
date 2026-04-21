#!/usr/bin/env python3
"""
scaffold_fastapi.py — FastAPI Sovereign Scaffolder (MC-OVO-32-F)

Generates a minimal FastAPI project with real wiring (no placeholders),
security middleware, a health endpoint, a typed Pydantic route, and a
pytest test that verifies the endpoints. Then runs a BOOT GATE:
  1. pip install --user fastapi uvicorn pytest httpx
  2. pytest tests/ (must pass)
  3. uvicorn app.main:app (background) -> curl /health -> HTTP 200
  4. kill uvicorn

Usage:
    python tools/scaffold_fastapi.py --out /tmp/my-api --name my-api
    python tools/scaffold_fastapi.py --out ./demo-api --name demo-api --no-boot-test

Exit codes:
    0 — all gates pass
    1 — scaffold succeeded but boot-test failed
    2 — dependency install failed
    3 — bad args
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

APP_MAIN = """\
\"\"\"FastAPI app entry. Security middleware + typed routes.\"\"\"
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from .config import Settings

settings = Settings()
app = FastAPI(title=settings.project_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

bearer = HTTPBearer(auto_error=False)


def require_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if creds is None or creds.credentials != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid bearer token",
        )
    return creds.credentials


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    project: str


class EchoRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=280)


class EchoResponse(BaseModel):
    echoed: str
    length: int


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", project=settings.project_name)


@app.post("/echo", response_model=EchoResponse)
def echo(req: EchoRequest, _: str = Depends(require_token)) -> EchoResponse:
    return EchoResponse(echoed=req.message, length=len(req.message))
"""

APP_CONFIG = """\
\"\"\"Typed settings via Pydantic. Reads from env or .env.\"\"\"
from __future__ import annotations

import os
from pydantic import BaseModel, Field


class Settings(BaseModel):
    project_name: str = Field(default_factory=lambda: os.getenv("PROJECT_NAME", "scaffolded-api"))
    api_token: str = Field(default_factory=lambda: os.getenv("API_TOKEN", "dev-token-change-me"))
    cors_origins: list[str] = Field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    )
"""

APP_INIT = '"""Package marker for the FastAPI app."""\n'

TESTS_MAIN = """\
\"\"\"Pytest suite for the scaffolded API. Tests run against a TestClient, no network.\"\"\"
from __future__ import annotations

import os

os.environ.setdefault("API_TOKEN", "test-token")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "project" in body


def test_echo_requires_auth():
    resp = client.post("/echo", json={"message": "hello"})
    assert resp.status_code == 401


def test_echo_happy_path():
    resp = client.post(
        "/echo",
        json={"message": "hello world"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["echoed"] == "hello world"
    assert body["length"] == 11


def test_echo_rejects_long_input():
    long_msg = "x" * 500
    resp = client.post(
        "/echo",
        json={"message": long_msg},
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 422
"""

REQUIREMENTS = "fastapi>=0.115.0\nuvicorn[standard]>=0.30.0\npydantic>=2.6.0\nhttpx>=0.27.0\npytest>=8.0.0\n"

README = """\
# {name}

Scaffolded by Claude Power Pack `scaffold_fastapi` (MC-OVO-32-F). Zero placeholders.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest tests/
```

## Auth

Set `API_TOKEN` env var; `/echo` requires `Authorization: Bearer <token>`.

## Security baseline

- CORS middleware with explicit origin allowlist (not `*`)
- Bearer auth on mutating endpoints (`/echo`)
- Pydantic strict typing on every request/response
- No `SELECT *`-equivalents (typed responses only)
"""

GITIGNORE = "__pycache__/\n*.pyc\n.venv/\n.env\n.pytest_cache/\n"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def scaffold(out: Path, name: str) -> None:
    write_file(out / "app" / "__init__.py", APP_INIT)
    write_file(out / "app" / "main.py", APP_MAIN)
    write_file(out / "app" / "config.py", APP_CONFIG)
    write_file(out / "tests" / "__init__.py", "")
    write_file(out / "tests" / "test_main.py", TESTS_MAIN)
    write_file(out / "requirements.txt", REQUIREMENTS)
    write_file(out / "README.md", README.format(name=name))
    write_file(out / ".gitignore", GITIGNORE)


def run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env or os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def gate_install(out: Path) -> bool:
    """Gate 1: pip install deps."""
    print("[gate-install] pip install --user -r requirements.txt")
    result = run(
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", "-r", "requirements.txt"],
        cwd=out,
        timeout=180,
    )
    if result.returncode != 0:
        print(f"[gate-install] FAIL\n{result.stderr[-500:]}")
        return False
    print("[gate-install] OK")
    return True


def gate_pytest(out: Path) -> bool:
    """Gate 2: pytest passes."""
    print("[gate-pytest] pytest tests/")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(out)
    result = run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"], cwd=out, env=env, timeout=60)
    if result.returncode != 0:
        print(f"[gate-pytest] FAIL\n{result.stdout[-1500:]}\n{result.stderr[-500:]}")
        return False
    # Count passes from output
    passes = result.stdout.count(" PASSED")
    print(f"[gate-pytest] OK — {passes} tests passed")
    return True


def gate_boot(out: Path) -> bool:
    """Gate 3: uvicorn boots and /health returns 200."""
    print("[gate-boot] uvicorn app.main:app --port 8799 (background)")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(out)
    env["API_TOKEN"] = "boot-test-token"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8799", "--host", "127.0.0.1"],
        cwd=str(out),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # Wait for startup
        time.sleep(3)
        import urllib.request
        try:
            with urllib.request.urlopen("http://127.0.0.1:8799/health", timeout=5) as resp:
                body = resp.read().decode()
                status = resp.status
        except Exception as err:
            print(f"[gate-boot] FAIL — GET /health: {err}")
            return False
        if status != 200 or '"status":"ok"' not in body:
            print(f"[gate-boot] FAIL — status={status} body={body}")
            return False
        print(f"[gate-boot] OK - GET /health -> 200 {body}")
        return True
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--out", type=Path, required=True, help="output directory (will be created)")
    ap.add_argument("--name", type=str, default="scaffolded-api", help="project name for README + settings")
    ap.add_argument("--no-boot-test", action="store_true", help="skip the uvicorn boot gate (gate 3)")
    ap.add_argument("--no-install", action="store_true", help="skip pip install + pytest (gates 1+2 — for dry-run)")
    args = ap.parse_args()

    if args.out.exists() and any(args.out.iterdir()):
        print(f"ERROR: {args.out} exists and is non-empty", file=sys.stderr)
        return 3

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"[scaffold] writing to {args.out}")
    scaffold(args.out, args.name)
    files = sorted(p.relative_to(args.out) for p in args.out.rglob("*") if p.is_file())
    print(f"[scaffold] wrote {len(files)} files:")
    for f in files:
        print(f"  - {f}")

    if args.no_install:
        print("[scaffold] --no-install -> skipping gates 1-3")
        return 0

    if not gate_install(args.out):
        return 2
    if not gate_pytest(args.out):
        return 1
    if args.no_boot_test:
        print("[scaffold] --no-boot-test -> skipping gate 3")
        return 0
    if not gate_boot(args.out):
        return 1

    print("[scaffold] ALL GATES PASS — FastAPI scaffold verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
