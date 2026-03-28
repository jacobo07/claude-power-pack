# Overlay: Python

- **Framework:** FastAPI preferred. Use Pydantic v2 models for all request/response schemas.
- **Async:** Use `async def` for I/O-bound endpoints. Never mix sync blocking calls in async handlers.
- **Types:** Run `mypy --strict` or `pyright`. No `Any` unless explicitly justified.
- **Testing:** pytest + pytest-asyncio. Fixtures over mocks. Coverage target: 80%+.
- **Migrations:** Alembic for DB schema changes. Always generate migration, never raw DDL.
- **Dependencies:** Pin versions in requirements.txt or pyproject.toml. Use venv, never global install.
- **Error Handling:** Raise HTTPException with correct status codes. Never return 200 on error.
- **Config:** Pydantic Settings with .env loading. No os.getenv scattered in code.
- **Formatting:** Black + isort + ruff. Run before commit.
- **Security:** Use secrets module for tokens. Parameterized queries only. No f-string SQL.
