from __future__ import annotations

import argparse
import sys

from sidepick.config import DB_PATH, load_settings
from sidepick.db import SidePickDb
from sidepick.pipeline import run_discovery


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sidepick",
        description="Discover product candidates from official Naver Shopping APIs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover", help="Run product discovery once.")
    discover.add_argument("--top", type=int, default=20, help="Number of results to show.")

    args = parser.parse_args(argv)

    if args.command == "discover":
        settings = load_settings()
        db = SidePickDb(DB_PATH)
        run_discovery(settings, db, top=args.top)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"\nSidePick stopped: {error}", file=sys.stderr)
        raise SystemExit(1)

