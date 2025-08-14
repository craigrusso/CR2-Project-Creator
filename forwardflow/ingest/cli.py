"""CLI entrypoint for ingest (hidden by feature flag in Phase 0)."""

from __future__ import annotations

import argparse
import sys

from .config import FF_INGEST_ENABLED


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - stub
    if not FF_INGEST_ENABLED:
        print("Ingest is currently disabled. Set FF_INGEST_ENABLED=True to enable.")
        return 2
    parser = argparse.ArgumentParser(prog="forwardflow-ingest")
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args(argv)
    print(f"Ingest would run from {args.source} to {args.destination}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


