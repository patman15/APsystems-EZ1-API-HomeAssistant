from __future__ import annotations

import asyncio

from aiohttp import client_exceptions

import voluptuous as vol

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    PLATFORM_SCHEMA
)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from APsystemsEZ1 import APsystemsEZ1M
from .const import DOMAIN, CONF_COORDINATOR
from homeassistant.helpers.device_registry import DeviceInfo

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default="solar"): cv.string
})


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    api = config[CONF_COORDINATOR]._api

    numbers = [
        MaxPower(api, device_name=config[CONF_NAME], sensor_name="Max Output Power", sensor_id="max_output_power")
    ]

    add_entities(numbers, True)


class MaxPower(NumberEntity):
    _attr_device_class = NumberDeviceClass.POWER
    _attr_available = False
    _attr_native_max_value = 800
    _attr_native_min_value = 30
    _attr_native_step = 1

    def __init__(self, api: APsystemsEZ1M, device_name: str, sensor_name: str, sensor_id: str):
        """Initialize the sensor."""
        self._api = api
        self._state = None
        self._device_name = device_name
        self._name = sensor_name
        self._sensor_id = sensor_id

    async def async_update(self):
        try:
            self._state = await self._api.get_max_power()
            self._attr_available = True
        except (client_exceptions.ClientConnectionError, asyncio.TimeoutError):
            self._attr_available = False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self) -> str | None:
        return f"apsystemsapi_{self._device_name}_{self._sensor_id}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"APsystems {self._device_name} {self._name}"

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self._api.set_max_power(int(value))
            self._attr_available = True
        except (client_exceptions.ClientConnectionError, asyncio.TimeoutError):
            self._attr_available = False

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                ("apsystemsapi_local", self._device_name)
            },
            name=self._device_name,
            manufacturer="APsystems",
            model="EZ1-M",
        )
