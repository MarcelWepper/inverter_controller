"""The reactive brain of the Inverter Controller integration."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_state_change_event
from .const import DOMAIN, LOGGER, DEFAULT_MIN_POWER, DEFAULT_MAX_POWER, DEFAULT_STEP_SIZE

class InverterCoordinator(DataUpdateCoordinator):
    """Coordinator to track state changes and apply power balancing logic."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize the coordinator and subscribe to real-time updates."""
        super().__init__(hass, LOGGER, name=DOMAIN)
        self.config_entry = entry
        
        # Internal state tracking
        self.solar_ema = None
        self.hard_boost = False
        self.enabled = True  # Controlled by switch.py
        
        # Initialize self.data for our dashboard sensors
        self.data = {
            "target_power": 100,
            "solar_ema": 0.0,
            "house_load": 0.0,
            "solar_yield": 0.0,
            "logic_state": "Initializing",
            "hard_boost": False,
            "guard_active": False,
        }

        # Reactive Trigger: Subscribe to the sensors provided in config
        self.async_on_remove(
            async_track_state_change_event(
                hass, 
                [
                    self.get_cfg("grid_sensor"), 
                    self.get_cfg("soc_sensor"), 
                    self.get_cfg("solar_sensor")
                ],
                self._async_handle_update
            )
        )

    def get_cfg(self, key, default=None):
        """Helper to get setting from options (priority) or initial data."""
        return self.config_entry.options.get(key, self.config_entry.data.get(key, default))

    async def _async_handle_update(self, event):
        """The main logic loop triggered by any sensor change."""
        
        # 1. Fetch current values from the state machine
        try:
            grid_p = float(self.hass.states.get(self.get_cfg("grid_sensor")).state or 0)
            soc = float(self.hass.states.get(self.get_cfg("soc_sensor")).state or 0)
            solar_raw = float(self.hass.states.get(self.get_cfg("solar_sensor")).state or 0)
            
            # Use the target entity itself to find its current limit
            limit_entity_id = self.get_cfg("inverter_limit_entity")
            current_setpoint = float(self.hass.states.get(limit_entity_id).state or 100)
        except (ValueError, AttributeError, TypeError):
            # If any sensor is 'Unavailable' or 'Unknown', skip this cycle
            return

        # 2. Statistics & Adjustable variables
        alpha = self.get_cfg("solar_ema_alpha", 0.3)
        house_load = current_setpoint + grid_p  # Estimated house consumption
        yield_ratio = (current_setpoint / solar_raw * 100) if solar_raw > 0 else 0

        # 3. EMA Smoothing logic
        if self.solar_ema is None:
            self.solar_ema = solar_raw
        else:
            self.solar_ema = (alpha * solar_raw) + ((1 - alpha) * self.solar_ema)

        # 4. Hysteresis Logic (Hard Boost)
        if not self.hard_boost and soc >= 96:
            self.hard_boost = True
        elif self.hard_boost and soc <= 94:
            self.hard_boost = False

        # 5. Calculation Logic
        state_desc = "Balanced"
        desired = current_setpoint
        step = self.get_cfg("step_size", DEFAULT_STEP_SIZE)
        
        if self.hard_boost:
            desired, state_desc = desired + step, "Boosting (High SoC)"
        elif grid_p > 10:  # Hysteresis for grid import
            desired, state_desc = desired + step, "Increasing Output"
        elif grid_p < -60: # Hysteresis for grid export
            desired, state_desc = desired - step, "Decreasing Output"

        # 6. Safety Guard: Force output to min if sun is gone
        guard_active = solar_raw < 100
        if guard_active:
            desired, state_desc = 100, "Guard Active (Low Sun)"
        
        # Clamp values between Min and Max
        target = max(
            self.get_cfg("min_power", DEFAULT_MIN_POWER), 
            min(self.get_cfg("max_power", DEFAULT_MAX_POWER), desired)
        )

        # 7. Push to the Inverter Entity ONLY if enabled
        if self.enabled and target != current_setpoint:
            domain = limit_entity_id.split(".")[0]
            await self.hass.services.async_call(
                domain, 
                "set_value", 
                {"entity_id": limit_entity_id, "value": target}
            )

        # 8. Update data for dashboard entities
        self.data = {
            "target_power": target,
            "solar_ema": round(self.solar_ema, 1),
            "house_load": round(house_load, 1),
            "solar_yield": round(yield_ratio, 1),
            "logic_state": state_desc,
            "hard_boost": self.hard_boost,
            "guard_active": guard_active,
        }
        
        # Tell Home Assistant the sensors need refreshing
        self.async_set_updated_data(self.data)