"""Configuration for the Realt.by rental listings collector."""

BASE_URL = "https://realt.by"

LISTINGS_URL = f"{BASE_URL}/rent/flat-for-long/"
LISTING_CARD_URL = f"{BASE_URL}/rent-flat-for-long/object/{{code}}/"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

REQUEST_TIMEOUT = 25
REQUEST_RETRIES = 3

LIST_PAGE_DELAY = 0.3
CARD_REQUEST_DELAY = 0.35

CURRENCY_CODES = {
    643: "RUB",
    840: "USD",
    933: "BYN",
    978: "EUR",
}

PRICE_CHANGE_DIRECTION = {
    -1: "down",
    1: "up",
}

METRO_TIME_MODE = {
    1: "walk",
    2: "transport",
}

REPAIR_STATE_MAP = {
    "евроремонт": "euro",
    "хороший": "good",
    "нормальный": "normal",
}

BALCONY_TYPE_MAP = {
    "нет": None,
    "лоджия застекленная": "loggia_glazed",
    "лоджия": "loggia",
    "балкон": "balcony",
    "терраса": "terrace",
}

LISTING_COLUMNS = [
    "ad_code",
    "ad_uuid",
    "collected_at",
    "listed_price",
    "listed_currency",
    "price_byn",
    "price_usd",
    "price_change_date",
    "price_change_direction",
    "rooms",
    "area_total_m2",
    "area_living_m2",
    "area_kitchen_m2",
    "floor",
    "floors_total",
    "building_year",
    "repair_state",
    "has_furniture",
    "balcony",
    "latitude",
    "longitude",
    "metro_station",
    "metro_time_min",
    "metro_time_mode",
    "district",
    "subdistrict",
    "created_at",
    "updated_at",
    "raise_date",
    "new_again_date",
    "seller_type",
]

PRICE_HISTORY_COLUMNS = [
    "ad_code",
    "recorded_at",
    "price_currency",
    "price_listed",
    "price_byn",
    "price_usd",
    "status",
]
