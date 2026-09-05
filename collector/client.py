"""HTTP client for collecting rental listings from Realt.by."""

import datetime as dt
import json
import logging
import re
import time
from typing import Any

import requests

from collector.config import (
    LIST_PAGE_DELAY,
    LISTING_CARD_URL,
    LISTINGS_URL,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
    USER_AGENT,
)


logger = logging.getLogger(__name__)


class RealtClient:
    """Client for retrieving rental listing data from Realt.by."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json, text/html",
            }
        )

    def fetch_html(self, url: str) -> str:
        """Fetch HTML from a URL with retry handling."""
        last_error: str | None = None

        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)

                if response.status_code == 200 and response.text:
                    return response.text

                last_error = f"HTTP {response.status_code}"

            except requests.RequestException as exc:
                last_error = str(exc)

            if attempt < REQUEST_RETRIES - 1:
                time.sleep(1.5 * (attempt + 1))

        raise RuntimeError(f"Failed to fetch {url} after {REQUEST_RETRIES} attempts: {last_error}")

    def fetch_listing_page(self, page: int) -> dict[str, Any]:
        """Fetch and parse one rental listings page."""
        if page < 1:
            raise ValueError("Page number must be greater than or equal to 1.")

        url = LISTINGS_URL if page == 1 else f"{LISTINGS_URL}?page={page}"
        html = self.fetch_html(url)

        return self._extract_page_props(html)

    def fetch_listing_card(self, ad_code: int) -> dict[str, Any]:
        """Fetch and parse an individual rental listing card."""
        url = LISTING_CARD_URL.format(code=ad_code)
        html = self.fetch_html(url)

        return self._extract_page_props(html).get("object") or {}

    def collect_listings(self, max_ads: int | None = None) -> tuple[list[dict[str, Any]], int | None]:
        """Collect unique rental listings from all result pages.

        If the same listing appears more than once during pagination,
        the version with the latest ``updatedAt`` value is retained.
        """
        listings_by_code: dict[int, dict[str, Any]] = {}
        page = 1
        total_count: int | None = None

        while True:
            page_data = self.fetch_listing_page(page)
            total_count = page_data.get("totalCount", total_count)
            batch = page_data.get("objects") or []

            if not batch:
                break

            previous_count = len(listings_by_code)

            for listing in batch:
                ad_code = listing.get("code")

                if ad_code is None:
                    continue

                current_listing = listings_by_code.get(ad_code)

                if current_listing is None or self._is_newer(
                    listing,
                    current_listing,
                ):
                    listings_by_code[ad_code] = listing

            added_count = len(listings_by_code) - previous_count

            logger.info(
                "Page %s: %s new listings, %s/%s unique listings collected",
                page,
                added_count,
                len(listings_by_code),
                total_count or "?",
            )

            if total_count is not None and len(listings_by_code) >= total_count:
                break

            if added_count == 0:
                break

            if max_ads is not None and len(listings_by_code) >= max_ads:
                break

            page += 1
            time.sleep(LIST_PAGE_DELAY)

        listings = list(listings_by_code.values())

        if max_ads is not None:
            listings = listings[:max_ads]

        return listings, total_count

    @staticmethod
    def _extract_page_props(html: str) -> dict[str, Any]:
        """Extract Next.js page properties from an HTML document."""
        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )

        if not match:
            raise ValueError("__NEXT_DATA__ was not found in the HTML.")

        next_data = json.loads(match.group(1))

        try:
            return next_data["props"]["pageProps"]
        except KeyError as exc:
            raise ValueError("Unexpected __NEXT_DATA__ structure: pageProps is missing.") from exc

    @staticmethod
    def _parse_timestamp(value: str | None) -> dt.datetime | None:
        """Parse an ISO 8601 timestamp returned by Realt.by."""
        if not value:
            return None

        try:
            return dt.datetime.fromisoformat(value)
        except ValueError:
            return None

    @classmethod
    def _is_newer(cls, candidate: dict[str, Any], current: dict[str, Any]) -> bool:
        """Return whether the candidate listing has a newer update timestamp."""
        candidate_time = cls._parse_timestamp(candidate.get("updatedAt"))
        current_time = cls._parse_timestamp(current.get("updatedAt"))

        if candidate_time is None:
            return False

        if current_time is None:
            return True

        return candidate_time > current_time
