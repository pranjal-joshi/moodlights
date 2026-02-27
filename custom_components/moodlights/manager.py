"""Mood management for MoodLights."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_AREA,
    CONF_EXCLUSION_HELPERS,
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_CONFIG,
    CONF_LIGHT_EFFECT,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    CONF_NAME,
    CONF_SAVE_STATES,
    DOMAIN,
    LIGHT_POWER_DONT_CHANGE,
    LIGHT_POWER_OFF,
    LIGHT_POWER_ON,
)
from .exclusion import ExclusionEngine
from .state import StateManager


@dataclass
class MoodConfig:
    """Configuration for a mood."""

    mood_id: str
    name: str
    area_id: str
    light_config: dict
    exclusion_helpers: list[str] = field(default_factory=list)
    save_states: bool = True


class MoodManager:
    """Manages all moods and their operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the mood manager."""
        self._hass = hass
        self._moods: dict[str, MoodConfig] = {}
        self._state_manager = StateManager(hass)
        self._exclusion_engine = ExclusionEngine(hass)

    async def load_moods(self, config: dict) -> None:
        """Load moods from config."""
        moods_data = config.get("moods", [])
        
        for idx, mood_data in enumerate(moods_data):
            mood_id = f"mood_{idx}"
            mood_config = MoodConfig(
                mood_id=mood_id,
                name=mood_data.get(CONF_NAME, f"Mood {idx + 1}"),
                area_id=mood_data.get(CONF_AREA, ""),
                light_config=mood_data.get(CONF_LIGHT_CONFIG, {}),
                exclusion_helpers=mood_data.get(CONF_EXCLUSION_HELPERS, []),
                save_states=mood_data.get(CONF_SAVE_STATES, True),
            )
            self._moods[mood_id] = mood_config

    async def activate_mood(self, mood_id: str) -> bool:
        """Activate a mood."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        excluded, _ = await self.check_exclusions(mood_id)
        if excluded:
            return False

        if mood_config.save_states:
            self._state_manager.save_current_state(
                mood_id,
                list(mood_config.light_config.keys()),
            )

        await self._apply_light_config(mood_config.light_config)

        return True

    async def restore_previous(self, mood_id: str) -> bool:
        """Restore the previous state for a mood."""
        return await self._state_manager.restore_previous(mood_id)

    def can_restore(self, mood_id: str) -> bool:
        """Check if a mood can be restored."""
        return self._state_manager.can_restore(mood_id)

    def get_all_moods(self) -> dict[str, MoodConfig]:
        """Get all mood configurations."""
        return self._moods.copy()

    async def _apply_light_config(self, light_config: dict) -> None:
        """Apply light configuration to all lights."""
        tasks = []

        for entity_id, config in light_config.items():
            power = config.get(CONF_LIGHT_POWER, LIGHT_POWER_DONT_CHANGE)
            
            if power == LIGHT_POWER_OFF:
                tasks.append(
                    self._hass.services.async_call("light", "turn_off", {"entity_id": entity_id})
                )
            elif power == LIGHT_POWER_ON:
                service_data: dict[str, Any] = {"entity_id": entity_id}
                
                brightness = config.get(CONF_LIGHT_BRIGHTNESS)
                if brightness is not None:
                    service_data["brightness_pct"] = brightness
                
                color_temp_kelvin = config.get(CONF_LIGHT_COLOR_TEMP_KELVIN)
                if color_temp_kelvin is not None:
                    service_data["color_temp_kelvin"] = color_temp_kelvin
                
                rgb_color = config.get(CONF_LIGHT_RGB_COLOR)
                if rgb_color is not None:
                    service_data["rgb_color"] = rgb_color
                
                effect = config.get(CONF_LIGHT_EFFECT)
                if effect:
                    service_data["effect"] = effect
                
                tasks.append(
                    self._hass.services.async_call("light", "turn_on", service_data)
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def check_exclusions(self, mood_id: str) -> tuple[bool, str]:
        """Check if mood should be blocked by exclusions."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False, ""

        return await self._exclusion_engine.check_exclusions(
            mood_config.exclusion_helpers,
            [],
        )

    async def async_unload(self) -> None:
        """Unload the manager."""
        self._state_manager.clear_all_states()
        self._moods.clear()
