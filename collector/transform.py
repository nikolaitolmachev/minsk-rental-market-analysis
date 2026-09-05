"""Transform raw Realt.by data into analysis-ready records."""

from typing import Any

from collector.config import (
    BALCONY_TYPE_MAP,
    CURRENCY_CODES,
    METRO_TIME_MODE,
    PRICE_CHANGE_DIRECTION,
    REPAIR_STATE_MAP,
)


def to_number(value: Any) -> int | float | None:
    """Convert a numeric value to int or float when possible."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return int(number) if number.is_integer() else number


def optional_string(value: Any) -> str | None:
    """Return a non-empty string or None."""
    return value if isinstance(value, str) and value else None


def currency_label(code: Any) -> str | None:
    """Convert an ISO 4217 numeric currency code to its string label."""
    if code is None:
        return None

    return CURRENCY_CODES.get(code, str(code))


def normalize_repair_state(value: Any) -> str | None:
    """Normalize a human-readable repair state returned by a listing card."""
    if value is None or not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    return REPAIR_STATE_MAP.get(normalized, normalized)


def normalize_balcony_type(value: Any) -> str | None:
    """Normalize a human-readable balcony type returned by a listing card."""
    if value is None or not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    return BALCONY_TYPE_MAP.get(normalized, normalized)


def detect_seller_type(listing: dict[str, Any], card: dict[str, Any] | None = None) -> str:
    """Classify a listing as agency or private based on agency metadata."""
    agency_fields = (
        "agencyName",
        "agencyUuid",
        "companyName",
        "companyUuid",
    )

    has_agency_metadata = any(listing.get(field) for field in agency_fields)
    card_has_agency = bool(card and card.get("agency"))

    return "agency" if has_agency_metadata or card_has_agency else "private"


def build_listing_row(listing: dict[str, Any], collected_at: str) -> dict[str, Any]:
    """Build an analysis-ready row from a rental listing."""
    location = listing.get("location") or []
    price_rates = listing.get("priceRates") or {}

    latitude = to_number(location[1]) if len(location) == 2 else None
    longitude = to_number(location[0]) if len(location) == 2 else None

    return {
        "ad_code": listing.get("code"),
        "ad_uuid": listing.get("uuid"),
        "collected_at": collected_at,
        "listed_price": to_number(listing.get("price")),
        "listed_currency": currency_label(listing.get("priceCurrency")),
        "price_byn": to_number(price_rates.get("933")),
        "price_usd": to_number(price_rates.get("840")),
        "price_change_date": optional_string(listing.get("priceChangeDate")),
        "price_change_direction": PRICE_CHANGE_DIRECTION.get(listing.get("priceChangeDirection")),
        "rooms": to_number(listing.get("rooms")),
        "area_total_m2": to_number(listing.get("areaTotal")),
        "area_living_m2": to_number(listing.get("areaLiving")),
        "area_kitchen_m2": to_number(listing.get("areaKitchen")),
        "floor": to_number(listing.get("storey")),
        "floors_total": to_number(listing.get("storeys")),
        "building_year": to_number(listing.get("buildingYear")),
        "repair_state": None,
        "has_furniture": None,
        "balcony": None,
        "latitude": latitude,
        "longitude": longitude,
        "metro_station": optional_string(listing.get("metroStationName")),
        "metro_time_min": to_number(listing.get("metroTime")),
        "metro_time_mode": METRO_TIME_MODE.get(listing.get("metroTimeType")),
        "district": None,
        "subdistrict": None,
        "created_at": optional_string(listing.get("createdAt")),
        "updated_at": optional_string(listing.get("updatedAt")),
        "raise_date": None,
        "new_again_date": None,
        "seller_type": detect_seller_type(listing),
    }


def enrich_listing_row(row: dict[str, Any], card: dict[str, Any]) -> None:
    """Enrich a listing row with fields available only on the listing card."""
    row["district"] = optional_string(card.get("townDistrictName"))
    row["subdistrict"] = optional_string(card.get("townSubDistrictName"))
    row["raise_date"] = optional_string(card.get("raiseDate"))
    row["new_again_date"] = optional_string(card.get("newAgainDate"))

    if card.get("repairState") is not None:
        row["repair_state"] = normalize_repair_state(card.get("repairState"))

    if isinstance(card.get("furniture"), bool):
        row["has_furniture"] = card["furniture"]

    if card.get("balconyType") is not None:
        row["balcony"] = normalize_balcony_type(card.get("balconyType"))

    if detect_seller_type({}, card) == "agency":
        row["seller_type"] = "agency"


def build_price_history_rows(ad_code: int, card: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert normalized price history into long-format records.

    A record with status 0 represents the earliest price known to the source,
    not necessarily the original listing price.
    """
    rows = []

    for record in card.get("normalizedPriceHistory") or []:
        recorded_at = optional_string(record.get("updatedAt"))

        if recorded_at is None:
            continue

        price_rates = record.get("priceRates") or {}
        currency_code = record.get("priceCurrency")
        price_currency = currency_label(currency_code)

        price_listed = to_number(price_rates.get(str(currency_code))) if currency_code is not None else None

        rows.append(
            {
                "ad_code": ad_code,
                "recorded_at": recorded_at,
                "price_currency": price_currency,
                "price_listed": price_listed,
                "price_byn": to_number(price_rates.get("933")),
                "price_usd": to_number(price_rates.get("840")),
                "status": record.get("status"),
            }
        )

    return rows
