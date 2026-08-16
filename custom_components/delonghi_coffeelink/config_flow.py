"""Config flow for De'Longhi Coffee Link."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coffeelink import REGIONS, AuthError, CoffeeLinkClient, CoffeeLinkError
from .const import CONF_DSN, CONF_MODEL, CONF_OEM_MODEL, DEFAULT_REGION, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION, default=DEFAULT_REGION): vol.In(list(REGIONS)),
    }
)


class CoffeeLinkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for De'Longhi Coffee Link."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = CoffeeLinkClient(
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                user_input[CONF_REGION],
            )
            try:
                await client.authenticate()
                devices = await client.async_get_devices()
            except AuthError:
                errors["base"] = "invalid_auth"
            except CoffeeLinkError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during setup")
                errors["base"] = "unknown"
            else:
                if not devices:
                    errors["base"] = "no_device"
                else:
                    device = devices[0]
                    dsn = device["dsn"]
                    await self.async_set_unique_id(dsn)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"De'Longhi {device.get('product_name') or dsn}",
                        data={
                            **user_input,
                            CONF_DSN: dsn,
                            CONF_MODEL: device.get("model"),
                            CONF_OEM_MODEL: device.get("oem_model"),
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
