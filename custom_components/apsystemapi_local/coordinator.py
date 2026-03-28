"""The coordinator for APsystems local API integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from .APsystemsEZ1 import (
    APsystemsEZ1M,
    InverterReturnedError,
    ReturnAlarmInfo,
    ReturnOutputData,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .const import DOMAIN, LOGGER, BASE_PRODUCED_P1, BASE_PRODUCED_P2


import logging
_LOGGER = logging.getLogger(__name__)

@dataclass
class ApSystemsSensorData:
    """Representing different Apsystems sensor data."""
    output_data: ReturnOutputData
    alarm_info: ReturnAlarmInfo


@dataclass
class ApSystemsData:
    """Store runtime data."""
    coordinator: ApSystemsDataCoordinator
    device_id: str
    slow_coordinator: APSystemsSlowUpdateCoordinator

type ApSystemsConfigEntry = ConfigEntry[ApSystemsData]


from .number import ApSystemsMaxOutputNumber
from .switch import ApSystemsInverterSwitch

class APSystemsSlowUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
        update_interval: int,
        coordinator: ApSystemsDataCoordinator
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            # Name of the data. For logging purposes.
            name="APSystemsSlowData",
            config_entry=config_entry,
            update_interval=timedelta(seconds=update_interval),
            always_update=True,
        )
        self._coordinator = coordinator
        self._maxOutputNumber = None
        self._powerSwitch = None
        self._toggleCounter: int = 0
        _LOGGER.debug("APSystemsSlowCoordinator: Created...")

    def setMaxOutPutEntity(self, maxOutPut: ApSystemsMaxOutputNumber):
        """Defines max output entity."""
        self._maxOutputNumber = maxOutPut

    def setPowerSwitchEntity(self, powerSwitch: ApSystemsInverterSwitch):
        """Defines power switch entity."""
        self._powerSwitch = powerSwitch

    async def _async_setup(self):
        """Handle initial setup tasks."""
        _LOGGER.debug("APSystemsSlowCoordinator: _async_setup...")
        pass

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.debug("APSystemsSlowCoordinator: Updating ...")

        if self._maxOutputNumber is None:
            _LOGGER.warning("APSystemsSlowCoordinator: No max output entity!")
            return
        if self._powerSwitch is None:
            _LOGGER.warning("APSystemsSlowCoordinator: No power switch entity!")
            return

        counter: int = 0
        while self._coordinator.currently_running:
            await asyncio.sleep(0.7)  # Locking for poor people, but better than nothing...
            counter += 1  # usually we could stop updating, however maxout is rearly updated, therefore give it a little retry ..
            if counter > 4:  # After 2.8 seconds of waiting, give up
                _LOGGER.debug("Update already running, skipping slow data...")
                return # Skip update if coordinator is currently running an update

        try:
            self._coordinator.currently_running = True  # Set coordinator to running state to prevent concurrent updates

            if (self._toggleCounter%2==1):
                await self._maxOutputNumber.async_update()  # Update the max output number as part of the coordinator's update cycle
            else:
                await self._powerSwitch.async_update()

            self._toggleCounter+=1
        except:
            _LOGGER.debug("Exception while update slow data. Retry next cycle...")
        finally:
            self._coordinator.currently_running = False  # Reset running state on error


class ApSystemsDataCoordinator(DataUpdateCoordinator[ApSystemsSensorData]):
    """Coordinator used for all sensors."""

    config_entry: ApSystemsConfigEntry
    device_version: str
    battery_system: bool

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ApSystemsConfigEntry,
        api: APsystemsEZ1M,
        interval: int = 5,
        base_produced_p1: float = 0,
        base_produced_p2: float = 0,
        _store: Store[dict[str, float]] = None
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name="APSystems Data",
            update_interval=timedelta(seconds=interval),
        )
        self.api = api
        self.base_produced_p1 = base_produced_p1
        self.base_produced_p2 = base_produced_p2
        self.last_tp1: float = 0
        self.last_tp2: float = 0
        self.retrycounter: int = 0
        self._store = _store
        self.updateCounter: int = 0
        self.old_output_data = ReturnOutputData(
            p1=0,
            e1=10,
            te1=20,
            p2=0,
            e2=11,
            te2=22
        )
        self.old_alarm_info = ReturnAlarmInfo(
                offgrid=False,
                shortcircuit_1=False,
                shortcircuit_2=False,
                operating=True
        )
        self.currently_running: bool = False

    async def _async_setup(self) -> None:
        retry: int = 5
        while retry > 0:
            try:
                device_info = await self.api.get_device_info()
                retry = 0  # reset retry counter on success

            except:
                if retry <= 0:
                    raise UpdateFailed from None
                await asyncio.sleep(2)  # Add a short delay before retrying

        self.api.max_power = device_info.maxPower
        self.api.min_power = device_info.minPower
        self.device_version = device_info.devVer
        self.battery_system = device_info.isBatterySystem

    async def _async_update_data(self) -> ApSystemsSensorData:
        # _LOGGER.info("Starting data update...")
        if self.currently_running:
            _LOGGER.debug("Update already running, skipping outvalues and alarm info, using old data...")
            return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
        try:
            self.currently_running = True
            if (self.retrycounter>7) and ((self.retrycounter % 5) != 0):
                # After 7 unavailable cycles, reduce update rate, since micro inverter is very likely off and cannot response anyhow.
                self.retrycounter += 1
                return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
            output_data = await self.api.get_output_data()
            self.updateCounter += 1
            resetDetected:bool = False
            if (output_data.te1 < (self.last_tp1-100)):
                # This means that the inverter has been reset, so we update the base produced values
                self.base_produced_p1 += self.last_tp1
                resetDetected = True
            elif (output_data.te1 < self.last_tp1):
                # inverter rounding issue, ignore this value and use old one
                output_data.te1 = self.last_tp1
            else:
                self.last_tp1 = output_data.te1
            if (output_data.te2 < (self.last_tp2-100)):
                # This means that the inverter has been reset, so we update the base produced values
                self.base_produced_p2 += self.last_tp2
                resetDetected = True
            elif (output_data.te2 < self.last_tp2):
                # inverter rounding issue, ignore this value and use old one
                output_data.te2 = self.last_tp2
            else:
                self.last_tp2 = output_data.te2

            if (resetDetected and self._store is not None):
                _sData =  {
                    BASE_PRODUCED_P1: self.base_produced_p1,
                    BASE_PRODUCED_P2: self.base_produced_p2
                }
                await self._store.async_save(_sData)

            output_data.te1 += self.base_produced_p1
            output_data.te2 += self.base_produced_p2
            self.old_output_data = output_data

            if (self.updateCounter % 5 == 0):
                alarm_info = await self.api.get_alarm_info()
                self.old_alarm_info = alarm_info
            else:
                alarm_info = self.old_alarm_info

        except InverterReturnedError:
            self.retrycounter += 1
            if (self.retrycounter > 7):
                # After 7 unavailable cycles, micro inverter is off, prevent further logs, they are useless
                self.old_output_data.p1 = 0
                self.old_output_data.p2 = 0
                _LOGGER.debug("Inverter returned an error, returning modified old data... (retrycounter: %d)", self.retrycounter)
                return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
            elif (self.retrycounter > 5):
                _LOGGER.debug("Inverter returned an error, raising exception... (retrycounter: %d)", self.retrycounter)
                raise UpdateFailed(
                    translation_domain=DOMAIN, translation_key="inverter_error"
                ) from None
            else:
                # Otherwise we return old data
                _LOGGER.debug("Inverter returned an error, returning old data... (retrycounter: %d)", self.retrycounter)
                return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
        finally:
            self.currently_running = False

        self.retrycounter = 0
        # _LOGGER.info("  .. Ending data update")
        return ApSystemsSensorData(output_data=output_data, alarm_info=alarm_info)
