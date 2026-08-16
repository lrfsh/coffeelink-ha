"""Binary sensors for De'Longhi Coffee Link."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    async_add_entities(
        [CoffeeLinkPower(coordinator), CoffeeLinkOnline(coordinator)]
    )


class CoffeeLinkPower(CoffeeLinkEntity, BinarySensorEntity):
    """On while the machine is powered on (ready or heating)."""

    _attr_translation_key = "power"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:power"

    def __init__(self, coordinator: CoffeeLinkCoordinator) -> None:
        super().__init__(coordinator, "power")

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        return data.get("_monitor", {}).get("power_state") == "on"


class CoffeeLinkOnline(CoffeeLinkEntity, BinarySensorEntity):
    """Ayla cloud connectivity of the machine."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = None

    def __init__(self, coordinator: CoffeeLinkCoordinator) -> None:
        super().__init__(coordinator, "online")

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("_online"))
