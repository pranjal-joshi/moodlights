"""Mood entity for MoodLights."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory

from .const import ATTR_CAN_RESTORE, ATTR_CURRENT_PRESET, ATTR_PREVIOUS_PRESET, DOMAIN, ICON_MOOD
from .manager import MoodConfig, MoodManager


class MoodEntity(SelectEntity):
    """Representation of a Mood entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        mood_config: MoodConfig,
        manager: MoodManager,
    ) -> None:
        """Initialize the mood entity."""
        self._hass = hass
        self._config = mood_config
        self._manager = manager
        self._current_preset: str | None = None
        self._previous_preset: str | None = None

        self.entity_description = SelectEntityDescription(
            key=mood_config.mood_id,
            name=mood_config.name,
            icon=ICON_MOOD,
            entity_category=EntityCategory.CONFIG,
        )

        self._attr_options = manager.get_mood_options(mood_config.mood_id)
        self._attr_unique_id = f"{DOMAIN}_{mood_config.mood_id}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            ATTR_CURRENT_PRESET: self._current_preset,
            ATTR_PREVIOUS_PRESET: self._previous_preset,
            ATTR_CAN_RESTORE: self._manager.can_restore(self._config.mood_id),
        }

    async def async_select_option(self, option: str) -> None:
        """Handle option selection."""
        excluded, _ = await self._manager.check_exclusions(self._config.mood_id)
        
        if excluded:
            return

        self._previous_preset = self._current_preset
        self._current_preset = option

        await self._manager.activate_mood(self._config.mood_id, option)
        self.async_write_ha_state()

    async def update_preset(self, preset_name: str) -> None:
        """Update the current preset."""
        self._previous_preset = self._current_preset
        self._current_preset = preset_name
        self.async_write_ha_state()

    async def async_restore_previous(self) -> bool:
        """Restore the previous mood state."""
        return await self._manager.restore_previous(self._config.mood_id)

    async def async_save_state(self) -> bool:
        """Manually save the current state."""
        return await self._manager.save_state(self._config.mood_id)
