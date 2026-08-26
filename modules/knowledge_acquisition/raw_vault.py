"""Content-addressed, write-once store for raw prompts and raw responses.

WHY THIS EXISTS
---------------
`deep_research` fetches raw HTML, derives markdown, and persists neither --
only the final synthesis. For a repeatable web search that is merely wasteful.
For a 30-70 hour acquisition against a paid account that will not answer the
same question the same way twice, it is unrecoverable data loss: once the
derived artifact is found to be wrong, there is nothing to re-derive from.

Guarantees:
  * Write-once. An existing digest is never rewritten. A second put() of the
    same bytes is a no-op that returns the same path.
  * Atomic. Content lands via tmp + os.replace, so a crash mid-write leaves
    either the whole artifact or nothing -- never a truncated one that hashes
    to a digest it does not match.
  * Self-describing. Each artifact carries a sidecar recording what produced
    it. If the registry database is lost, the vault alone still reconstructs
    which prompt produced which response, and under which extractor version.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import EXTRACTOR_VERSION, content_hash, utc_now


class RawVaultError(Exception):
    """Raised on a genuine integrity failure. Never swallowed."""


@dataclass(frozen=True)
class RawArtifact:
    digest: str
    kind: str  # "prompt" | "response"
    path: Path
    created_at: str
    already_present: bool


class RawVault:
    """Immutable artifact store rooted at a single directory."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # -- addressing ---------------------------------------------------------

    def path_for(self, digest: str, kind: str) -> Path:
        """Shard by the first two hex chars: 256 dirs keeps any one listing small."""
        return self.root / kind / digest[:2] / f"{digest}.md"

    def _meta_path(self, digest: str, kind: str) -> Path:
        return self.path_for(digest, kind).with_suffix(".meta.json")

    # -- writing ------------------------------------------------------------

    def put(
        self,
        raw: str,
        *,
        kind: str,
        prompt_id: str,
        source: str = "",
        source_version: str = "",
        extra: dict | None = None,
    ) -> RawArtifact:
        if kind not in ("prompt", "response"):
            raise RawVaultError(f"unknown artifact kind: {kind!r}")
        if not raw:
            raise RawVaultError("refusing to store an empty artifact")

        digest = content_hash(raw)
        target = self.path_for(digest, kind)

        if target.exists():
            # Write-once: verify what is on disk still hashes to its own name.
            # A mismatch means the vault was tampered with or corrupted, which
            # must be loud -- silently trusting it would poison every
            # derivation downstream.
            existing = target.read_text(encoding="utf-8")
            if content_hash(existing) != digest:
                raise RawVaultError(
                    f"vault corruption: {target} does not hash to its own name"
                )
            return RawArtifact(digest, kind, target, utc_now(), already_present=True)

        target.parent.mkdir(parents=True, exist_ok=True)
        created = utc_now()

        self._atomic_write(target, raw)
        self._atomic_write(
            self._meta_path(digest, kind),
            json.dumps(
                {
                    "digest": digest,
                    "kind": kind,
                    "prompt_id": prompt_id,
                    "source": source,
                    "source_version": source_version,
                    "extractor_version": EXTRACTOR_VERSION,
                    "created_at": created,
                    "char_count": len(raw),
                    **(extra or {}),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        return RawArtifact(digest, kind, target, created, already_present=False)

    @staticmethod
    def _atomic_write(target: Path, text: str) -> None:
        """tmp + fsync + replace. A crash leaves the old state, never a half file."""
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    # -- reading ------------------------------------------------------------

    def get(self, digest: str, kind: str) -> str:
        target = self.path_for(digest, kind)
        if not target.exists():
            raise RawVaultError(f"artifact not in vault: {kind}/{digest}")
        raw = target.read_text(encoding="utf-8")
        if content_hash(raw) != digest:
            raise RawVaultError(f"vault corruption on read: {target}")
        return raw

    def meta(self, digest: str, kind: str) -> dict:
        p = self._meta_path(digest, kind)
        if not p.exists():
            raise RawVaultError(f"sidecar missing for {kind}/{digest}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- integrity ----------------------------------------------------------

    def verify_all(self) -> tuple[int, list[str]]:
        """Re-hash every artifact. Returns (checked, list of corrupt digests)."""
        checked, corrupt = 0, []
        for kind in ("prompt", "response"):
            base = self.root / kind
            if not base.exists():
                continue
            for f in base.rglob("*.md"):
                checked += 1
                if content_hash(f.read_text(encoding="utf-8")) != f.stem:
                    corrupt.append(f"{kind}/{f.stem}")
        return checked, corrupt

    def stats(self) -> dict:
        out = {}
        for kind in ("prompt", "response"):
            base = self.root / kind
            files = list(base.rglob("*.md")) if base.exists() else []
            out[kind] = {
                "count": len(files),
                "bytes": sum(f.stat().st_size for f in files),
            }
        return out


__all__ = ["RawVault", "RawArtifact", "RawVaultError", "asdict"]
