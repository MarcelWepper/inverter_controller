from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
import logging

_LOGGER = logging.getLogger(__name__)

class InverterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name="Inverter Controller")
        self.entry = entry
        self.solar_ema = None
        self.soft_boost = False
        self.hard_boost = False
        
        # Monitor the sensors you picked in the UI
        async_track_state_change_event(
            hass, 
            [entry.data["grid_sensor"], entry.data["soc_sensor"], entry.data["solar_sensor"]],
            self._async_handle_update
        )

    async def _async_handle_update(self, event):
        # 1. Get current values from HA state machine
        grid_p = float(self.hass.states.get(self.entry.data["grid_sensor"]).state or 0)
        soc = float(self.hass.states.get(self.entry.data["soc_sensor"]).state or 0)
        solar_raw = float(self.hass.states.get(self.entry.data["solar_sensor"]).state or 0)
        current_setpoint = float(self.hass.states.get(self.entry.data["inverter_limit_entity"]).state or 100)

        # 2. EMA Smoothing logic from your power.py
        alpha = 0.3
        if self.solar_ema is None: self.solar_ema = solar_raw
        else: self.solar_ema = alpha * solar_raw + (1 - alpha) * self.solar_ema

        # 3. Boost Hysteresis logic
        if not self.hard_boost and soc >= 96: self.hard_boost = True
        elif self.hard_boost and soc <= 94: self.hard_boost = False

        # 4. Calculation Logic
        desired = current_setpoint
        step = self.entry.data["step_size"]

        if self.hard_boost:
            desired += step
        elif grid_p > 10: # HYST_IMPORT
            desired += step
        elif grid_p < -60: # EXPORT_BAND_LOW - HYST_EXPORT
            desired -= step

        # 5. Safety Guard
        if solar_raw < 100: desired = 100
        
        target = max(self.entry.data["min_power"], min(self.entry.data["max_power"], desired))

        # 6. Push to the Inverter Entity
        if target != current_setpoint:
            await self.hass.services.async_call(
                "number", "set_value", 
                {ATTR_ENTITY_ID: self.entry.data["inverter_limit_entity"], "value": target}
            )