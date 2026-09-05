import unittest

from collector.transform import (
    build_listing_row,
    build_price_history_rows,
    detect_seller_type,
    normalize_balcony_type,
    normalize_repair_state,
    to_number,
)


class TestTransform(unittest.TestCase):
    def test_to_number(self):
        cases = [
            ("42", 42),
            ("42.5", 42.5),
            (10, 10),
            ("", None),
            (None, None),
            ("invalid", None),
        ]

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(to_number(value), expected)

    def test_category_normalization(self):
        self.assertEqual(
            normalize_repair_state("Евроремонт"),
            "euro",
        )
        self.assertEqual(
            normalize_repair_state("Хороший"),
            "good",
        )
        self.assertEqual(
            normalize_balcony_type("лоджия"),
            "loggia",
        )
        self.assertEqual(
            normalize_balcony_type("терраса"),
            "terrace",
        )

        # Unknown source values should be preserved.
        self.assertEqual(
            normalize_repair_state("отличный"),
            "отличный",
        )
        self.assertEqual(
            normalize_balcony_type("бз"),
            "бз",
        )

    def test_detect_seller_type(self):
        agency_listing = {
            "agencyName": "Example Agency",
        }

        self.assertEqual(
            detect_seller_type(agency_listing),
            "agency",
        )
        self.assertEqual(
            detect_seller_type({}),
            "private",
        )
        self.assertEqual(
            detect_seller_type(
                {},
                {"agency": {"name": "Example Agency"}},
            ),
            "agency",
        )

    def test_build_listing_row(self):
        listing = {
            "code": 123,
            "uuid": "test-uuid",
            "price": 700,
            "priceCurrency": 840,
            "priceRates": {
                "933": 2155,
                "840": 700,
            },
            "rooms": 2,
            "areaTotal": 50.5,
            "storey": 5,
            "storeys": 10,
            "location": [27.5, 53.9],
            "createdAt": "2026-09-01T12:00:00+03:00",
            "updatedAt": "2026-09-05T12:00:00+03:00",
        }

        row = build_listing_row(
            listing,
            collected_at="2026-09-05T14:00:00+03:00",
        )

        self.assertEqual(row["ad_code"], 123)
        self.assertEqual(row["listed_price"], 700)
        self.assertEqual(row["listed_currency"], "USD")
        self.assertEqual(row["price_byn"], 2155)
        self.assertEqual(row["price_usd"], 700)
        self.assertEqual(row["area_total_m2"], 50.5)
        self.assertEqual(row["latitude"], 53.9)
        self.assertEqual(row["longitude"], 27.5)
        self.assertEqual(row["seller_type"], "private")

    def test_build_price_history_rows(self):
        card = {
            "normalizedPriceHistory": [
                {
                    "updatedAt": "2026-09-01T12:00:00+03:00",
                    "priceCurrency": 840,
                    "priceRates": {
                        "840": 700,
                        "933": 2155,
                    },
                    "status": 0,
                },
                {
                    "updatedAt": "2026-09-03T12:00:00+03:00",
                    "priceCurrency": 840,
                    "priceRates": {
                        "840": 650,
                        "933": 2001,
                    },
                    "status": -1,
                },
            ]
        }

        rows = build_price_history_rows(123, card)

        self.assertEqual(len(rows), 2)

        self.assertEqual(rows[0]["ad_code"], 123)
        self.assertEqual(rows[0]["price_currency"], "USD")
        self.assertEqual(rows[0]["price_listed"], 700)
        self.assertEqual(rows[0]["status"], 0)

        self.assertEqual(rows[1]["price_listed"], 650)
        self.assertEqual(rows[1]["status"], -1)


if __name__ == "__main__":
    unittest.main()
