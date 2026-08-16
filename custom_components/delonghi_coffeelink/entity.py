"""Base entity for De'Longhi Coffee Link."""
from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoffeeLinkCoordinator


class CoffeeLinkEntity(CoordinatorEntity[CoffeeLinkCoordinator]):
    """Common base: ties every entity to the one coffee-machine device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CoffeeLinkCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.dsn}_{key}"
        sw_version = None
        if coordinator.data:
            sw = coordinator.data.get("software_version")
            if isinstance(sw, str):
                sw_version = sw
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.dsn)},
            manufacturer="De'Longhi",
            name="Coffee machine",
            model=getattr(coordinator, "model", None) or "Coffee Link",
            serial_number=coordinator.dsn,
            sw_version=sw_version,
        )
