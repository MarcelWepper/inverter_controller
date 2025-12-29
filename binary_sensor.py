from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add):
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add([
        InverterBinary(coord, "hard_boost", "Hard Boost"),
        InverterBinary(coord, "guard_active", "Low Sun Guard")
    ])

class InverterBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coord, key, name):
        super().__init__(coord)
        self._key, self._attr_name = key, f"Inverter {name}"
    @property
    def is_on(self): return self.coordinator.data.get(self._key)