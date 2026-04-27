"""Constants for the APsystems Local API integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)
DOMAIN = "apsystemsapi_local"
DEFAULT_PORT = 8050
UPDATE_INTERVAL = "update_interval"
BASE_PRODUCED_P1 = "base_produced_p1"
BASE_PRODUCED_P2 = "base_produced_p2"
DAILY_DEBOUNCE_P1 = "daily_debounce_p1"
DAILY_DEBOUNCE_P2 = "daily_debounce_p2"
DAILY_DEBOUNCE_LAST_P1 = "daily_debounce_last_p1"
DAILY_DEBOUNCE_LAST_P2 = "daily_debounce_last_p2"
DAILY_DEBOUNCE_DAY = "daily_debounce_day"
USE_API_V2 = "use_api_v2"
