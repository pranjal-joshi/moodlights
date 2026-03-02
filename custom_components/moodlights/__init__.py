"""MoodLights - Easy mood-based light management for Home Assistant."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.service import ServiceCall

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry
    from .manager import MoodManager

PLATFORMS = [Platform.BUTTON]

ATTR_ENTRY_ID = "entry_id"
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
            vol.Required(ATTR_ENTRY_ID): cv.string,
            vol.Required(ATTR_MOOD_ID): cv.string,
            vol.Optional(ATTR_PRESET_NAME, default=""): cv.string,
        }
    )
    restore = vol.Schema(
        {
            vol.Required(ATTR_ENTRY_ID): cv.string,
            vol.Required(ATTR_MOOD_ID): cv.string,
        }
    )
    save = vol.Schema(
        {
            vol.Required(ATTR_ENTRY_ID): cv.string,
            vol.Required(ATTR_MOOD_ID): cv.string,
            vol.Optional(ATTR_PRESET_NAME, default=""): cv.string,
        }
    )
    return activate, restore, save


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the MoodLights integration."""
    hass.data.setdefault(DOMAIN, {})

    schema_activate, schema_restore, schema_save = _build_schemas()

    async def handle_activate_mood(call: ServiceCall) -> None:
        """Handle the activate_mood service call."""
        entry_id = call.data[ATTR_ENTRY_ID]
        mood_id = call.data[ATTR_MOOD_ID]
        preset_name = call.data.get(ATTR_PRESET_NAME, "")

        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN or not entry.state:
            raise ServiceValidationError(f"Invalid config entry: {entry_id}")

        manager: MoodManager = entry.runtime_data
        await manager.activate_mood(mood_id, preset_name=preset_name)

    async def handle_restore_previous(call: ServiceCall) -> None:
        """Handle the restore_previous service call."""
        entry_id = call.data[ATTR_ENTRY_ID]
        mood_id = call.data[ATTR_MOOD_ID]

        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN or not entry.state:
            raise ServiceValidationError(f"Invalid config entry: {entry_id}")

        manager: MoodManager = entry.runtime_data
        success = await manager.restore_previous(mood_id)
        if not success:
            raise ServiceValidationError(
                f"No saved state to restore for mood '{mood_id}'"
            )

    async def handle_save_state(call: ServiceCall) -> None:
        """Handle the save_state service call."""
        entry_id = call.data[ATTR_ENTRY_ID]
        mood_id = call.data[ATTR_MOOD_ID]
        preset_name = call.data.get(ATTR_PRESET_NAME, "")

        entry = hass.config_entries.async_get_entry(entry_id)
        if not entry or entry.domain != DOMAIN or not entry.state:
            raise ServiceValidationError(f"Invalid config entry: {entry_id}")

        manager: MoodManager = entry.runtime_data
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
    LOGGER.debug("MoodLights services registered")

    return True


async def async_setup_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> bool:
    """Set up MoodLights from a config entry."""
    from .manager import MoodManager

    manager = MoodManager(hass)
    await manager.load_moods(entry.data)

    entry.runtime_data = manager

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


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

    device_reg = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_reg, entry.entry_id):
        device_reg.async_remove_device(device.id)

    entity_reg = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
        entity_reg.async_remove(entity.entity_id)


async def async_reload_entry(hass: HomeAssistant, entry: MoodLightsConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
