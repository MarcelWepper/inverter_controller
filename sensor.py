from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add):
    coord = hass.data[DOMAIN][entry.entry_id]
    async_add([InverterSensor(coord, "target_power", "Target Power", "W"), InverterSensor(coord, "solar_ema", "Solar EMA", "W")])

class InverterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coord, key, name, unit):
        super().__init__(coord)
        self._key, self._attr_name, self._attr_native_unit_of_measurement = key, f"Inverter {name}", unit
        self._attr_unique_id = f"{coord.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, coord.config_entry.entry_id)}, name="Inverter Controller")
    @property
    def native_value(self): return self.coordinator.data.get(self._key)