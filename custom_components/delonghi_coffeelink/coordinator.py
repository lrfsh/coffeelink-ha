"""DataUpdateCoordinator for De'Longhi Coffee Link.

Polls the machine's Ayla properties and keeps the access token alive (refresh
token, falling back to a full re-login). This is why no external cron is needed.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .coffeelink import AuthError, CoffeeLinkClient, CoffeeLinkError, decode_monitor
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CoffeeLinkCoordinator(DataUpdateCoordinator[dict]):
    """Fetch machine state on an interval, refreshing the token as needed."""

    def __init__(self, hass: HomeAssistant, client: CoffeeLinkClient, dsn: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.dsn = dsn
        self.model: str | None = None

    async def _async_update_data(self) -> dict:
        try:
            device = await self.client.async_get_device()
            props = await self.client.async_get_properties()
        except AuthError as err:
            # Bad/expired credentials -> trigger the HA reauth flow.
            raise ConfigEntryAuthFailed(str(err)) from err
        except CoffeeLinkError as err:
            raise UpdateFailed(str(err)) from err

        props["_online"] = str(device.get("connection_status", "")).lower() == "online"
        props["_connected_at"] = device.get("connected_at")
        props["_monitor"] = decode_monitor(props.get("d302_monitor_machine"))
        return props
