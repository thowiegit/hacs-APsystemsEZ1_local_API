"""The output limit which can be set in the APsystems local API integration."""

from __future__ import annotations

from aiohttp import ClientConnectorError
import asyncio

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.util import timedelta

from .coordinator import ApSystemsConfigEntry, ApSystemsData
from .entity import ApSystemsEntity

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ApSystemsConfigEntry,
    add_entities: AddConfigEntryEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    add_entities([ApSystemsMaxOutputNumber(config_entry.runtime_data)], True)


class ApSystemsMaxOutputNumber(ApSystemsEntity, NumberEntity):
    """Base sensor to be used with description."""

    _attr_native_step = 1
    _attr_device_class = NumberDeviceClass.POWER
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_translation_key = "max_output"

    def __init__(
        self,
        data: ApSystemsData,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data)
        self._api = data.coordinator.api
        self._coordinator = data.coordinator
        # there is no own coordinator for numbers and switch, therefore they run with default from HA = 30 seconds. Nothing to control here.
        # This is good enough for these two values, therefore no further effort to this ...
        self._attr_unique_id = f"{data.device_id}_output_limit"
        self._attr_native_max_value = data.coordinator.api.max_power
        self._attr_native_min_value = data.coordinator.api.min_power

    async def async_update(self) -> None:
        """Set the state with the value fetched from the inverter."""

        _LOGGER.debug("Updating max output number...")
        counter: int = 0
        while self._coordinator.currently_running:
            await asyncio.sleep(0.8)  # Locking for poor people, but better than nothing...
            counter += 1  # usually we could stop updating, however maxout is rearly updated, therefore give it a little retry ..
            if counter > 4:  # After 3.2 seconds of waiting, give up
                _LOGGER.debug("Update already running, skipping max_power...")
                return # Skip update if coordinator is currently running an update

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates
            status = await self._api.get_max_power()
        except:
            _LOGGER.debug("Cannot update max power. Retry next cycle...")
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_native_value = status
        finally:
            self._coordinator.currently_running = False  # Reset running state on error

    async def async_set_native_value(self, value: float) -> None:
        """Set the desired output power."""
        counter: int = 0

        while self._coordinator.currently_running:
            await asyncio.sleep(1)  # Locking for poor people, but better than nothing...
            counter += 1
            if counter > 15:  # After 15 seconds of waiting, give up and raise an error
                _LOGGER.warning("Timeout while waiting for coordinator to be free. Aborting setting max power.")
                counter = 0
                return

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates
            self._attr_native_value = await self._api.set_max_power(int(value))
            self._attr_available = True
        except:
            _LOGGER.error("Error while setting max power.")
            self._attr_available = False
        finally:
            self._coordinator.currently_running = False  # Reset running state on error
