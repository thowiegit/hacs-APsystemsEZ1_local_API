"""The read-only sensors for APsystems local API integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

from .APsystemsEZ1 import ReturnOutputData

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfEnergy, UnitOfFrequency, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType, StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ApSystemsConfigEntry, ApSystemsData, ApSystemsDataCoordinator
from .entity import ApSystemsEntity


@dataclass(frozen=True, kw_only=True)
class ApsystemsLocalApiSensorDescription(SensorEntityDescription):
    """Describes Apsystens Inverter sensor entity."""
    need_api_v2: bool = False
    value_fn: Callable[[ReturnOutputData], float | None]


SENSORS: tuple[ApsystemsLocalApiSensorDescription, ...] = (
    ApsystemsLocalApiSensorDescription(
        key="total_power",
        translation_key="total_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.p1 + c.p2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="total_power_p1",
        translation_key="total_power_p1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.p1,
    ),
    ApsystemsLocalApiSensorDescription(
        key="total_power_p2",
        translation_key="total_power_p2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: c.p2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="current_p1",
        translation_key="current_p1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        need_api_v2=True,
        value_fn=lambda c: c.c1,
    ),
    ApsystemsLocalApiSensorDescription(
        key="current_p2",
        translation_key="current_p2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        need_api_v2=True,
        value_fn=lambda c: c.c2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="voltage_p1",
        translation_key="voltage_p1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        need_api_v2=True,
        value_fn=lambda c: c.v1,
    ),
    ApsystemsLocalApiSensorDescription(
        key="voltage_p2",
        translation_key="voltage_p2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=3,
        need_api_v2=True,
        value_fn=lambda c: c.v2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="grid_frequency",
        translation_key="grid_frequency",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        need_api_v2=True,
        value_fn=lambda c: c.gf,
    ),
    ApsystemsLocalApiSensorDescription(
        key="grid_voltage",
        translation_key="grid_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        need_api_v2=True,
        value_fn=lambda c: c.gv,
    ),
    ApsystemsLocalApiSensorDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        need_api_v2=True,
        value_fn=lambda c: c.t,
    ),
    ApsystemsLocalApiSensorDescription(
        key="lifetime_production",
        translation_key="lifetime_production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.te1 + c.te2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="lifetime_production_p1",
        translation_key="lifetime_production_p1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.te1,
    ),
    ApsystemsLocalApiSensorDescription(
        key="lifetime_production_p2",
        translation_key="lifetime_production_p2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda c: c.te2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="today_production",
        translation_key="today_production",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda c: c.e1 + c.e2,
    ),
    ApsystemsLocalApiSensorDescription(
        key="today_production_p1",
        translation_key="today_production_p1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda c: c.e1,
    ),
    ApsystemsLocalApiSensorDescription(
        key="today_production_p2",
        translation_key="today_production_p2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=3,
        value_fn=lambda c: c.e2,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ApSystemsConfigEntry,
    add_entities: AddConfigEntryEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    config = config_entry.runtime_data

    add_e_list = []
    for desc in SENSORS:
        if (not desc.need_api_v2 or config.coordinator.use_api_v2):
            add_e_list.append( ApSystemsSensorWithDescription(data=config, entity_description=desc) )

    add_entities(add_e_list)



class ApSystemsSensorWithDescription(
    CoordinatorEntity[ApSystemsDataCoordinator], ApSystemsEntity, SensorEntity
):
    """Base sensor to be used with description."""

    entity_description: ApsystemsLocalApiSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        data: ApSystemsData,
        entity_description: ApsystemsLocalApiSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(data.coordinator)
        ApSystemsEntity.__init__(self, data)
        self.entity_description = entity_description
        self._attr_unique_id = f"{data.device_id}_{entity_description.key}"

    @property
    def native_value(self) -> StateType:
        """Return value of sensor."""
        return self.entity_description.value_fn(self.coordinator.data.output_data)
