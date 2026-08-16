"""Diagnostics support for De'Longhi Coffee Link."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_DSN, DOMAIN
from .coordinator import CoffeeLinkCoordinator

REDACT = {CONF_USERNAME, CONF_PASSWORD, CONF_DSN, "dsn"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: CoffeeLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry": async_redact_data(entry.data, REDACT),
        "data": async_redact_data(coordinator.data or {}, REDACT),
    }
