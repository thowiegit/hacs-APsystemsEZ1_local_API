"""The coordinator for APsystems local API integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from .APsystemsEZ1 import (
    APsystemsEZ1M,
    InverterReturnedError,
    ReturnAlarmInfo,
    ReturnDetailedOutputData,
    ReturnOutputData,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER, BASE_PRODUCED_P1, BASE_PRODUCED_P2, DAILY_DEBOUNCE_P1, DAILY_DEBOUNCE_P2


import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class ApSystemsSensorData:
    """Representing different Apsystems sensor data."""

    output_data: ReturnDetailedOutputData
    alarm_info: ReturnAlarmInfo


@dataclass
class ApSystemsData:
    """Store runtime data."""

    coordinator: ApSystemsDataCoordinator
    device_id: str
    slow_coordinator: APSystemsSlowUpdateCoordinator


type ApSystemsConfigEntry = ConfigEntry[ApSystemsData]

"""
# for information class is not actually used
class StoreApsystemsData:
    ""Store persistent data.""

    def __init__(
        self,
        total_produced_port1: float,
        total_produced_port2: float,
        day_produced_port1: float,
        day_produced_port2: float,
    ) -> None:
        self.total_produced_p1: float = total_produced_port1
        self.total_produced_p2: float = total_produced_port2
        self.day_produced_p1: float = day_produced_port1
        self.day_produced_p2: float = day_produced_port2
