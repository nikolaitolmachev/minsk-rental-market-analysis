"""Command-line entry point for the Realt.by rental listings collector."""

import argparse
import logging
import sys

from collector.pipeline import collect_snapshot


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Collect a snapshot of Minsk long-term rental listings.")
    parser.add_argument(
        "--max-ads",
        type=int,
        default=None,
        help="Limit the number of listings for a quick test run.",
    )
    return parser.parse_args()


def main() -> int:
    """Run the rental listings collection pipeline."""
    args = parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        listings_path, history_path = collect_snapshot(max_ads=args.max_ads)
    except Exception as exc:
        logging.error("Collection failed: %s", exc)
        return 1

    logging.info("Listings saved to: %s", listings_path)
    logging.info("Price history saved to: %s", history_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
