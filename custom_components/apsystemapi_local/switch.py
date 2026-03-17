"""The power switch which can be toggled via the APsystems local API integration."""

from __future__ import annotations

from typing import Any
import asyncio

from aiohttp.client_exceptions import ClientConnectionError
from .APsystemsEZ1 import InverterReturnedError

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ApSystemsConfigEntry, ApSystemsData
from .entity import ApSystemsEntity

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ApSystemsConfigEntry,
    add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the switch platform."""

    add_entities([ApSystemsInverterSwitch(config_entry.runtime_data)], True)


class ApSystemsInverterSwitch(ApSystemsEntity, SwitchEntity):
    """The switch class for APSystems switches."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_translation_key = "inverter_status"

    def __init__(self, data: ApSystemsData) -> None:
        """Initialize the switch."""
        super().__init__(data)
        self._api = data.coordinator.api
        self._coordinator = data.coordinator
        self._attr_unique_id = f"{data.device_id}_inverter_status"
        if data.coordinator.battery_system:
            self._attr_available = False

    async def async_update(self) -> None:
        """Update switch status and availability."""
        _LOGGER.debug("Updating inverter switch...")
        counter: int = 0
        while self._coordinator.currently_running:
            await asyncio.sleep(0.9)  # Locking for poor people, but better than nothing...
            counter += 1  # usually we could stop updating, however switch status is rearly updated, therefore give it a little retry ..
            if counter > 4:  # After 3.6 seconds of waiting, give up
                _LOGGER.debug("Update already running, skipping switch...")
                return # Skip update if coordinator is currently running an update

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates
            status = await self._api.get_device_power_status()
        except:
            self._attr_available = False
            _LOGGER.info("Cannot update switch status. Retry next cycle...")
        else:
            self._attr_available = True
            self._attr_is_on = status
        finally:
            self._coordinator.currently_running = False  # Reset running state on error

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        counter: int = 0
        while self._coordinator.currently_running:
            await asyncio.sleep(1)  # Locking for poor people, but better than nothing...
            counter += 1
            if counter > 20:  # After 20 seconds of waiting, give up and raise an error
                _LOGGER.warning("Timeout while waiting for coordinator to be free. Aborting setting power on.")
                counter = 0
                return

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates
            await self._api.set_device_power_status(True)
            self._attr_available = True
            self._attr_is_on = True
        except:
            _LOGGER.error("Error while setting power on.")
        finally:
            self._coordinator.currently_running = False  # Reset running state on error

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""

        counter: int = 0
        while self._coordinator.currently_running:
            await asyncio.sleep(1)  # Locking for poor people, but better than nothing...
            counter += 1
            if counter > 20:  # After 20 seconds of waiting, give up and raise an error
                _LOGGER.warning("Timeout while waiting for coordinator to be free. Aborting setting power off.")
                counter = 0
                return

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates
            await self._api.set_device_power_status(False)
            self._attr_available = True
            self._attr_is_on = False
        except:
            _LOGGER.error("Error while setting power off.")
            self._attr_available = False
        finally:
            self._coordinator.currently_running = False  # Reset running state on error
