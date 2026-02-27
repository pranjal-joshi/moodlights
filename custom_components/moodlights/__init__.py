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
    
    async def handle_activate(call, manager):
        """Handle activate service."""
        entity_id = call.data.get("entity_id")
        if entity_id and entity_id.startswith("select."):
            mood_id = entity_id.replace("select.", "").replace(f"{DOMAIN}_", "")
            await manager.activate_mood(mood_id)

    async def handle_restore(call, manager):
        """Handle restore service."""
        entity_id = call.data.get("entity_id")
        if entity_id and entity_id.startswith("select."):
            mood_id = entity_id.replace("select.", "").replace(f"{DOMAIN}_", "")
            await manager.restore_previous(mood_id)

    async def handle_get_status(call, manager):
        """Handle get_status service."""
        entity_id = call.data.get("entity_id")
        if entity_id and entity_id.startswith("select."):
            mood_id = entity_id.replace("select.", "").replace(f"{DOMAIN}_", "")
            can_restore = manager.can_restore(mood_id)
            return {"can_restore": can_restore}
        return {"can_restore": False}

    async def async_activate_service(call):
        """Service to activate a mood."""
        for entry_id, manager in hass.data.get(DOMAIN, {}).items():
            await handle_activate(call, manager)

    async def async_restore_service(call):
        """Service to restore previous state."""
        for entry_id, manager in hass.data.get(DOMAIN, {}).items():
            await handle_restore(call, manager)

    async def async_get_status_service(call):
        """Service to get mood status."""
        for entry_id, manager in hass.data.get(DOMAIN, {}).items():
            return await handle_get_status(call, manager)
        return {"can_restore": False}

    hass.services.async_register(DOMAIN, "activate", async_activate_service)
    hass.services.async_register(DOMAIN, "restore", async_restore_service)
    hass.services.async_register(DOMAIN, "get_status", async_get_status_service)

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
