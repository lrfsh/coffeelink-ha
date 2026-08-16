"""Constants for the De'Longhi Coffee Link integration."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "delonghi_coffeelink"
PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.BUTTON,
]

# Config entry keys (email/password/region use homeassistant.const equivalents).
CONF_DSN = "dsn"
CONF_MODEL = "model"
CONF_OEM_MODEL = "oem_model"

DEFAULT_REGION = "eu"
DEFAULT_SCAN_INTERVAL = 30  # seconds
