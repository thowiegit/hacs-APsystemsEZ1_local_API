"""The config_flow for APsystems local API integration."""

from typing import Any

from aiohttp.client_exceptions import ClientConnectionError

from homeassistant.helpers.storage import Store
from .APsystemsEZ1 import APsystemsEZ1M
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_PORT,
    DOMAIN,
    UPDATE_INTERVAL,
    BASE_PRODUCED_P1,
    BASE_PRODUCED_P2,
    DAILY_DEBOUNCE_P1,
    DAILY_DEBOUNCE_P2,
    USE_API_V2,
)

import logging

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(UPDATE_INTERVAL, default=15): int,
        vol.Optional(BASE_PRODUCED_P1): cv.string,  # due to a bug, we need to read here a string and convert later
        vol.Optional(BASE_PRODUCED_P2): cv.string,
        vol.Required(USE_API_V2, default=True): bool,
    }
)


class APsystemsLocalAPIFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Apsystems local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass, False)
            api = APsystemsEZ1M(
                ip_address=user_input[CONF_IP_ADDRESS],
                port=user_input.get(CONF_PORT, DEFAULT_PORT),
                session=session,
            )
            try:
                device_info = await api.get_device_info()
            except TimeoutError, ClientConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(device_info.deviceId)
                self._abort_if_unique_id_configured()

                # from info: Store is now a Generic class: self._store = Store[dict[str, int]](hass, STORAGE_VERSION, STORAGE_KEY)
                _store = Store[dict[str, float]](
                    self.hass, 1, f"{DOMAIN}_storage_{device_info.deviceId}"
                )
                _sData = await _store.async_load()
                try:
                    if _sData is not None:
                        _sData = {
                            # use stored values if no user input, however user input always overwrites stored values
                            BASE_PRODUCED_P1: float(user_input.get(BASE_PRODUCED_P1, _sData.get(BASE_PRODUCED_P1, 0))),
                            BASE_PRODUCED_P2: float(user_input.get(BASE_PRODUCED_P2, _sData.get(BASE_PRODUCED_P2, 0))),
                            DAILY_DEBOUNCE_P1: float(_sData.get(DAILY_DEBOUNCE_P1, 0)),
                            DAILY_DEBOUNCE_P2: float(_sData.get(DAILY_DEBOUNCE_P2, 0)),
                        }
                    else:
                        _sData = {
                            BASE_PRODUCED_P1: float(user_input.get(BASE_PRODUCED_P1, 0)),
                            BASE_PRODUCED_P2: float(user_input.get(BASE_PRODUCED_P2, 0)),
                        }
                    await _store.async_save(_sData)
                except ValueError:
                    errors[BASE_PRODUCED_P1] = (
                        "invalid value for base produced power. Must be a float number in kWh."
                    )
                    errors[BASE_PRODUCED_P2] = (
                        "invalid value for base produced power. Must be a float number in kWh."
                    )
                # await session.close() # seems HA do not like that
                else:
                    return self.async_create_entry(
                        title="Solar",
                        data=user_input,
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure step."""
        errors: dict[str, str] = {}

        # _LOGGER.info("Reconfigure called with user input: %s", user_input)

        if user_input is not None:
            session = async_get_clientsession(self.hass, False)
            api = APsystemsEZ1M(
                ip_address=user_input[CONF_IP_ADDRESS],
                port=user_input.get(CONF_PORT, DEFAULT_PORT),
                session=session,
            )
            try:
                device_info = await api.get_device_info()
            except TimeoutError, ClientConnectionError:
                errors["base"] = "cannot_connect"
            else:
                # await self.async_set_unique_id(device_info.deviceId)

                # from info: Store is now a Generic class: self._store = Store[dict[str, int]](hass, STORAGE_VERSION, STORAGE_KEY)
                _store = Store[dict[str, float]](
                    self.hass, 1, f"{DOMAIN}_storage_{device_info.deviceId}"
                )
                _sData = await _store.async_load()
                try:
                    if _sData is not None:
                        _sData = {
                            BASE_PRODUCED_P1: float(user_input.get(BASE_PRODUCED_P1, _sData.get(BASE_PRODUCED_P1, 0))),
                            BASE_PRODUCED_P2: float(user_input.get(BASE_PRODUCED_P2, _sData.get(BASE_PRODUCED_P2, 0))),
                            DAILY_DEBOUNCE_P1: float(_sData.get(DAILY_DEBOUNCE_P1, 0)),
                            DAILY_DEBOUNCE_P2: float(_sData.get(DAILY_DEBOUNCE_P2, 0)),
                        }
                    else:
                        _sData = {
                            BASE_PRODUCED_P1: float(user_input.get(BASE_PRODUCED_P1, 0)),
                            BASE_PRODUCED_P2: float(user_input.get(BASE_PRODUCED_P2, 0)),
                        }
                    await _store.async_save(_sData)
                except ValueError:
                    _LOGGER.error(
                        "Value error while parsing base produced power. User input must be a float number in kWh."
                    )
                    errors[BASE_PRODUCED_P1] = (
                        "invalid value for base produced power. Must be a float number in kWh."
                    )
                    errors[BASE_PRODUCED_P2] = (
                        "invalid value for base produced power. Must be a float number in kWh."
                    )
                else:
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(), data_updates=user_input
                    )

        ip_configured = self._get_reconfigure_entry().data.get(CONF_IP_ADDRESS, "")
        port_configured = self._get_reconfigure_entry().data.get(CONF_PORT, DEFAULT_PORT)
        update_interval_configured = self._get_reconfigure_entry().data.get(UPDATE_INTERVAL, 15)
        base_produced_p1_configured: float = self._get_reconfigure_entry().data.get(BASE_PRODUCED_P1, "")
        base_produced_p2_configured: float = self._get_reconfigure_entry().data.get(BASE_PRODUCED_P2, "")
        use_api_v2: bool = self._get_reconfigure_entry().data.get(USE_API_V2, True)

        session = async_get_clientsession(self.hass, False)
        api = APsystemsEZ1M(
            ip_address=ip_configured,
            port=port_configured,
            session=session,
        )
        device_info = None
        try:
            device_info = await api.get_device_info()
        except:
            pass  # we ignore here any errors, device info will be just none
        # await session.close() # seems HA do not like that

        # from info: Store is now a Generic class: self._store = Store[dict[str, int]](hass, STORAGE_VERSION, STORAGE_KEY)
        _store = Store[dict[str, float]](self.hass, 1, f"{DOMAIN}_storage_{device_info.deviceId}")
        _sData = await _store.async_load()
        if _sData is not None:
            base_produced_p1_configured = _sData.get(BASE_PRODUCED_P1, base_produced_p1_configured)
            base_produced_p2_configured = _sData.get(BASE_PRODUCED_P2, base_produced_p2_configured)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS, default=ip_configured): cv.string,
                    vol.Optional(CONF_PORT, default=port_configured): cv.port,
                    vol.Optional(
                        UPDATE_INTERVAL, default=update_interval_configured
                    ): int,
                    vol.Optional(
                        BASE_PRODUCED_P1, default=base_produced_p1_configured
                    ): cv.string,  # due to a bug, we need to read here a string and convert later
                    vol.Optional(
                        BASE_PRODUCED_P2, default=base_produced_p2_configured
                    ): cv.string,
                    #                       vol.Optional(BASE_PRODUCED_P1, default=base_produced_p1_configured): vol.Coerce(float),   do not work either
                    #                       vol.Optional(BASE_PRODUCED_P2, default=base_produced_p2_configured): vol.Coerce(float)
                    vol.Required(USE_API_V2, default=use_api_v2): bool,
                }
            ),
            errors=errors,
        )
