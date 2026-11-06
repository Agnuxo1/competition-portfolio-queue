# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT
# Research-Project: Competition Portfolio Queue
# Research-Author: Francisco Angulo de Lafuente
# Research-ORCID: https://orcid.org/0009-0001-1634-7063
# Research-Date: 2026-11-06
"""Write or check provenance/SHA256SUMS for every tracked source file."""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "provenance" / "SHA256SUMS"
SKIP = {"provenance/SHA256SUMS"}


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return sorted(p for p in out.splitlines() if p not in SKIP)


def digest(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    lines = "".join(f"{digest(p)}  {p}\n" for p in tracked())
    if args.check:
        if MANIFEST.read_text(encoding="utf-8") != lines:
            print("provenance/SHA256SUMS is out of date", file=sys.stderr)
            return 1
        print("manifest ok")
        return 0
    MANIFEST.write_text(lines, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
