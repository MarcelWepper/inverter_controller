from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add):
    async_add([InverterSwitch(hass.data[DOMAIN][entry.entry_id])])

class InverterSwitch(SwitchEntity):
    def __init__(self, coord):
        self.coord = coord
        self._attr_name = "Inverter Controller Enabled"
        self._attr_is_on = True # Initial state
    async def async_turn_on(self, **kwargs):
        self.coord.enabled = self._attr_is_on = True
        self.async_write_ha_state()
    async def async_turn_off(self, **kwargs):
        self.coord.enabled = self._attr_is_on = False
        self.async_write_ha_state()