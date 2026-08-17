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
    entities = [
        CoffeeLinkPower(coordinator),
        CoffeeLinkOnline(coordinator),
        CoffeeLinkProblem(coordinator),
    ]
    entities += [
        CoffeeLinkAlarm(coordinator, key, bit, icon)
        for key, bit, icon in ALARM_SENSORS
    ]
    async_add_entities(entities)


# (translation_key, alarm bit, icon) — bit layout from the DlghIoT MonitorV2.
ALARM_SENSORS = [
    ("water_tank_empty", 0, "mdi:cup-water"),
    ("grounds_full", 1, "mdi:delete-alert"),
    ("descale_needed", 2, "mdi:coffee-maker"),
    ("filter_replace", 3, "mdi:air-filter"),
]


class CoffeeLinkAlarm(CoffeeLinkEntity, BinarySensorEntity):
    """A single maintenance alarm decoded from the monitor alarm bitfield."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: CoffeeLinkCoordinator, key: str, bit: int, icon: str) -> None:
        super().__init__(coordinator, key)
        self._attr_translation_key = key
        self._attr_icon = icon
        self._bit = bit

    @property
    def is_on(self) -> bool | None:
        monitor = (self.coordinator.data or {}).get("_monitor", {})
        alarms = monitor.get("alarms")
        if alarms is None:
            return None
        on = bool((alarms >> self._bit) & 1)
        if self._bit == 0:  # water tank: also flagged as "removed" via switch bit 4
            on = on or bool((monitor.get("switches", 0) >> 4) & 1)
        return on


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


class CoffeeLinkProblem(CoffeeLinkEntity, BinarySensorEntity):
    """On when the machine needs attention (water tank, grounds, tray, descale…)."""

    _attr_translation_key = "problem"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator: CoffeeLinkCoordinator) -> None:
        super().__init__(coordinator, "problem")

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("_monitor", {}).get("alarms"))

    @property
    def extra_state_attributes(self) -> dict:
        alarms = (self.coordinator.data or {}).get("_monitor", {}).get("alarms")
        return {"alarms": None if alarms is None else f"0x{alarms:08x}"}
