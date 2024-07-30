from tuya_connector import TuyaOpenAPI
from homeassistant.core import HomeAssistant

import logging
from pprint import pformat

_LOGGER = logging.getLogger(__package__)


class TuyaACAPI:
    def __init__(
        self,
        hass: HomeAssistant,
        access_id,
        access_secret,
        climate_id,
        infrared_id,
        api_url
    ):
        self.hass = hass
        self.climate_id = climate_id
        self.infrared_id = infrared_id

        openapi = TuyaOpenAPI(api_url, access_id, access_secret)
        openapi.connect()
        self.openapi = openapi

        self._temperature = None
        self._mode = None
        self._power = None
        self._wind = None

    async def async_init(self):
        await self.update()

    async def async_update(self):
        status = await self.get_status()
        if status:
            self._temperature = status.get("temp")
            self._mode = status.get("mode")
            self._power = status.get("power")
            self._wind = status.get("wind")
        _LOGGER.info(pformat("ASYNC_UPDATE " + str(status)))

    async def async_turn_on(self):
        await self.send_command("power", "1")

    async def async_turn_off(self):
        await self.send_command("power", "0")

    async def async_set_fan_speed(self, fan_speed):
        _LOGGER.info(fan_speed)
        await self.send_command("wind", str(fan_speed))

    async def async_set_temperature(self, temperature):
        await self.send_command("temp", str(temperature))

    async def async_set_hvac_mode(self, hvac_mode):
        await self.send_command("mode", str(hvac_mode))
        
    async def async_set_multiple(self, power, mode, temp, wind):
        cmd = { "power": power, "mode": mode, "temp": temp, "wind": wind }
        await self.send_multiple_command(cmd)

    async def get_status(self):
        url = f"/v2.0/infrareds/{self.infrared_id}/remotes/{self.climate_id}/ac/status"
        _LOGGER.info(url)
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            if data.get("success"):
                _LOGGER.info(pformat("GET_STATUS " + str(data.get("result"))))
                return data.get("result")
        except Exception as e:
            _LOGGER.error(f"Error fetching status: {e}")
        return None

    async def send_command(self, code, value):
        url = f"/v2.0/infrareds/{self.infrared_id}/air-conditioners/{self.climate_id}/command"
        _LOGGER.info(url)
        try:
            _LOGGER.info(pformat("SEND_COMMAND_CODE_THEN_VAL " + code + " " + value))
            data = await self.hass.async_add_executor_job(
                self.openapi.post,
                url,
                {
                    "code": code,
                    "value": value,
                },
            )
            _LOGGER.info(pformat("SEND_COMMAND_END " + str(data)))
            return data
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            return False

    async def send_multiple_command(self, command):
        url = f"/v2.0/infrareds/{self.infrared_id}/air-conditioners/{self.climate_id}/scenes/command"
        _LOGGER.info(url)
        try:
            _LOGGER.info(pformat("SEND_COMMAND " + str(command)))
            data = await self.hass.async_add_executor_job(self.openapi.post, url, command)
            _LOGGER.info(pformat("SEND_COMMAND_END " + str(data)))
            return data
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            return False


class TuyaRemoteAPI:
    def __init__(
        self,
        hass: HomeAssistant,
        access_id,
        access_secret,
        remote_id,
        infrared_id,
        api_url
    ):
        self.hass = hass
        self.remote_id = remote_id
        self.infrared_id = infrared_id

        openapi = TuyaOpenAPI(api_url, access_id, access_secret)
        openapi.connect()
        self.openapi = openapi

        self._power = None
        self._speed = None
        self._commands = {}

    async def async_init(self):
        url = f'/v2.0/infrareds/{self.infrared_id}/remotes/{self.remote_id}/keys'
        _LOGGER.info(url)
        try:
            data = await self.hass.async_add_executor_job(self.openapi.get, url)
            if data.get("success"):
                _LOGGER.info(pformat("GET_KEYS " + str(data.get("result"))))
                commands = {}
                for k in data.get('result').get('key_list'):
                    commands[k['key_name']] = k.copy()
                self._commands = commands.copy()
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
        await self.update()

    async def async_update(self):
        _LOGGER.info("ASYNC_UPDATE ")
        pass

    async def async_turn_off(self):
        self._power = False
        await self.send_command("Fan Off")

    async def async_toggle_light(self):
        await self.send_command("Light On/Off")

    async def async_set_fan_speed(self, speed):
        self._speed = speed
        self._power = True
        await self.send_command(speed)

    async def send_command(self, cmd):
        url = f"/v2.0/infrareds/{self.infrared_id}/remotes/{self.remote_id}/raw/command"
        _LOGGER.info(url)
        try:
            cmd = self._commands[cmd]
            _LOGGER.info(pformat("SEND_COMMAND_CODE_THEN_VAL " + cmd ))
            data = await self.hass.async_add_executor_job(
                self.openapi.post,
                url,
                {
                    "category_id": self.category_id,
                    "key_id": cmd['key_id'],
                    "key": cmd['key'],
                },
            )
            _LOGGER.info(pformat("SEND_COMMAND_END " + str(data)))
            return data
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            return False
