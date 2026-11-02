import unittest
from zoneinfo import ZoneInfo

from argparse import Namespace

from irctc_preflight import (
    ConfigurationError,
    apply_cli_overrides,
    get_trigger_datetime,
    validate_config,
)


class ConfigValidationTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "browser": {
                "binary": "auto",
                "profile_dir": "~/.local/share/irctc-preflight/test-profile",
                "start_url": "https://www.irctc.co.in/nget/train-search",
            },
            "trip": {
                "origin": "SBC",
                "destination": "AGC",
                "journey_date": "2026-11-04",
                "quota": "GENERAL",
            },
            "schedule": {
                "timezone": "Asia/Kolkata",
                "trigger_at": "2026-11-03T10:00:00",
            },
        }

    def test_valid_config(self):
        validate_config(self.config)

    def test_rejects_non_irctc_host(self):
        self.config["browser"]["start_url"] = "https://example.com/"
        with self.assertRaises(ConfigurationError):
            validate_config(self.config)

    def test_rejects_invalid_journey_date(self):
        self.config["trip"]["journey_date"] = "04-11-2026"
        with self.assertRaises(ConfigurationError):
            validate_config(self.config)

    def test_rejects_unsupported_quota(self):
        self.config["trip"]["quota"] = "VIP"
        with self.assertRaises(ConfigurationError):
            validate_config(self.config)

    def test_trigger_uses_configured_timezone(self):
        trigger = get_trigger_datetime(self.config)
        self.assertEqual(trigger.tzinfo, ZoneInfo("Asia/Kolkata"))
        self.assertEqual(trigger.hour, 10)
        self.assertEqual(trigger.minute, 0)

    def test_cli_overrides_journey_date_and_quota(self):
        args = Namespace(
            origin=None,
            destination=None,
            journey_date="2026-11-05",
            quota="TATKAL",
            train="KARNATAKA EXP (12627)",
            travel_class="3A",
            trigger_at="2026-11-04T10:00:00",
        )
        apply_cli_overrides(self.config, args)
        self.assertEqual(self.config["trip"]["journey_date"], "2026-11-05")
        self.assertEqual(self.config["trip"]["quota"], "TATKAL")
        self.assertEqual(self.config["trip"]["preferred_train"], "KARNATAKA EXP (12627)")
        self.assertEqual(self.config["trip"]["preferred_class"], "3A")
        self.assertEqual(self.config["schedule"]["trigger_at"], "2026-11-04T10:00:00")

    def test_cli_override_rejects_invalid_date(self):
        args = Namespace(
            origin=None,
            destination=None,
            journey_date="05-11-2026",
            quota=None,
            train=None,
            travel_class=None,
            trigger_at=None,
        )
        with self.assertRaises(ConfigurationError):
            apply_cli_overrides(self.config, args)


if __name__ == "__main__":
    unittest.main()
