# De'Longhi Coffee Link — Home Assistant integration

Control and monitor a WiFi De'Longhi coffee machine (the ones paired with the
**Coffee Link** app) directly from Home Assistant — no cloud webhooks, no Android
app, no external cron. Verified on an **Eletta Explore 450.65.G** (`oem_model
DL-striker-cb`, EU region).

## How it works

The machine talks the binary **ECAM** protocol tunnelled through **Ayla
Networks** IoT cloud. Auth is a two-step chain, fully headless:

1. **Gigya** `accounts.login` (email + password) → `id_token`
2. **Ayla** `token_sign_in` (app_id + app_secret + id_token) → `access_token` (24 h)

The integration then reads/writes Ayla *properties*. Commands (e.g. power-on) are
raw ECAM frames written base64-encoded to the `app_data_request` property.

The De'Longhi app's Gigya key and Ayla `app_id`/`app_secret` are **hardcoded in
the app and identical for every user** — they ship inside this integration, so you
only ever provide your **email + password**. Token lifetime is handled by the
`DataUpdateCoordinator` (refresh token → full re-login fallback); **no cron or
CronJob is required.**

## Install (HACS custom repository)

1. HACS → ⋮ → **Custom repositories**
2. Add `https://github.com/lrfsh/homeassistant-delonghi-coffeelink`, category
   **Integration**
3. Install **De'Longhi Coffee Link**, then restart Home Assistant
4. **Settings → Devices & Services → Add Integration → De'Longhi Coffee Link**
5. Enter your Coffee Link **email**, **password**, and **region** (EU / US / CN)

## Entities (v1)

| Entity | Type | Notes |
|--------|------|-------|
| Wake up | button | Powers the machine on / wakes it from standby |
| Status | sensor (enum) | `ready` / `heating` / `standby` / `offline` |
| Total beverages | sensor | lifetime counter |
| Total espressi | sensor | lifetime counter |
| Total cappuccinos | sensor | lifetime counter |
| Coffee grounds in tray | sensor | pucks since the tray was emptied |
| Beverages until descale | sensor | maintenance countdown |
| Filters used | sensor | lifetime counter |
| Water hardness | sensor | configured hardness level |

Per-beverage brew buttons (espresso, cappuccino, …) are planned for v2 — they need
one "learn" pass to capture each dispense frame.

## Regions

`eu` is verified against a live account. `us` / `cn` use the standard Ayla/Gigya
hosts and may need a region-specific Gigya key; open an issue with details if you
run one of those.

## Credits & prior art

- `sk7n4k3d/delonghi-ha`, `actabi/delonghi_coffeelink` — Ayla/Gigya flow & property
  names
- `prototux/delonghi-re`, `Arbuzov/home_assistant_delonghi_primadonna` — ECAM frame
  format
- `ayla-iot-unofficial` — generic Ayla client reference

## Legal

Reverse-engineered for interoperability with your own machine. The app_id/app_secret
belong to De'Longhi and are shipped only to allow that interoperability, exactly as
the existing community integrations do. Not affiliated with or endorsed by De'Longhi.
