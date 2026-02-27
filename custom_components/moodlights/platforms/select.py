"""Select platform for MoodLights."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .manager import MoodManager, MoodConfig


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights select entities."""
    manager: MoodManager = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for mood_id, mood_config in manager.get_all_moods().items():
        entity = MoodSelectEntity(mood_config, manager)
        entities.append(entity)

    async_add_entities(entities)


class MoodSelectEntity(SelectEntity):
    """Representation of a Mood select entity."""

    def __init__(self, mood_config: MoodConfig, manager: MoodManager) -> None:
        """Initialize the mood entity."""
        self._config = mood_config
        self._manager = manager
        self._current_option: str | None = None

        self._attr_unique_id = f"{DOMAIN}_{mood_config.mood_id}"
        self._attr_name = mood_config.name
        self._attr_options = [p.get("name", "default") for p in mood_config.presets]
        self._attr_icon = "mdi:lightbulb-group"

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._current_option

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        excluded, _ = await self._manager.check_exclusions(self._config.mood_id)

        if excluded:
            return

        self._current_option = option
        await self._manager.activate_mood(self._config.mood_id, option)
        self.async_write_ha_state()

    async def update_preset(self, preset_name: str) -> None:
        """Update the current preset."""
        self._current_option = preset_name
        self.async_write_ha_state()
