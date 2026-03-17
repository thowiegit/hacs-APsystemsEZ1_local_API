"""The APsystems local API integration."""

from __future__ import annotations

import logging

from .APsystemsEZ1 import APsystemsEZ1M

from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, Platform
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DEFAULT_PORT, DOMAIN, UPDATE_INTERVAL, BASE_PRODUCED_P1, BASE_PRODUCED_P2, LOGGER
from .coordinator import ApSystemsConfigEntry, ApSystemsData, ApSystemsDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


class StoreApsystemsData:
    """Store persistent data."""

    def __init__(
        self,
        total_produced_port1: float,
        total_produced_port2: float,
    ) -> None:
        self.total_produced_p1: float = total_produced_port1
        self.total_produced_p2: float = total_produced_port2


async def async_setup_entry(hass: HomeAssistant, entry: ApSystemsConfigEntry) -> bool:
    """Set up this integration using UI."""
    api = APsystemsEZ1M(
        ip_address=entry.data[CONF_IP_ADDRESS],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        timeout=4,
        enable_debounce=True,
    )

    assert entry.unique_id

    # from info: Store is now a Generic class: self._store = Store[dict[str, int]](hass, STORAGE_VERSION, STORAGE_KEY)
    _store = Store[dict[str, float]](hass, 1, f"{DOMAIN}_storage_{entry.unique_id}")
    _LOGGER.info("Unique ID: %s", entry.unique_id)

    _rData = await _store.async_load()
    bp_p1=0
    bp_p2=0
    if _rData is not None:
        # if there is stored data use it, otherwise use configured ones from config flow, is 0 if not provided
        bp_p1 = _rData.get(BASE_PRODUCED_P1, 0)
        bp_p2 = _rData.get(BASE_PRODUCED_P2, 0)
        _LOGGER.info("Loaded data from storage: %s, p1: %f, p2: %f", _rData, _rData[BASE_PRODUCED_P1], _rData[BASE_PRODUCED_P2])
    else:
        bp_p1 = entry.data.get(BASE_PRODUCED_P1, 0)
        bp_p2 = entry.data.get(BASE_PRODUCED_P2, 0)
        _LOGGER.info("No data found in storage, using defaults: p1: %f, p2: %f", bp_p1, bp_p2)

    coordinator = ApSystemsDataCoordinator(hass, entry, api, interval=entry.data.get(UPDATE_INTERVAL, 15),
                        base_produced_p1=bp_p1, base_produced_p2=bp_p2, _store=_store)

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = ApSystemsData(
        coordinator=coordinator, device_id=entry.unique_id
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ApSystemsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
