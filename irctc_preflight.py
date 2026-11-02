#!/usr/bin/env python3
"""Launch a persistent IRCTC browser profile and show a scheduled reminder.

This tool deliberately does not interact with IRCTC page controls. The user
performs login, train search, quota/class selection, passenger entry, OTP and
payment manually.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import tomllib
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

IRCTC_SEARCH_URL = "https://www.irctc.co.in/nget/train-search"
BROWSER_CANDIDATES = (
    "chromium",
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
)


class ConfigurationError(ValueError):
    """Raised when the TOML configuration is invalid."""


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as config_file:
            config = tomllib.load(config_file)
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Config file not found: {path}. Copy config.example.toml to config.toml."
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Invalid TOML in {path}: {exc}") from exc

    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    for section in ("browser", "trip", "schedule"):
        if not isinstance(config.get(section), dict):
            raise ConfigurationError(f"Missing [{section}] section in config.")

    browser = config["browser"]
    trip = config["trip"]
    schedule = config["schedule"]

    binary = browser.get("binary", "auto")
    if not isinstance(binary, str) or not binary.strip():
        raise ConfigurationError("[browser].binary must be a non-empty string.")

    profile_dir = browser.get("profile_dir")
    if not isinstance(profile_dir, str) or not profile_dir.strip():
        raise ConfigurationError("[browser].profile_dir must be a non-empty path.")

    start_url = browser.get("start_url", IRCTC_SEARCH_URL)
    parsed_url = urlparse(start_url)
    if parsed_url.scheme != "https" or parsed_url.hostname != "www.irctc.co.in":
        raise ConfigurationError(
            "[browser].start_url must use the official https://www.irctc.co.in host."
        )

    for key in ("origin", "destination"):
        code = trip.get(key)
        if not isinstance(code, str) or not (2 <= len(code.strip()) <= 5):
            raise ConfigurationError(
                f"[trip].{key} must be a station code (2–5 characters)."
            )
        if not code.strip().isalnum():
            raise ConfigurationError(
                f"[trip].{key} must contain only letters or digits."
            )

    try:
        date.fromisoformat(trip["journey_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigurationError(
            "[trip].journey_date must use YYYY-MM-DD format."
        ) from exc

    quota = str(trip.get("quota", "GENERAL")).upper()
    if quota not in {"GENERAL", "TATKAL", "PREMIUM TATKAL"}:
        raise ConfigurationError(
            "[trip].quota must be GENERAL, TATKAL or PREMIUM TATKAL."
        )

    timezone_name = schedule.get("timezone", "Asia/Kolkata")
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError) as exc:
        raise ConfigurationError(f"Unknown timezone: {timezone_name!r}") from exc

    if not isinstance(schedule.get("trigger_at"), str):
        raise ConfigurationError(
            "[schedule].trigger_at must be an ISO local datetime string."
        )
    try:
        datetime.fromisoformat(schedule["trigger_at"])
    except ValueError as exc:
        raise ConfigurationError(
            "[schedule].trigger_at must use YYYY-MM-DDTHH:MM:SS format."
        ) from exc


def get_trigger_datetime(config: dict[str, Any]) -> datetime:
    timezone = ZoneInfo(config["schedule"].get("timezone", "Asia/Kolkata"))
    parsed = datetime.fromisoformat(config["schedule"]["trigger_at"])
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone)


def find_browser(binary_setting: str) -> str:
    if binary_setting != "auto":
        resolved = shutil.which(binary_setting)
        if resolved is None and not Path(binary_setting).is_file():
            raise ConfigurationError(
                f"Browser executable not found: {binary_setting}. "
                "Install Chromium or set its path."
            )
        return resolved or str(Path(binary_setting).expanduser().resolve())

    for candidate in BROWSER_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise ConfigurationError(
        "No supported browser found. Install Chromium with: sudo dnf install chromium"
    )


def make_profile_directory(config: dict[str, Any]) -> Path:
    profile = Path(config["browser"]["profile_dir"]).expanduser()
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Browser profiles contain session cookies. Keep the directory private.
    try:
        profile.chmod(0o700)
    except OSError:
        pass
    return profile.resolve()


def launch_browser(config: dict[str, Any], browser_binary: str, profile: Path):
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
    except ImportError as exc:
        raise RuntimeError(
            "Selenium is not installed. Activate your virtual environment and run "
            "'python -m pip install -r requirements.txt'."
        ) from exc

    options = Options()
    options.binary_location = browser_binary
    options.add_argument(f"--user-data-dir={profile}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--start-maximized")
    options.add_argument("--no-first-run")

    # Selenium Manager resolves a compatible driver in modern Selenium releases.
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(config["browser"].get("start_url", IRCTC_SEARCH_URL))
        return driver
    except Exception as exc:  # Selenium raises different exceptions by version.
        raise RuntimeError(
            "Could not start Chromium through Selenium. Close any existing Chromium "
            "window using this profile, check the browser installation and network "
            "access for Selenium Manager, then retry."
        ) from exc


def show_notification(title: str, message: str) -> None:
    notify_send = shutil.which("notify-send")
    if notify_send:
        try:
            subprocess.run(
                [notify_send, "--urgency=critical", title, message],
                check=False,
                timeout=4,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    # Also alert in the terminal; KDE notification services may be disabled.
    print("\a\a", end="", flush=True)
    print(f"\n[{title}] {message}", flush=True)


def wait_until(target: datetime) -> None:
    print(f"\nReminder scheduled for: {target:%Y-%m-%d %H:%M:%S %Z}")
    while True:
        remaining = (target - datetime.now(target.tzinfo)).total_seconds()
        if remaining <= 0:
            break
        print(f"\rTime remaining: {remaining:6.1f}s", end="", flush=True)
        time.sleep(min(0.5, remaining))
    print("\rTime remaining:   0.0s                 ", flush=True)


def print_trip_summary(
    config: dict[str, Any], profile: Path, browser_binary: str
) -> None:
    trip = config["trip"]
    print("\n=== IRCTC browser preparation ===")
    print(f"Route:       {trip['origin'].upper()} -> {trip['destination'].upper()}")
    print(f"Journey:     {trip['journey_date']}")
    print(f"Quota:       {str(trip.get('quota', 'GENERAL')).upper()}")
    if trip.get("preferred_train"):
        print(f"Train note:  {trip['preferred_train']}")
    if trip.get("preferred_class"):
        print(f"Class note:  {trip['preferred_class']}")
    print(f"Browser:     {browser_binary}")
    print(f"Profile:     {profile}")
    print("Credentials: not stored or read by this application")
    print("Automation:  browser launch and reminder only; page actions are manual")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch a persistent IRCTC browser profile and show a reminder."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("config.toml"),
        help="TOML config path (default: ./config.toml)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate configuration and browser/Selenium installation without opening a browser.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        target = get_trigger_datetime(config)
        now = datetime.now(target.tzinfo)
        if target <= now:
            raise ConfigurationError(
                f"Configured trigger time {target:%Y-%m-%d %H:%M:%S %Z} is not in the future. "
                "Update [schedule].trigger_at in config.toml."
            )

        browser_binary = find_browser(config["browser"].get("binary", "auto"))
        profile = make_profile_directory(config)
        print_trip_summary(config, profile, browser_binary)

        if args.check_only:
            try:
                import selenium  # noqa: F401
            except ImportError as exc:
                raise RuntimeError(
                    "Selenium is missing; install requirements.txt."
                ) from exc
            print("\nPreflight passed. Browser launch was not attempted (--check-only).")
            return 0

        print("\nLaunching browser. Log in manually and prepare the official search page.")
        driver = launch_browser(config, browser_binary, profile)
        try:
            wait_until(target)
            trip = config["trip"]
            show_notification(
                "IRCTC reminder",
                f"Start your manual search: {trip['origin'].upper()} -> "
                f"{trip['destination'].upper()} | {trip['journey_date']} | "
                f"{str(trip.get('quota', 'GENERAL')).upper()}",
            )
            print("Complete all page actions, verification and payment manually.")
            input("\nPress ENTER here after you are finished to close the browser... ")
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            try:
                input("Press ENTER to close the browser... ")
            except (EOFError, KeyboardInterrupt):
                pass
        finally:
            driver.quit()
        return 0
    except (ConfigurationError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
