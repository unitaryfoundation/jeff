"""Command line interface for the jeff verifier."""

from __future__ import annotations

import argparse
from pathlib import Path

from .verifier import verify_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify encoded jeff modules.")
    parser.add_argument("paths", nargs="+", type=Path, help="jeff files to verify")
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        errors = verify_file(path)
        if errors:
            failed = True
            print(f"{path}: invalid")
            for error in errors:
                print(f"  {error.path}: {error.message}")
        else:
            print(f"{path}: ok")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
