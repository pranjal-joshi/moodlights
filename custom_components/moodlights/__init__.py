"""MoodLights - Easy mood-based light management for Home Assistant."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN

__version__ = "0.1.0"

PLATFORM_SCHEMA = vol.Schema({vol.Optional(DOMAIN): vol.Schema({})})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the MoodLights integration."""
    hass.data[DOMAIN] = {}

    async def handle_activate(call, manager, entry_id):
        """Handle activate service."""
        entity_id = call.data.get("entity_id")
        if not entity_id:
            return
        
        for mood_id, mood_config in manager.get_all_moods().items():
            expected_entity_id = f"select.{DOMAIN}_{mood_id}"
            if entity_id == expected_entity_id:
                await manager.activate_mood(mood_id)
                return

    async def handle_restore(call, manager, entry_id):
        """Handle restore service."""
        entity_id = call.data.get("entity_id")
        if not entity_id:
            return
        
        for mood_id, mood_config in manager.get_all_moods().items():
            expected_entity_id = f"select.{DOMAIN}_{mood_id}"
            if entity_id == expected_entity_id:
                await manager.restore_previous(mood_id)
                return

    async def async_activate_service(call):
        """Service to activate a mood."""
        for entry_id, manager in hass.data.get(DOMAIN, {}).items():
            await handle_activate(call, manager, entry_id)

    async def async_restore_service(call):
        """Service to restore previous state."""
        for entry_id, manager in hass.data.get(DOMAIN, {}).items():
            await handle_restore(call, manager, entry_id)

    hass.services.async_register(DOMAIN, "activate", async_activate_service)
    hass.services.async_register(DOMAIN, "restore", async_restore_service)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up MoodLights from a config entry."""
    from .manager import MoodManager

    manager = MoodManager(hass)
    await manager.load_moods(entry.data)
    hass.data[DOMAIN][entry.entry_id] = manager

    await hass.config_entries.async_forward_entry_setups(entry, ["select"])

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    manager = hass.data[DOMAIN].pop(entry.entry_id, None)
    if manager:
        await manager.async_unload()

    return await hass.config_entries.async_unload_platforms(entry, ["select"])


async def async_reload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
