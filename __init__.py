"""
Custom integration to integrate inverter_controller with Home Assistant.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import InverterCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    # Initialize your reactive coordinator
    coordinator = InverterCoordinator(hass, entry)
    
    # Store the coordinator instance
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True