"""


from .number import ApSystemsMaxOutputNumber
from .number import ApSystemsDefaultMaxOutputNumber
from .switch import ApSystemsInverterSwitch


class APSystemsSlowUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry,
        update_interval: int,
        coordinator: ApSystemsDataCoordinator,
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
        self._defaultMaxOutputNumber = None
        self._powerSwitch = None
        self._toggleCounter: int = 0
        _LOGGER.debug("APSystemsSlowCoordinator: Created...")

    def setMaxOutPutEntity(self, maxOutPut: ApSystemsMaxOutputNumber):
        """Defines max output entity."""
        self._maxOutputNumber = maxOutPut

    def setDefaultMaxOutPutEntity(self, defaultMaxOutPut: ApSystemsDefaultMaxOutputNumber):
        """Defines default max output entity."""
        self._defaultMaxOutputNumber = defaultMaxOutPut

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
            await asyncio.sleep(
                0.7
            )  # Locking for poor people, but better than nothing...
            counter += 1  # usually we could stop updating, however maxout is rearly updated, therefore give it a little retry ..
            if counter > 4:  # After 2.8 seconds of waiting, give up
                _LOGGER.debug("Update already running, skipping slow data...")
                return  # Skip update if coordinator is currently running an update

        try:
            self._coordinator.currently_running = (
                True  # Set coordinator to running state to prevent concurrent updates
            )

            if (self._toggleCounter % 3 == 1) or (self._maxOutputNumber.native_value is None):
                await self._maxOutputNumber.async_update()  # Update the max output number as part of the coordinator's update cycle
            if (self._toggleCounter % 3 == 2) or (self._defaultMaxOutputNumber is not None and self._defaultMaxOutputNumber.native_value is None):
                if self._defaultMaxOutputNumber is not None:
                    await self._defaultMaxOutputNumber.async_update()  # Update the default max output number as part of the coordinator's update cycle
            if (self._toggleCounter % 3 == 0) or (self._powerSwitch.is_on is None):
                await self._powerSwitch.async_update()

            self._toggleCounter += 1
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
        use_api_v2: bool = True,
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
        self.base_produced_p1: float = base_produced_p1
        self.base_produced_p2: float = base_produced_p2
        self.base_day_p1: float = 0
        self.base_day_p2: float = 0
        self.last_tp1: float = 0
        self.last_tp2: float = 0
        self.last_dayp1: float = 0
        self.last_dayp2: float = 0
        self.last_update_day = 0
        self.retrycounter: int = 0
        # from info: Store is now a Generic class: self._store = Store[dict[str, int]](hass, STORAGE_VERSION, STORAGE_KEY)
        self._store = Store[dict[str, float]](self.hass, 1, f"{DOMAIN}_storage_{self.config_entry.unique_id}")
        self.updateCounter: int = 0
        self.old_output_data = ReturnDetailedOutputData(
            c1=0, v1=0, p1=0, e1=10, te1=11, c2=0, v2=0, p2=0, e2=20, te2=22, gf=0, gv=0, t=0
        )
        self.old_alarm_info = ReturnAlarmInfo(
            offgrid=False, shortcircuit_1=False, shortcircuit_2=False, operating=True
        )
        self.use_api_v2 = use_api_v2
        self.currently_running: bool = False

    async def _async_setup(self) -> None:
        retry: int = 5
        device_info = None
        while retry > 0:
            try:
                device_info = await self.api.get_device_info()
                retry = 0  # reset retry counter on success to exit loop
            except:
                retry -= 1
                _LOGGER.debug("Exception while fetching device info. Retries left: %d", retry)
                if retry <= 0:
                   raise UpdateFailed from None  # we cannot start if device is unavailable, therefore stop init (HA will retry later)
                await asyncio.sleep(2)  # Add a short delay before retrying

        # we default to known values, will be overwritten, when device is available.
        # if device was not available, at least we prevent crashes...
        self.device_version = None
        self.battery_system = False
        self.api.max_power = 800
        self.api.min_power = 30
        if device_info:
            self.api.max_power = device_info.maxPower
            self.api.min_power = device_info.minPower
            self.device_version = device_info.devVer
            self.battery_system = device_info.isBatterySystem

        _LOGGER.info("Unique ID: %s", self.config_entry.unique_id)
        _rData = await self._store.async_load()
        if _rData is not None:
            # if there is stored data use it, otherwise use configured ones from config flow, is 0 if not provided
            self.base_produced_p1 = _rData.get(BASE_PRODUCED_P1, self.base_produced_p1)
            self.base_produced_p2 = _rData.get(BASE_PRODUCED_P2, self.base_produced_p2)
            self.base_day_p1 = _rData.get(DAILY_DEBOUNCE_P1, 0)
            self.base_day_p2 = _rData.get(DAILY_DEBOUNCE_P2, 0)
            _LOGGER.info("Loaded data from storage: %s, p1: %f, p2: %f, day_p1: %f, day_p2: %f",
                _rData, self.base_produced_p1, self.base_produced_p2, self.base_day_p1, self.base_day_p2)
        self.last_update_day = dt_util.now().day


    async def _async_update_data(self) -> ApSystemsSensorData:
        # _LOGGER.info("Starting data update...")
        if self.currently_running:
            _LOGGER.debug("Update already running, skipping outvalues and alarm info, using old data...")
            return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
        try:
            self.currently_running = True
            if (self.retrycounter > 7) and ((self.retrycounter % 5) != 0):
                # After 7 unavailable cycles, reduce update rate, since micro inverter is very likely off and cannot response anyhow.
                self.retrycounter += 1
                return ApSystemsSensorData(output_data=self.old_output_data, alarm_info=self.old_alarm_info)
            if self.use_api_v2:
                output_data = await self.api.get_detailed_output_data()
            else:
                output_data = await self.api.get_output_data()
            self.updateCounter += 1
            resetDetected: bool = False
            # 1st check total values
            if output_data.te1 < (self.last_tp1 - 100):
                # This means that the inverter has been reset, so we update the base produced values
                self.base_produced_p1 += self.last_tp1
                self.last_tp1 = output_data.te1  # reset last_tp1 to prevent further reset detections due to old value
                resetDetected = True
            elif output_data.te1 < self.last_tp1:
                # inverter rounding issue, ignore this value and use old one
                output_data.te1 = self.last_tp1
            else:
                self.last_tp1 = output_data.te1
            if output_data.te2 < (self.last_tp2 - 100):
                # This means that the inverter has been reset, so we update the base produced values
                self.base_produced_p2 += self.last_tp2
                self.last_tp2 = output_data.te2  # reset last_tp2 to prevent further reset detections due to old value
                resetDetected = True
            elif output_data.te2 < self.last_tp2:
                # inverter rounding issue, ignore this value and use old one
                output_data.te2 = self.last_tp2
            else:
                self.last_tp2 = output_data.te2

            # 2nd check day values - start with day reset check
            if (self.last_update_day != dt_util.now().day):
                self.last_update_day = dt_util.now().day
                if output_data.e1 < (self.last_dayp1 - 0.0003): self.last_dayp1 = output_data.e1 # if the day reset by chance happens exactly at the day reset, we need to update the last_dayp1 to prevent false reset value
                if output_data.e2 < (self.last_dayp2 - 0.0003): self.last_dayp2 = output_data.e2
                self.base_day_p1 = -self.last_dayp1  # we need to substract startvalue of daystart to start with a 0 at 00:00
                self.base_day_p2 = -self.last_dayp2
                resetDetected = True
            else:
                if output_data.e1 < (self.last_dayp1 - 0.0003):  # we assume a day production is bigger than 0.0003 kWh, if not detection will fail. But this is no further issue
                    # This means that the day production has been reset, so we update the base day produced values
                    self.base_day_p1 += self.last_dayp1
                    self.last_dayp1 = output_data.e1  # reset last_dayp1 to prevent further reset detections due to old value
                    resetDetected = True
                elif output_data.e1 < self.last_dayp1:
                    # inverter rounding issue, ignore this value and use old one
                    output_data.e1 = self.last_dayp1
                else:
                    self.last_dayp1 = output_data.e1
                if output_data.e2 < (self.last_dayp2 - 0.0003):
                    # This means that the day production has been reset, so we update the base day produced values
                    self.base_day_p2 += self.last_dayp2
                    self.last_dayp2 = output_data.e2  # reset last_dayp2 to prevent further reset detections due to old value
                    resetDetected = True
                elif output_data.e2 < self.last_dayp2:
                    # inverter rounding issue, ignore this value and use old one
                    output_data.e2 = self.last_dayp2
                else:
                    self.last_dayp2 = output_data.e2

            if resetDetected and self._store is not None:
                _sData = {
                    BASE_PRODUCED_P1: self.base_produced_p1,
                    BASE_PRODUCED_P2: self.base_produced_p2,
                    DAILY_DEBOUNCE_P1: self.base_day_p1,
                    DAILY_DEBOUNCE_P2: self.base_day_p2,
                }
                await self._store.async_save(_sData)

            output_data.te1 += self.base_produced_p1
            output_data.te2 += self.base_produced_p2
            output_data.e1 += self.base_day_p1
            output_data.e2 += self.base_day_p2
            self.old_output_data = output_data

            if self.updateCounter % 5 == 0:
                alarm_info = await self.api.get_alarm_info()
                self.old_alarm_info = alarm_info
            else:
                alarm_info = self.old_alarm_info

        except InverterReturnedError:
            self.retrycounter += 1
            if self.retrycounter > 7:
                # After 7 unavailable cycles, micro inverter is off, prevent further logs, they are useless
                self.old_output_data.c1 = 0
                self.old_output_data.v1 = 0
                self.old_output_data.p1 = 0
                self.old_output_data.c2 = 0
                self.old_output_data.v2 = 0.123  # just for indication we are in unavailable state
                self.old_output_data.p2 = 0
                self.old_output_data.gf = 50.0123  # just for indication we are in unavailable state
                if (self.last_update_day != dt_util.now().day):
                    # no --> self.last_update_day = dt_util.now().day   Do not save it, the real correction still needs to be done..
                    self.old_output_data.e1 = 0  # there is the day change during inverter off, so reset day production
                    self.old_output_data.e2 = 0  # However we do not set any last values, because when inverter aways in the morning the actual correction values will be calculated (we cannot know yet)
                _LOGGER.debug("Inverter returned an error, returning modified old data... (retrycounter: %d)", self.retrycounter)
                return ApSystemsSensorData(
                    output_data=self.old_output_data, alarm_info=self.old_alarm_info
                )
            elif self.retrycounter > 5:
                _LOGGER.debug(
                    "Inverter returned an error, raising exception... (retrycounter: %d)",
                    self.retrycounter,
                )
                raise UpdateFailed(
                    translation_domain=DOMAIN, translation_key="inverter_error"
                ) from None
            else:
                # Otherwise we return old data
                _LOGGER.debug(
                    "Inverter returned an error, returning old data... (retrycounter: %d)",
                    self.retrycounter,
                )
                return ApSystemsSensorData(
                    output_data=self.old_output_data, alarm_info=self.old_alarm_info
                )
        finally:
            self.currently_running = False

        self.retrycounter = 0
        # _LOGGER.info("  .. Ending data update")
        return ApSystemsSensorData(output_data=output_data, alarm_info=alarm_info)
