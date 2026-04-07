"""The APsystems local API integration."""

from __future__ import annotations

import logging

from .APsystemsEZ1 import APsystemsEZ1M

from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, Platform
from homeassistant.core import _LOGGER, HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DEFAULT_PORT,
    DOMAIN,
    UPDATE_INTERVAL,
    BASE_PRODUCED_P1,
    BASE_PRODUCED_P2,
    USE_API_V2,
)
from .coordinator import (
    ApSystemsConfigEntry,
    ApSystemsData,
    ApSystemsDataCoordinator,
    APSystemsSlowUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

async def async_setup_entry(hass: HomeAssistant, entry: ApSystemsConfigEntry) -> bool:
    """Set up this integration using UI."""
    api = APsystemsEZ1M(
        ip_address=entry.data[CONF_IP_ADDRESS],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
        timeout=4,
        enable_debounce=False,
    )

    assert entry.unique_id

    bp_p1 = float(entry.data.get(BASE_PRODUCED_P1, 0))
    bp_p2 = float(entry.data.get(BASE_PRODUCED_P2, 0))
    use_api_v2 = bool(entry.data.get(USE_API_V2, True))
    _LOGGER.info("Configured values for base: p1: %f, p2: %f, use_api_v2: %s", bp_p1, bp_p2, use_api_v2)

    coordinator = ApSystemsDataCoordinator(
        hass,
        entry,
        api,
        interval=entry.data.get(UPDATE_INTERVAL, 15),
        base_produced_p1=bp_p1,
        base_produced_p2=bp_p2,
        use_api_v2=use_api_v2,
    )
    await coordinator.async_config_entry_first_refresh()

    # Not defining an own coordinator seems to make HA GUI very unresponsive, since we need to do a lot of retries and waits, therefore we added our own coordinator
    # even for the slow updates.
    slowcoord = APSystemsSlowUpdateCoordinator(hass, entry, 24, coordinator)
    entry.runtime_data = ApSystemsData(
        coordinator=coordinator, device_id=entry.unique_id, slow_coordinator=slowcoord
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ApSystemsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
