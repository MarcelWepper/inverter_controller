from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from .const import DOMAIN, LOGGER

class InverterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, LOGGER, name=DOMAIN)
        self.config_entry = entry # Entry is still passed to coordinator constructor
        self.solar_ema, self.hard_boost, self.enabled = 0.0, False, True
        self.data = {"target_power": 100, "solar_ema": 0.0, "hard_boost": False, "guard_active": False}
        
        async_track_state_change_event(hass, [self.get_cfg("grid_sensor"), self.get_cfg("soc_sensor"), self.get_cfg("solar_sensor")], self._async_handle_update)

    def get_cfg(self, key, default=None):
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))

    async def _async_handle_update(self, event):
        try:
            grid_p = float(self.hass.states.get(self.get_cfg("grid_sensor")).state or 0)
            soc = float(self.hass.states.get(self.get_cfg("soc_sensor")).state or 0)
            solar_raw = float(self.hass.states.get(self.get_cfg("solar_sensor")).state or 0)
            limit_id = self.get_cfg("inverter_limit_entity")
            current = float(self.hass.states.get(limit_id).state or 100)
        except (ValueError, AttributeError, TypeError): return

        self.solar_ema = (0.3 * solar_raw) + (0.7 * self.solar_ema)
        if not self.hard_boost and soc >= 96: self.hard_boost = True
        elif self.hard_boost and soc <= 94: self.hard_boost = False

        desired, step = current, self.get_cfg("step_size", 50)
        if self.hard_boost or grid_p > 10: desired += step
        elif grid_p < -60: desired -= step

        guard = solar_raw < 100
        if guard: desired = 100
        target = max(self.get_cfg("min_power", 100), min(self.get_cfg("max_power", 800), desired))

        if self.enabled and target != current:
            await self.hass.services.async_call(limit_id.split(".")[0], "set_value", {"entity_id": limit_id, "value": target})

        self.data = {"target_power": target, "solar_ema": round(self.solar_ema, 1), "hard_boost": self.hard_boost, "guard_active": guard}
        self.async_set_updated_data(self.data)