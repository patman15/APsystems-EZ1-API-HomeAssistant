from __future__ import annotations
from aiohttp import client_exceptions

import voluptuous as vol

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
    PLATFORM_SCHEMA
)
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from APsystemsEZ1 import APsystemsEZ1M, Status
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_COORDINATOR
import asyncio

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
        MaxPower(api, device_name=config[CONF_NAME], sensor_name="Power output", sensor_id="power_output")
    ]

    add_entities(numbers, True)


class MaxPower(SwitchEntity):
    _attr_available = False
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, api: APsystemsEZ1M, device_name: str, sensor_name: str, sensor_id: str):
        """Initialize the sensor."""
        self._api = api
        self._state = None
        self._device_name = device_name
        self._name = sensor_name
        self._sensor_id = sensor_id

    async def async_update(self):
        try:
            status = await self._api.get_device_power_status()
            if status == Status.normal:
                self._state = True
            else:
                self._state = False
            self._attr_available = True
        except (client_exceptions.ClientConnectionError, asyncio.TimeoutError):
            self._attr_available = False

    @property
    def unique_id(self) -> str | None:
        return f"apsystemsapi_{self._device_name}_{self._sensor_id}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    async def async_turn_on(self, **kwargs):
        try:
            await self._api.set_device_power_status(0)
            self._attr_available = True
        except (client_exceptions.ClientConnectionError, asyncio.TimeoutError, asyncio.TimeoutError):
            self._attr_available = False

    async def async_turn_off(self, **kwargs):
        try:
            await self._api.set_device_power_status(1)
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

    @property
    def is_on(self) -> bool | None:
        return self._state
