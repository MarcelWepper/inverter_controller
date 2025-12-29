import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN

class InverterControllerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Inverter Controller", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                # Input Sensors
                vol.Required("grid_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("soc_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("solar_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                # Output Control (The Inverter Entity)
                vol.Required("inverter_limit_entity"): selector.EntitySelector(selector.EntitySelectorConfig(domain=["number", "input_number"])),
                # Settings from your power.py
                vol.Optional("min_power", default=100): int,
                vol.Optional("max_power", default=800): int,
                vol.Optional("step_size", default=50): int,
            })
        )