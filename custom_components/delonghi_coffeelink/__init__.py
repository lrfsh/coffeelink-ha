"""The De'Longhi Coffee Link integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coffeelink import CoffeeLinkClient
from .const import CONF_DSN, CONF_MODEL, DEFAULT_REGION, DOMAIN, PLATFORMS
from .coordinator import CoffeeLinkCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up De'Longhi Coffee Link from a config entry."""
    session = async_get_clientsession(hass)
    client = CoffeeLinkClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_REGION, DEFAULT_REGION),
    )
    client.dsn = entry.data[CONF_DSN]

    coordinator = CoffeeLinkCoordinator(hass, client, entry.data[CONF_DSN])
    coordinator.model = entry.data.get(CONF_MODEL)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
