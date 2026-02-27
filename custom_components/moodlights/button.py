"""Button platform for MoodLights."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .manager import MoodManager, MoodConfig


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights button entities."""
    manager: MoodManager = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for mood_id, mood_config in manager.get_all_moods().items():
        # Create activate button
        activate_entity = MoodActivateButton(mood_config, manager)
        entities.append(activate_entity)
        
        # Create restore button
        restore_entity = MoodRestoreButton(mood_config, manager)
        entities.append(restore_entity)

    async_add_entities(entities)


class MoodButtonBase(ButtonEntity):
    """Base class for Mood buttons."""

    def __init__(self, mood_config: MoodConfig, manager: MoodManager) -> None:
        """Initialize the mood button."""
        self._config = mood_config
        self._manager = manager


class MoodActivateButton(MoodButtonBase):
    """Button to activate a mood."""

    def __init__(self, mood_config: MoodConfig, manager: MoodManager) -> None:
        """Initialize the activate button."""
        super().__init__(mood_config, manager)
        self._attr_unique_id = f"{DOMAIN}_{mood_config.mood_id}_activate"
        self._attr_name = "Activate"
        self._attr_icon = "mdi:play"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mood_config.mood_id)},
            "name": mood_config.name,
            "manufacturer": "MoodLights",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        await self._manager.activate_mood(self._config.mood_id)


class MoodRestoreButton(MoodButtonBase):
    """Button to restore previous state."""

    def __init__(self, mood_config: MoodConfig, manager: MoodManager) -> None:
        """Initialize the restore button."""
        super().__init__(mood_config, manager)
        self._attr_unique_id = f"{DOMAIN}_{mood_config.mood_id}_restore"
        self._attr_name = "Revert"
        self._attr_icon = "mdi:restore"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, mood_config.mood_id)},
            "name": mood_config.name,
            "manufacturer": "MoodLights",
        }

    async def async_press(self) -> None:
        """Handle button press."""
        await self._manager.restore_previous(self._config.mood_id)
