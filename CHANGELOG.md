# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-08-17

### Added
- **Maintenance alarms** decoded from the monitor alarm bitfield, each a `problem`
  binary sensor: **Water tank empty**, **Grounds container full**, **Descaling
  needed**, **Water filter** — plus a generic **Problem** sensor (on for any alarm).
- Detailed machine **Status** states — `ready`, `rinsing`, `descaling`,
  `preparing_steam`, `preparing_milk`, `dispensing_hot_water`, `cleaning_milk`,
  `waking_up`, `going_to_sleep`, … — decoded from the monitor status code.

### Changed
- The **Status** sensor now reports the machine's real operational state instead of
  a plain on / standby.

[0.1.1]: https://github.com/lrfsh/coffeelink-ha/releases/tag/v0.1.1

## [0.1.0] - 2026-08-17

Initial release.

### Added
- Cloud (Ayla) integration for De'Longhi **Coffee Link** machines — fully
  headless auth (email + password); no companion app or Android emulator needed
  at runtime.
- Config flow with **region** selection (EU verified; US/CN endpoints included).
- `DataUpdateCoordinator` with automatic **access-token refresh** (refresh token,
  falling back to a full re-login). No cron / external scheduler required.
- **Wake / power-on** via the DlghIoT **cloud-session handshake**: register a
  session (`app_device_connected`), poll the machine's `app_id` property until it
  acknowledges the session, then send the ECAM `84 0f` command. Validated live on
  an Eletta Explore 450.65.G.
- **Sensors:** status (on / standby / offline), total beverages, total espressi,
  total cappuccinos, coffee grounds in tray, beverages until descale, filters
  used, water hardness, connected-since (uptime).
- **Binary sensors:** Power (running), Cloud connection (connectivity).
- **Button:** Wake up.
- Redacted diagnostics.

### Notes
- Ships De'Longhi's shared app credentials (Gigya API key + Ayla
  `app_id`/`app_secret`), same as every community integration — required for
  interoperability, not user secrets.

[0.1.0]: https://github.com/lrfsh/coffeelink-ha/releases/tag/v0.1.0
