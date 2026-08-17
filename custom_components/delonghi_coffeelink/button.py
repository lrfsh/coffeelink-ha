"""Buttons for De'Longhi Coffee Link."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coffeelink import BEVERAGES
from .const import DOMAIN
from .coordinator import CoffeeLinkCoordinator
from .entity import CoffeeLinkEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CoffeeLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list = [CoffeeLinkWakeButton(coordinator)]
    entities += [
        CoffeeLinkBrewButton(coordinator, bev_id, key, name, icon)
        for bev_id, key, name, icon in BEVERAGES
    ]
    async_add_entities(entities)


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


class CoffeeLinkBrewButton(CoffeeLinkEntity, ButtonEntity):
    """Start a beverage (EXPERIMENTAL — validate on a real brew)."""

    def __init__(self, coordinator: CoffeeLinkCoordinator, beverage_id: int,
                 key: str, name: str, icon: str) -> None:
        super().__init__(coordinator, f"brew_{key}")
        self._beverage_id = beverage_id
        self._attr_name = name
        self._attr_icon = icon

    async def async_press(self) -> None:
        await self.coordinator.client.async_brew(self._beverage_id)
        await self.coordinator.async_request_refresh()
