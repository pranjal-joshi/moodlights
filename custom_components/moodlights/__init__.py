"""MoodLights - Easy mood-based light management for Home Assistant."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry
    from .manager import MoodManager

_LOGGER = logging.getLogger(__name__)

__version__ = "0.1.0"

PLATFORMS = [Platform.BUTTON]

ATTR_MOOD_ID = "mood_id"
ATTR_PRESET_NAME = "preset_name"

SERVICE_ACTIVATE_MOOD = "activate_mood"
SERVICE_RESTORE_PREVIOUS = "restore_previous"
SERVICE_SAVE_STATE = "save_state"


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


async def async_setup_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> bool:
    """Set up MoodLights from a config entry."""
    from .manager import MoodManager

    manager = MoodManager(hass)
    await manager.load_moods(entry.data)

    entry.runtime_data = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await _async_setup_services(hass)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def _async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for the integration."""
    from homeassistant.exceptions import ServiceValidationError

    if hass.services.has_service(DOMAIN, SERVICE_ACTIVATE_MOOD):
        return

    schema_activate, schema_restore, schema_save = _build_schemas()

    async def handle_activate_mood(call) -> None:
        """Handle the activate_mood service call."""
        mood_id = call.data[ATTR_MOOD_ID]
        preset_name = call.data.get(ATTR_PRESET_NAME, "")
        manager = _get_manager_for_mood(hass, mood_id)
        if manager is None:
            raise ServiceValidationError(f"Mood '{mood_id}' not found")
        await manager.activate_mood(mood_id, preset_name=preset_name)

    async def handle_restore_previous(call) -> None:
        """Handle the restore_previous service call."""
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
        """Handle the save_state service call."""
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


def _get_manager_for_mood(hass: HomeAssistant, mood_id: str) -> MoodManager | None:
    """Find the MoodManager that owns the given mood_id."""
    from .manager import MoodManager

    for manager in hass.data[DOMAIN].values():
        if not isinstance(manager, MoodManager):
            continue
        if mood_id in manager.get_all_moods():
            return manager
    return None


async def async_unload_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    manager: MoodManager = entry.runtime_data
    await manager.async_unload()

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> None:
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


async def async_reload_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
