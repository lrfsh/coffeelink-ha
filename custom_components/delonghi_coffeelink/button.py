"""Buttons for De'Longhi Coffee Link."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CoffeeLinkCoordinator
from .entity import CoffeeLinkEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CoffeeLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CoffeeLinkWakeButton(coordinator)])


class CoffeeLinkWakeButton(CoffeeLinkEntity, ButtonEntity):
    """Wake the machine from standby (power on)."""

    _attr_translation_key = "wake"
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: CoffeeLinkCoordinator) -> None:
        super().__init__(coordinator, "wake")

    async def async_press(self) -> None:
        await self.coordinator.client.async_wake()
        # Give the machine a moment, then refresh state so the UI reflects it.
        await self.coordinator.async_request_refresh()
