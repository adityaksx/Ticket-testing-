# Project Plan

## Objective

Reduce avoidable preparation overhead for a user-operated IRCTC booking session on Fedora KDE. The first release focuses on a stable browser profile, a configurable journey summary, and a time-based reminder.

## Scope for v0.1

1. **Environment preflight** — check Python, Selenium, Chromium/Chrome and configuration.
2. **Dedicated browser profile** — launch the official IRCTC train-search page with a persistent, owner-only browser profile.
3. **Manual authentication** — user enters credentials and completes verification directly on IRCTC.
4. **Journey configuration** — keep origin, destination, journey date, quota and preferred train/class as local planning metadata; support one-run CLI overrides.
5. **Time reminder** — wait until a timezone-aware target and notify through KDE (`notify-send`) and the terminal.
6. **Manual flow checklist** — print the screenshot-matched sequence for Karnataka Express (12627), 3A availability, date card, Book Now, Master List passenger, payment-mode Continue and review-page Continue.
7. **Clean shutdown** — keep the WebDriver session alive while the user completes manual actions, then close it on confirmation.

## Explicit non-goals

- Automated IRCTC login or credential storage.
- Automated train search, quota/class selection or seat-selection clicks.
- Automated passenger master-list selection or passenger-form submission.
- CAPTCHA, Aadhaar OTP or other verification automation.
- Automated payment, payment-gateway interaction or booking confirmation.
- Stealth WebDriver flags, anti-bot evasion, private API calls, request replay or rate-limit bypass.

IRCTC's published terms prohibit automation/scripting software. The project intentionally stays at browser launch and notification level; any later scope change must be reviewed against the current IRCTC terms before implementation.

## Runtime flow

```text
Read TOML config
      |
Validate station/date/time settings
      |
Find Chromium/Chrome and prepare private profile
      |
Launch Selenium-managed browser at official IRCTC search page
      |
User logs in and prepares the page manually
      |
Wait for configured Asia/Kolkata reminder time
      |
Show KDE + terminal notification
      |
User performs every booking interaction manually
      |
User confirms completion -> close browser
```

## Fedora KDE setup

- Python 3.11+ (`tomllib` is part of the standard library).
- Chromium or Google Chrome.
- Selenium 4.27+; Selenium Manager normally resolves the compatible driver.
- `libnotify` for desktop notifications. The terminal alert remains available if notifications are unavailable.

## Verification checklist

- [ ] Invalid TOML or missing config reports a useful error.
- [ ] Invalid station codes, journey dates, timezone names and past trigger times are rejected.
- [ ] `--check-only` detects missing browser or Selenium without opening a session.
- [ ] Browser launches with the dedicated profile and opens only the official IRCTC host.
- [ ] A second run can reuse the profile after the first browser session is closed.
- [ ] Trigger produces a terminal alert and a KDE desktop notification when `notify-send` is installed.
- [ ] No credentials, passenger PII, OTPs or payment data are written to configuration or logs.
- [ ] CLI date and quota overrides are validated and do not mutate the saved TOML file.
- [ ] The screenshot-matched manual checklist prints at reminder time.
- [ ] No IRCTC page controls or booking endpoints are automated.

## Possible next improvements

- Add a simple KDE tray/countdown UI without interacting with IRCTC pages.
- Add a read-only local history of reminder runs (no account or passenger data).
- Add optional system-clock/NTP diagnostics before launch.
- Add tests for more configuration edge cases and desktop-notification fallback behaviour.
