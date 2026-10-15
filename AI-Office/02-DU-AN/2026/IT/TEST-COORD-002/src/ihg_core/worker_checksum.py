"""ihg_core.worker_checksum — Worker tinh SHA-256.

Day la WORKER (Python co logic xac dinh), KHONG phai AI Agent.
"""
import hashlib
import sys
from pathlib import Path
from typing import List

from .config import Config


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("usage: worker_checksum.py <file> [file...]", file=sys.stderr)
        return 2
    rc = 0
    for f in argv[1:]:
        p = Path(f)
        if not p.exists():
            print(f"MISSING: {f}", file=sys.stderr)
            rc = 1
            continue
        try:
            print(f"{sha256_file(p)}  {p}")
        except Exception as e:
            print(f"ERROR: {f} {e}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))
