"""Config flow and Options flow for Inverter Controller."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from .const import DOMAIN

class InverterControllerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inverter Controller."""
    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return InverterControllerOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Step 1: Required Entities (Mandatory)."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_settings()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("grid_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("soc_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("solar_sensor"): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required("inverter_limit_entity"): selector.EntitySelector(selector.EntitySelectorConfig(domain=["number", "input_number"])),
            })
        )

    async def async_step_settings(self, user_input=None):
        """Step 2: Adjustable Logic Variables."""
        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title="Inverter Controller", data=self.data)

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema({
                vol.Optional("min_power", default=100): int,
                vol.Optional("max_power", default=800): int,
                vol.Optional("step_size", default=50): int,
                vol.Optional("solar_ema_alpha", default=0.3): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.01, max=1.0, step=0.01, mode="box")
                ),
            })
        )

class InverterControllerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle editing variables after setup via the 'Configure' button."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the settings."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Pre-fill with existing data/options
        options = self.config_entry.options or self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("min_power", default=options.get("min_power", 100)): int,
                vol.Optional("max_power", default=options.get("max_power", 800)): int,
                vol.Optional("step_size", default=options.get("step_size", 50)): int,
                vol.Optional("solar_ema_alpha", default=options.get("solar_ema_alpha", 0.3)): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0.01, max=1.0, step=0.01, mode="box")
                ),
            })
        )