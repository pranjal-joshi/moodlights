"""MoodLights - Easy mood-based light management for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant import config_entries
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

__version__ = "0.1.0"

ATTR_MOOD_ID = "mood_id"
ATTR_PRESET_NAME = "preset_name"

SERVICE_ACTIVATE_MOOD = "activate_mood"
SERVICE_RESTORE_PREVIOUS = "restore_previous"
SERVICE_SAVE_STATE = "save_state"

PLATFORMS = ["button"]


def _build_schemas() -> tuple:
    """Build voluptuous service schemas (deferred so HA is not required at import time)."""
    import voluptuous as vol
    from homeassistant.helpers import config_validation as cv

    activate = vol.Schema(
        {
            vol.Required(ATTR_MOOD_ID): cv.string,
            vol.Optional(ATTR_PRESET_NAME, default=""): cv.string,
        }
    )
    restore = vol.Schema(
        {
            vol.Required(ATTR_MOOD_ID): cv.string,
        }
    )
    save = vol.Schema(
        {
            vol.Required(ATTR_MOOD_ID): cv.string,
            vol.Optional(ATTR_PRESET_NAME, default=""): cv.string,
        }
    )
    return activate, restore, save


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the MoodLights integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_will_start_from_async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Called when a config entry is about to be started.

    This is the place to register services - they're global to the integration.
    """
    if not hass.services.has_service(DOMAIN, SERVICE_ACTIVATE_MOOD):
        _register_services(hass)


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up MoodLights from a config entry."""
    from .manager import MoodManager

    hass.data.setdefault(DOMAIN, {})

    manager = MoodManager(hass)
    await manager.load_moods(entry.data)
    hass.data[DOMAIN][entry.entry_id] = manager

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        _LOGGER.exception("Error setting up MoodLights platform")
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    entry.async_on_unload(
        entry.add_delayed_start_listener(async_will_start_from_async_setup_entry)
    )

    return True


def _get_manager_for_mood(hass: HomeAssistant, mood_id: str):
    """Find the MoodManager that owns the given mood_id."""
    from .manager import MoodManager

    for _entry_id, manager in hass.data.get(DOMAIN, {}).items():
        if not isinstance(manager, MoodManager):
            continue
        if mood_id in manager.get_all_moods():
            return manager
    return None


def _register_services(hass: HomeAssistant) -> None:
    """Register MoodLights services."""
    from homeassistant.exceptions import ServiceValidationError

    schema_activate, schema_restore, schema_save = _build_schemas()

    async def handle_activate_mood(call) -> None:
        mood_id = call.data[ATTR_MOOD_ID]
        preset_name = call.data.get(ATTR_PRESET_NAME, "")
        manager = _get_manager_for_mood(hass, mood_id)
        if manager is None:
            raise ServiceValidationError(f"Mood '{mood_id}' not found")
        await manager.activate_mood(mood_id, preset_name=preset_name)

    async def handle_restore_previous(call) -> None:
        mood_id = call.data[ATTR_MOOD_ID]
        manager = _get_manager_for_mood(hass, mood_id)
        if manager is None:
            raise ServiceValidationError(f"Mood '{mood_id}' not found")
        success = await manager.restore_previous(mood_id)
        if not success:
            raise ServiceValidationError(
                f"No saved state to restore for mood '{mood_id}'"
            )

    async def handle_save_state(call) -> None:
        mood_id = call.data[ATTR_MOOD_ID]
        preset_name = call.data.get(ATTR_PRESET_NAME, "")
        manager = _get_manager_for_mood(hass, mood_id)
        if manager is None:
            raise ServiceValidationError(f"Mood '{mood_id}' not found")
        await manager.save_state(mood_id, preset_name=preset_name)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTIVATE_MOOD,
        handle_activate_mood,
        schema=schema_activate,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESTORE_PREVIOUS,
        handle_restore_previous,
        schema=schema_restore,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_STATE,
        handle_save_state,
        schema=schema_save,
    )
    _LOGGER.debug("MoodLights services registered")


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    manager = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if manager:
        await manager.async_unload()

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Clean up when the integration is removed."""
    from homeassistant.helpers import device_registry as dr
    from homeassistant.helpers import entity_registry as er

    # Remove devices owned by this config entry
    device_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_reg, entry.entry_id):
        device_reg.async_remove_device(device.id)

    # Remove orphaned entities
    entity_reg = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
        entity_reg.async_remove(entity.entity_id)

    # Clean up hass.data
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)
    if DOMAIN in hass.data and not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)


async def async_reload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
