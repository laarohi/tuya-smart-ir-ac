import voluptuous as vol

import logging

from pprint import pformat

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.components.fan import FanEntityFeature, FanEntity
from homeassistant.const import (
    STATE_UNKNOWN, 
    STATE_UNAVAILABLE,
    CONF_NAME,
    CONF_UNIQUE_ID
)
from homeassistant.util.percentage import ordered_list_item_to_percentage, percentage_to_ordered_list_item

from .const import TUYA_API_URLS
from .api import TuyaRemoteAPI

_LOGGER = logging.getLogger(__package__)

CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_INFRARED_ID = "infrared_id"
CONF_REMOTE_ID = "remote_id"
CONF_CATEGORY_ID = "category_id"
CONF_TUYA_COUNTRY = "country"

DEFAULT_PRECISION = 1.0
DEFAULT_TUYA_COUNTRY = "EU"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ACCESS_ID): cv.string,
        vol.Required(CONF_ACCESS_SECRET): cv.string,
        vol.Required(CONF_INFRARED_ID): cv.string,
        vol.Required(CONF_REMOTE_ID): cv.string,
        vol.Required(CONF_CATEGORY_ID): vol.Coerce(int),
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_TUYA_COUNTRY, default=DEFAULT_TUYA_COUNTRY): vol.In(TUYA_API_URLS.keys())
    }
)

ORDERED_NAMED_FAN_SPEEDS = ["Low", "Medium", "High"]  

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:

    add_entities([TuyaFan(hass, config)])


class TuyaFan(FanEntity):
    def __init__(self, hass, config):
        self._api = TuyaRemoteAPI(
            hass,
            config[CONF_ACCESS_ID],
            config[CONF_ACCESS_SECRET],
            config[CONF_REMOTE_ID],
            config[CONF_INFRARED_ID],
            config[CONF_CATEGORY_ID],
            TUYA_API_URLS.get(config[CONF_TUYA_COUNTRY])
        )
        self._name = config.get(CONF_NAME)
        self._unique_id = config.get(CONF_UNIQUE_ID, None)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def supported_features(self):
        return FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON

    @property
    def percentage(self):
        """Return the current speed percentage."""
        current_speed = self._api._speed if self._api._speed else None
        if current_speed:
            return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, current_speed)
        else:
            return 0

    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    async def async_turn_off(self):
        """Turn the fan off."""
        _LOGGER.info("TURN OFF")
        await self._api.async_turn_off()

    async def async_update(self):
        await self._api.async_update()
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        speed = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
        await self._api.async_set_fan_speed(speed)



