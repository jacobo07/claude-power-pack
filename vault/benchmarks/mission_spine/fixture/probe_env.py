#!/usr/bin/env python3
"""Report live facts about the ingest environment.

Real and runnable. It reads; it never writes, uploads or deletes. Run it with
no arguments to describe the default incoming folder, or pass a path to
describe another one -- on a developer machine `D:\\incoming` will not exist,
and saying so is the correct output rather than an error.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

DEFAULT_INCOMING = Path(r"D:\incoming")


def describe(folder: Path) -> int:
    print(f"incoming : {folder}")
    if not folder.is_dir():
        print("  status : ABSENT on this host -- nothing to report about it")
    else:
        now = time.time()
        files = sorted(p for p in folder.iterdir() if p.is_file())
        print(f"  status : present, {len(files)} file(s)")
        for p in files[:20]:
            try:
                st = p.stat()
            except OSError as exc:
                print(f"    {p.name}: unreadable ({exc.__class__.__name__})")
                continue
            print(f"    {p.name}  {st.st_size / 1_048_576:,.1f} MB  "
                  f"last written {now - st.st_mtime:,.0f}s ago")

    anchor = folder if folder.is_dir() else Path(folder.anchor or Path.cwd())
    try:
        usage = shutil.disk_usage(anchor)
    except OSError as exc:
        print(f"  volume : unreadable ({exc.__class__.__name__})")
        return 0
    gb = 1_073_741_824
    print(f"  volume : {anchor}  {usage.free / gb:,.1f} GB free of "
          f"{usage.total / gb:,.1f} GB ({100 * usage.free / usage.total:.0f}% free)")
    return 0


def main(argv: list[str]) -> int:
    return describe(Path(argv[1]) if len(argv) > 1 else DEFAULT_INCOMING)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
