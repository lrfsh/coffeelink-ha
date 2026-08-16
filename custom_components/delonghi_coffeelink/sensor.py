"""Sensors for De'Longhi Coffee Link (read-only machine state + counters)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import CoffeeLinkCoordinator
from .entity import CoffeeLinkEntity


def _int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _dt(value: object):
    if not isinstance(value, str):
        return None
    return dt_util.parse_datetime(value)


@dataclass(frozen=True, kw_only=True)
class CoffeeLinkSensorDescription(SensorEntityDescription):
    """Sensor description with a value extractor over the coordinator data."""

    value_fn: Callable[[dict], StateType]


SENSORS: tuple[CoffeeLinkSensorDescription, ...] = (
    CoffeeLinkSensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:coffee-maker",
        device_class=SensorDeviceClass.ENUM,
        options=["on", "standby", "offline", "unknown"],
        value_fn=lambda d: (
            "offline" if not d.get("_online")
            else d.get("_monitor", {}).get("power_state", "unknown")
        ),
    ),
    CoffeeLinkSensorDescription(
        key="total_beverages",
        translation_key="total_beverages",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _int(d.get("d701_tot_bev_b")),
    ),
    CoffeeLinkSensorDescription(
        key="total_espresso",
        translation_key="total_espresso",
        icon="mdi:coffee",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _int(d.get("d704_tot_bev_espressi")),
    ),
    CoffeeLinkSensorDescription(
        key="total_cappuccino",
        translation_key="total_cappuccino",
        icon="mdi:coffee",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _int(d.get("d710_tot_id7_capp")),
    ),
    CoffeeLinkSensorDescription(
        key="coffee_grounds",
        translation_key="coffee_grounds",
        icon="mdi:delete-variant",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _int(d.get("d551_cnt_coffee_fondi")),
    ),
    CoffeeLinkSensorDescription(
        key="beverages_until_descale",
        translation_key="beverages_until_descale",
        icon="mdi:water-percent-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _int(d.get("d558_bev_cnt_desc_on")),
    ),
    CoffeeLinkSensorDescription(
        key="filters_used",
        translation_key="filters_used",
        icon="mdi:filter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: _int(d.get("d554_cnt_filter_tot")),
    ),
    CoffeeLinkSensorDescription(
        key="water_hardness",
        translation_key="water_hardness",
        icon="mdi:water",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _int(d.get("d556_water_hardness")),
    ),
    CoffeeLinkSensorDescription(
        key="connected_since",
        translation_key="connected_since",
        icon="mdi:clock-check-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: _dt(d.get("_connected_at")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CoffeeLinkCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CoffeeLinkSensor(coordinator, description) for description in SENSORS
    )


class CoffeeLinkSensor(CoffeeLinkEntity, SensorEntity):
    """A single read-only value from the machine."""

    entity_description: CoffeeLinkSensorDescription

    def __init__(
        self,
        coordinator: CoffeeLinkCoordinator,
        description: CoffeeLinkSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
