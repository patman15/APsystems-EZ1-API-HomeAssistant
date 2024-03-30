"""Home Assistant coordinator for BLE Battery Management System integration."""

from datetime import timedelta

from homeassistant.const import ATTR_NAME, CONF_NAME, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry
from APsystemsEZ1 import APsystemsEZ1M, ReturnOutputData
from dataclasses import asdict
from .const import DOMAIN, UPDATE_INTERVAL, LOGGER


class EZ1Coordinator(DataUpdateCoordinator):
    """Update coordinator for a battery management system"""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize EZ1M data coordinator."""

        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        config = entry.data

        LOGGER.debug(f"Initializing coordinator for {config[CONF_NAME]}")

        self._api = APsystemsEZ1M(ip_address=config[CONF_IP_ADDRESS])
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, config[CONF_NAME])},
            name=config[CONF_NAME],
            manufacturer="APsystems",
            model="EZ1-M",
            connections={(CONF_IP_ADDRESS, config[CONF_IP_ADDRESS])},
            configuration_url=None,
        )
    
    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    # @property
    # def device_power_status(self)

    async def _setup(self) -> None:
        try:
            device_info = await self._api.get_device_info()
            if device_info is not None:
                self._device_info["sw_version"] = device_info.devVer
                self._device_info["serial_number"] = device_info.deviceId
        except:
            pass

    async def _async_update_data(self) -> dict[str, float]:
        """Return the latest data from the device."""
        LOGGER.debug(f"{self.device_info.get(ATTR_NAME)} data update")
        try:
            if self.device_info.get("serial_number") is None:
                await self._setup()
            data = await self._api.get_output_data()
        except Exception as err:
            raise UpdateFailed(f"Data update failed: {err}")
        if data is not None:
            LOGGER.debug(asdict(data))
            sums = {
                "power": data.p1 + data.p2,
                "energy_counter": data.te1 + data.te2,
                "energy_counter_daily": data.e1 + data.e2,
            }
            return asdict(data) | sums
        return {}
