"""The output limit which can be set in the APsystems local API integration."""

from __future__ import annotations

from aiohttp import ClientConnectorError
import asyncio

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfPower
from homeassistant.core import DOMAIN, HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.util import timedelta
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

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

    maxOutputEntity = ApSystemsMaxOutputNumber(config_entry.runtime_data)
    config_entry.runtime_data.slow_coordinator.setMaxOutPutEntity(maxOutputEntity)
    add_entities([maxOutputEntity], True)


# class APSystemsNumberCoordinator(DataUpdateCoordinator):
#    """My custom coordinator."""
#
#    def __init__(
#        self,
#        hass: HomeAssistant,
#        config_entry,
#        update_interval,
#        data: ApSystemsData,
#        add_entities: AddConfigEntryEntitiesCallback,
#    ) -> None:
#        """Initialize my coordinator."""
#        super().__init__(
#            hass,
#            _LOGGER,
#            # Name of the data. For logging purposes.
#            name=DOMAIN,
#            config_entry=config_entry,
#            update_interval=update_interval,
#            always_update=True,
#        )
#        self._coord = data.coordinator
#        self._maxOutputNumber = ApSystemsMaxOutputNumber(self, data)
#        add_entities([self._maxOutputNumber], True)
#        _LOGGER.debug("APSystemsNumberCoordinator: Created...")
#
#    async def _async_setup(self):
#        """Handle initial setup tasks."""
#        _LOGGER.debug("APSystemsNumberCoordinator: _async_setup...")
#        pass
#
#    async def _async_update_data(self) -> None:
#        """Fetch data from API endpoint.
#
#        This is the place to pre-process the data to lookup tables
#        so entities can quickly look up their data.
#        """
#        _LOGGER.debug("APSystemsNumberCoordinator: Updating max output number...")
#        await self._maxOutputNumber.async_update()  # Update the max output number as part of the coordinator's update cycle



class ApSystemsMaxOutputNumber(CoordinatorEntity, ApSystemsEntity, NumberEntity):
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
        CoordinatorEntity.__init__(self,
            coordinator=data.slow_coordinator
        )
        ApSystemsEntity.__init__(self,
            data=data
        )
        self._api = data.coordinator.api
        self._coordinator = data.coordinator   # has the lock we need
        self._attr_unique_id = f"{data.device_id}_output_limit"
        self._attr_native_max_value = data.coordinator.api.max_power
        self._attr_native_min_value = data.coordinator.api.min_power

    async def async_update(self) -> None:
        """Set the state with the value fetched from the inverter."""

        _LOGGER.debug("Updating max output number...")
        # locking is done by coordinator, nothing to do here

        try:
            status = await self._api.get_max_power()
        except:
            _LOGGER.debug("Exception update max power. Retry next cycle...")
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_native_value = status

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
            self.async_write_ha_state()
        except:
            _LOGGER.error("Error while setting max power.")
            self._attr_available = False
        finally:
            self._coordinator.currently_running = False  # Reset running state on error
