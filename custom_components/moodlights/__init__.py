"""MoodLights - Easy mood-based light management for Home Assistant."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .manager import MoodManager

__version__ = "1.0.0"

PLATFORM_SCHEMA = vol.Schema({vol.Optional(DOMAIN): vol.Schema({})})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the MoodLights integration."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up MoodLights from a config entry."""
    manager = MoodManager(hass)
    hass.data[DOMAIN][entry.entry_id] = manager
    
    await hass.config_entries.async_forward_entry_setups(entry, ["select", "switch", "sensor"])
    
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.async_unload()
    
    return await hass.config_entries.async_unload_platforms(entry, ["select", "switch", "sensor"])


async def async_reload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
