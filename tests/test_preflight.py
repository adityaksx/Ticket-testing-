import unittest
from zoneinfo import ZoneInfo

from irctc_preflight import ConfigurationError, get_trigger_datetime, validate_config


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


if __name__ == "__main__":
    unittest.main()
