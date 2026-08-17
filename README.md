# De'Longhi Coffee Link — Home Assistant integration

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lrfsh&repository=coffeelink-ha&category=integration)

[![License](https://img.shields.io/github/license/lrfsh/coffeelink-ha?style=for-the-badge&color=success)](LICENSE)
[![Source Code](https://img.shields.io/badge/Source-GitHub-black?style=for-the-badge&logo=github)](https://github.com/lrfsh/coffeelink-ha)

Monitor and control a WiFi De'Longhi coffee machine (the ones paired with the
**Coffee Link** app) directly from Home Assistant — cloud-only, no companion app,
no Android emulator, no external cron. Verified on an **Eletta Explore 450.65.G**.

## How it works

The machine speaks the binary **ECAM** protocol tunnelled through the **Ayla
Networks** IoT cloud. Auth is a two-step, fully headless chain:

1. **Gigya** `accounts.login` (email + password) → `id_token`
2. **Ayla** `token_sign_in` (app_id + app_secret + id_token) → `access_token` (24 h)

The integration then reads/writes Ayla *properties*. The De'Longhi app's Gigya key
and Ayla `app_id`/`app_secret` are **hardcoded in the app and identical for every
user**, so you only ever provide your **email + password**. Token lifetime is
handled by the coordinator (refresh token → full re-login fallback) — **no cron is
required.**

### Power-on (the tricky bit)

ECAM/Eletta machines ignore a "cold" command. Power-on uses the **DlghIoT
cloud-session handshake**:

1. Register a session — write `app_device_connected`
2. Poll the machine's `app_id` property until it reflects our session (~10–15 s)
3. Send the ECAM `84 0f` wake command → the machine relays it → standby → on

## Install

### Via HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**
2. Add `https://github.com/lrfsh/coffeelink-ha`, category
   **Integration**
3. Install **De'Longhi Coffee Link**, then restart Home Assistant

### Manual

Copy `custom_components/delonghi_coffeelink/` into your `config/custom_components/`
directory and restart Home Assistant.

### Configure

**Settings → Devices & Services → Add Integration → De'Longhi Coffee Link**, then
enter your Coffee Link **email**, **password**, and **region**.

## Entities

| Entity | Type | Notes |
|--------|------|-------|
| Wake up | button | Powers the machine on / wakes it from standby |
| Status | sensor (enum) | `on` / `standby` / `offline` |
| Power | binary_sensor | on while the machine is powered on |
| Cloud connection | binary_sensor | Ayla connectivity |
| Connected since | sensor (timestamp) | WiFi module online-since (uptime) |
| Total beverages | sensor | lifetime counter |
| Total espressi | sensor | lifetime counter |
| Total cappuccinos | sensor | lifetime counter |
| Coffee grounds in tray | sensor | pucks since the tray was emptied |
| Beverages until descale | sensor | maintenance countdown |
| Filters used | sensor | lifetime counter |
| Water hardness | sensor | configured hardness level |

Per-beverage brew buttons (espresso, cappuccino, …) are planned — they need one
"learn" pass to capture each dispense frame.

## Compatibility

| Machine | oem_model | Monitoring | Power-on | Status |
|---------|-----------|:---------:|:--------:|--------|
| Eletta Explore 450.65.G | `DL-striker-cb` | ✅ | ✅ | **Verified** |
| Other Eletta Explore (`DL-striker*`) | `DL-striker*` | ✅ | ✅ | Expected, untested |
| Other Coffee Link machines (Dinamica, PrimaDonna, Magnifica Evo WiFi, …) | Ayla + ECAM | ✅ | ⚠️ | Likely; may need per-model tuning |
| Eletta Ultra / "My Coffee Lounge" | Daedalus (AWS + MQTT) | ❌ | ❌ | **Not supported** (different stack) |

If you run a machine not listed as verified, please open an issue with your
`oem_model` and a diagnostics download — most Coffee Link machines share this
Ayla/ECAM stack and should work.

### Regions

`eu` is verified against a live account. `us` / `cn` use the standard Ayla/Gigya
hosts and may need a region-specific Gigya key — open an issue if you run one.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Credits & prior art

- `actabi/delonghi_coffeelink` — the cloud-session handshake (`app_id` confirm)
  that makes power-on actually work
- `sk7n4k3d/delonghi-ha` — Ayla/Gigya flow & property names
- `miditkl/cremalink` — generic local+cloud De'Longhi bridge
- `prototux/delonghi-re`, `Arbuzov/home_assistant_delonghi_primadonna` — ECAM frame
  format

## Legal

Reverse-engineered for interoperability with your own machine. The app_id/app_secret
belong to De'Longhi and are shipped only to allow that interoperability, exactly as
the existing community integrations do. Not affiliated with or endorsed by De'Longhi.
