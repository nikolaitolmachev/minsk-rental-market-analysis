"""Orchestrate collection, enrichment, caching, and CSV output."""

import csv
import datetime as dt
import json
import logging
import time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from collector.client import RealtClient
from collector.config import (
    CARD_REQUEST_DELAY,
    LISTING_COLUMNS,
    PRICE_HISTORY_COLUMNS,
)
from collector.transform import (
    build_listing_row,
    build_price_history_rows,
    enrich_listing_row,
)


logger = logging.getLogger(__name__)

MINSK_TIMEZONE = ZoneInfo("Europe/Minsk")

DATA_DIR = Path("data")
CACHE_DIR = Path(".cache/realt")


def collect_snapshot(max_ads: int | None = None) -> tuple[Path, Path]:
    """Collect a rental market snapshot and write it to CSV files."""
    collected_at = dt.datetime.now(MINSK_TIMEZONE).isoformat()
    snapshot_date = collected_at[:10]

    client = RealtClient()

    logger.info("Collecting listing pages...")
    listings, total_count = client.collect_listings(max_ads=max_ads)

    if not listings:
        raise RuntimeError("No rental listings were collected.")

    logger.info(
        "Collected %s unique listings (source total: %s).",
        len(listings),
        total_count or "unknown",
    )

    rows = {
        listing["code"]: build_listing_row(listing, collected_at)
        for listing in listings
    }

    price_history: list[dict[str, Any]] = []
    failed_cards = 0

    cache_dir = _get_cache_dir(snapshot_date, max_ads)
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Enriching listing cards...")

    for index, listing in enumerate(listings, start=1):
        ad_code = listing["code"]

        try:
            card = _load_or_fetch_card(
                client=client,
                ad_code=ad_code,
                cache_dir=cache_dir,
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
            failed_cards += 1
            logger.warning("Failed to process listing card %s: %s", ad_code, exc)
            continue

        enrich_listing_row(rows[ad_code], card)

        price_history.extend(build_price_history_rows(ad_code, card))

        if index % 50 == 0 or index == len(listings):
            logger.info("Processed %s/%s listing cards.", index, len(listings))

    price_history = _deduplicate_price_history(price_history)

    listings_path, history_path = _get_output_paths(
        snapshot_date=snapshot_date,
        max_ads=max_ads,
    )

    _write_csv(path=listings_path, rows=list(rows.values()), columns=LISTING_COLUMNS)

    _write_csv(path=history_path, rows=price_history, columns=PRICE_HISTORY_COLUMNS)

    district_count = sum(1 for row in rows.values() if row["district"])

    logger.info("Snapshot complete.")
    logger.info("Listings: %s", len(rows))
    logger.info("Price history records: %s", len(price_history))
    logger.info("Failed listing cards: %s", failed_cards)
    logger.info("District coverage: %s/%s", district_count, len(rows))

    return listings_path, history_path


def _get_cache_dir(snapshot_date: str, max_ads: int | None) -> Path:
    """Return a cache directory for the current collection run."""
    cache_type = "test" if max_ads is not None else "snapshot"
    return CACHE_DIR / cache_type / snapshot_date


def _load_or_fetch_card(client: RealtClient, ad_code: int, cache_dir: Path) -> dict[str, Any]:
    """Load a listing card from cache or fetch it from Realt.by."""
    cache_file = cache_dir / f"{ad_code}.json"

    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    card = client.fetch_listing_card(ad_code)

    cache_file.write_text(
        json.dumps(card, ensure_ascii=False),
        encoding="utf-8",
    )

    time.sleep(CARD_REQUEST_DELAY)

    return card


def _deduplicate_price_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate price history by listing code and timestamp."""
    unique_rows: dict[tuple[Any, Any], dict[str, Any]] = {}

    for row in rows:
        key = (row["ad_code"], row["recorded_at"])
        current = unique_rows.get(key)

        if current is None:
            unique_rows[key] = row
            continue

        if current["price_listed"] is None and row["price_listed"] is not None:
            unique_rows[key] = row

    return list(unique_rows.values())


def _get_output_paths(snapshot_date: str, max_ads: int | None) -> tuple[Path, Path]:
    """Build output paths for a full snapshot or a test run."""
    if max_ads is None:
        output_dir = DATA_DIR
        suffix = snapshot_date
    else:
        output_dir = CACHE_DIR / "test_output"
        suffix = f"sample_{max_ads}_{snapshot_date}"

    output_dir.mkdir(parents=True, exist_ok=True)

    return (
        output_dir / f"listings_{suffix}.csv",
        output_dir / f"price_history_{suffix}.csv",
    )


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    """Write records to a UTF-8 CSV file."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    column: (
                        ""
                        if row.get(column) is None
                        else row.get(column)
                    )
                    for column in columns
                }
            )
