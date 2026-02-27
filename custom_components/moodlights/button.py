"""Button platform for MoodLights."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .manager import MoodConfig, MoodManager


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights button entities."""
    manager: MoodManager = hass.data[DOMAIN][config_entry.entry_id]
    entry_id = config_entry.entry_id

    entities: list[ButtonEntity] = []
    for mood_id, mood_config in manager.get_all_moods().items():
        entities.append(MoodActivateButton(mood_config, manager, entry_id))
        entities.append(MoodRestoreButton(mood_config, manager, entry_id))

    async_add_entities(entities)


class MoodButtonBase(ButtonEntity):
    """Base class for Mood buttons."""

    _attr_has_entity_name = True

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the mood button."""
        self._config = mood_config
        self._manager = manager
        self._entry_id = entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{mood_config.mood_id}")},
            name=mood_config.name,
            manufacturer="MoodLights",
            model="Mood",
            sw_version="0.1.0",
        )


class MoodActivateButton(MoodButtonBase):
    """Button to activate a mood."""

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the activate button."""
        super().__init__(mood_config, manager, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_activate"
        self._attr_name = "Activate"
        self._attr_icon = "mdi:play"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._manager.activate_mood(self._config.mood_id)


class MoodRestoreButton(MoodButtonBase):
    """Button to restore previous state."""

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the restore button."""
        super().__init__(mood_config, manager, entry_id)
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_restore"
        self._attr_name = "Revert"
        self._attr_icon = "mdi:restore"

    async def async_press(self) -> None:
        """Handle button press."""
        await self._manager.restore_previous(self._config.mood_id)
