from __future__ import annotations

import asyncio

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import client_exceptions
from APsystemsEZ1 import APsystemsEZ1M
from homeassistant import config_entries

from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
    ATTR_VOLTAGE,
    UnitOfEnergy,
    UnitOfPower,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import EZ1Coordinator
from .const import DOMAIN, LOGGER, CONF_COORDINATOR

SENSOR_TYPES: list[SensorEntityDescription] = [
    SensorEntityDescription(
        key="power",
        translation_key="power",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="p1",
        translation_key="p1",
        name="Power channel 1",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="p2",
        translation_key="p2",
        name="Power channel 2",
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="energy_counter",
        translation_key="energy_counter",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="te1",
        translation_key="te1",
        name="Energy channel 1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="te2",
        translation_key="te2",
        name="Energy channel 2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="energy_counter_daily",
        translation_key="energy_counter_daily",
        name="Energy today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="e1",
        translation_key="e1",
        name="Energy today channel 1",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
    SensorEntityDescription(
        key="e2",
        translation_key="e2",
        name="Energy today channel 2",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.ENERGY,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    LOGGER.debug(f"Setup entry {config_entry.title}")
    config = hass.data[DOMAIN][config_entry.entry_id]
    device: EZ1Coordinator = config[CONF_COORDINATOR]

    for descr in SENSOR_TYPES:
        async_add_entities([BaseSensor(device, descr)])


class BaseSensor(CoordinatorEntity[EZ1Coordinator], SensorEntity):  # type: ignore
    """Representation of an APsystem sensor."""

    def __init__(self, device: EZ1Coordinator, descr: SensorEntityDescription):
        """Initialize the sensor."""
        LOGGER.debug(f"Init sensor {descr.key}")
        self._device: EZ1Coordinator = device
        self._attr_device_info = self._device.device_info
        self._attr_unique_id = f"{self._attr_device_info.get(CONF_NAME)}-{descr.key}"
        self._attr_has_entity_name = True
        self._attr_available = False
        self.entity_description = descr
        super().__init__(self._device)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if self._device.data is None:
            return

        if self.entity_description.key in self._device.data:
            self._attr_native_value = self._device.data.get(self.entity_description.key)
            self._attr_available = True
        elif self._attr_available:
            self._attr_available = False
            self._device.logger.info(
                f"No update available for {self.entity_description.key}."
            )

        self.async_write_ha_state()
