# IRCTC Browser Preflight (Fedora KDE)

A small Python utility for preparing a **manual** IRCTC booking session. It launches Chromium through Selenium using a dedicated persistent browser profile, opens the official IRCTC train-search page, and shows a KDE desktop/terminal reminder at a configured time.

It does **not** log in, search trains, change quota/class, select trains, fill passenger forms, submit booking requests, handle OTP/CAPTCHA, or make payments. Those actions remain manual.

> **IRCTC policy:** IRCTC's published terms state that use of automation and/or scripting software is prohibited and identify suspicious activity involving scripting tools/Tatkal software as grounds for account deactivation and ticket release without refund. Read the current [IRCTC terms and conditions](https://contents.irctc.co.in/en/Terms%20and%20conditions.pdf) before using browser automation. This project deliberately limits automation to opening a browser and displaying a reminder.

## Fedora KDE installation

```bash
sudo dnf install python3 python3-pip chromium libnotify
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp config.example.toml config.toml
```

Edit `config.toml`: set station codes and `journey_date` (YYYY-MM-DD), choose `quota` as `GENERAL`, `TATKAL` or `PREMIUM TATKAL`, set the preferred train/class notes, and choose a future `trigger_at` time. The sample is SBC → AGC, 2026-11-04, Karnataka Express (12627), 3A. These values are displayed as reminders only; the script does not select the quota, train, class or date on the IRCTC page. The timezone defaults to `Asia/Kolkata`. Update the trigger before every run; the script rejects past times.

One-run overrides (do not edit the TOML file):

```bash
python irctc_preflight.py --config config.toml --date 2026-11-04 --quota GENERAL
python irctc_preflight.py --config config.toml --date 2026-11-04 --quota TATKAL
python irctc_preflight.py --config config.toml --date 2026-11-04 --quota "PREMIUM TATKAL"
```

Optional overrides: `--origin SBC`, `--destination AGC`, `--train "KARNATAKA EXP (12627)"`, `--class 3A`, and `--trigger-at 2026-11-03T10:00:00`. Overrides apply to that run only.

## Run

Validate configuration and local dependencies without opening a browser:

```bash
python irctc_preflight.py --config config.toml --check-only
```

Launch Chromium and wait for the reminder:

```bash
python irctc_preflight.py --config config.toml
```

At the reminder time, the terminal prints the screenshot-matched manual sequence:

1. Search the configured route, date and quota.
2. Find Karnataka Express (12627), open 3A availability and refresh/check the required date.
3. Select the required date card and click Book Now.
4. Select the intended saved passenger from Master List and verify the prefilled details.
5. Choose the payment mode and click Continue.
6. Review the journey, passenger and fare details; click Continue.
7. Complete IRCTC verification and payment manually.

The checklist is informational only. It does not click, refresh, select, populate or submit any IRCTC page controls.

## Security

The profile defaults to `~/.local/share/irctc-preflight/chrome-profile` and can contain session cookies. Do not commit, upload, share or sync it. The application does not ask for or store passwords, passenger data, Aadhaar details, OTPs or payment information.

The script does not hide WebDriver, bypass bot checks, defeat CAPTCHA/OTP, call private IRCTC endpoints or manipulate page controls. Do not add these behaviours. Close the browser using the script before launching another instance with the same profile.

## Clock accuracy

Check Fedora's clock/NTP status before a time-sensitive run:

```bash
timedatectl status
sudo timedatectl set-ntp true
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## References

- [Selenium Manager documentation](https://www.selenium.dev/documentation/selenium_manager/) — built-in browser-driver management.
- [Selenium Python documentation](https://www.selenium.dev/selenium/docs/api/py/) — Python bindings and installation.
- [IRCTC terms and conditions](https://contents.irctc.co.in/en/Terms%20and%20conditions.pdf) — current terms take precedence.
