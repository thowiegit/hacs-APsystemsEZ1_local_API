"""The output limit which can be set in the APsystems local API integration."""

from __future__ import annotations

from aiohttp import ClientConnectorError
import asyncio

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import STATE_IDLE, STATE_OK, STATE_UNAVAILABLE, UnitOfPower
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
    if (config_entry.runtime_data.coordinator.use_api_v2):
        defaultMaxOutputEntity = ApSystemsDefaultMaxOutputNumber(config_entry.runtime_data)
        config_entry.runtime_data.slow_coordinator.setDefaultMaxOutPutEntity(defaultMaxOutputEntity)
        add_entities([maxOutputEntity, defaultMaxOutputEntity], False)  # we do not want this entity to be updated on start --> will immediately cause raise condition with switch, therefore False, no update before adding
    else:
        add_entities([maxOutputEntity], False)


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
        CoordinatorEntity.__init__(self, coordinator=data.slow_coordinator)
        ApSystemsEntity.__init__(self, data=data)
        self._api = data.coordinator.api
        self._coordinator = data.coordinator  # has the lock we need
        self._attr_unique_id = f"{data.device_id}_output_limit"
        self._attr_native_max_value = data.coordinator.api.max_power
        self._attr_native_min_value = data.coordinator.api.min_power

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._attr_available or self._coordinator.use_api_v2   # in case of api2 we keep this number active, since we store the value internally

    async def async_update(self) -> None:
        """Set the state with the value fetched from the inverter."""

        _LOGGER.debug("Updating max output number...")
        # locking is done by coordinator, nothing to do here

        try:
            status = await self._api.get_max_power()
        except:
            _LOGGER.debug("Exception update max power. Retry next cycle...")
            # self._attr_native_value = 800
            self._attr_available = False
        else:
            self._attr_available = True
            self._attr_native_value = status

    async def async_set_native_value(self, value: float) -> None:
        """Set the desired output power."""
        counter: int = 0

        while self._coordinator.currently_running:
            await asyncio.sleep(
                1
            )  # Locking for poor people, but better than nothing...
            counter += 1
            if counter > 15:  # After 15 seconds of waiting, give up and raise an error
                _LOGGER.warning(
                    "Timeout while waiting for coordinator to be free. Aborting setting max power."
                )
                counter = 0
                return

        try:
            self._coordinator.currently_running = (
                True  # Set coordinator to running state to prevent concurrent updates
            )
            self._attr_native_value = await self._api.set_max_power(int(value))
            self._attr_available = True
            self.async_write_ha_state()
        except:
            _LOGGER.error("Error while setting max power.")
            self._attr_available = False
        finally:
            self._coordinator.currently_running = False  # Reset running state on error


class ApSystemsDefaultMaxOutputNumber(CoordinatorEntity, ApSystemsEntity, NumberEntity):
    """Base sensor to be used with description."""

    _attr_native_step = 1
    _attr_device_class = NumberDeviceClass.POWER
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_translation_key = "default_max_output"

    def __init__(
        self,
        data: ApSystemsData,
    ) -> None:
        """Initialize the sensor."""
        CoordinatorEntity.__init__(self, coordinator=data.slow_coordinator)
        ApSystemsEntity.__init__(self, data=data)
        self._api = data.coordinator.api
        self._coordinator = data.coordinator  # has the lock we need
        self._attr_unique_id = f"{data.device_id}_default_output_limit"
        self._attr_native_max_value = data.coordinator.api.max_power
        self._attr_native_min_value = data.coordinator.api.min_power

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        return self._attr_available

    async def async_update(self) -> None:
        """Set the state with the value fetched from the inverter."""

        _LOGGER.debug("Updating default max output number...")
        # locking is done by coordinator, nothing to do here

        try:
            status = await self._api.get_default_max_power()
        except:
            _LOGGER.debug("Exception update default max power. Retry next cycle...")
            self._attr_available = False
        else:
            self._attr_native_value = status
            self._attr_available = True

    async def async_set_native_value(self, value: float) -> None:
        """Set the desired output power."""
        counter: int = 0

        while self._coordinator.currently_running:
            await asyncio.sleep(
                1
            )  # Locking for poor people, but better than nothing...
            counter += 1
            if counter > 15:  # After 15 seconds of waiting, give up and raise an error
                _LOGGER.warning(
                    "Timeout while waiting for coordinator to be free. Aborting setting default max power."
                )
                counter = 0
                return
        try:
            self._coordinator.currently_running =  True  # Set coordinator to running state to prevent concurrent updates
            self._attr_native_value = await self._api.set_default_max_power(int(value))
            self._attr_available = True
            self.async_write_ha_state()
        except:
            _LOGGER.error("Error while setting default max power.")
            self._attr_available = False
        finally:
            self._coordinator.currently_running = False  # Reset running state on error
