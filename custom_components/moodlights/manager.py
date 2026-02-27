"""Mood management for MoodLights."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant

from .const import (
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_CONFIG,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    CONF_LIGHTS,
    CONF_MOOD_NAME,
    DOMAIN,
    LIGHT_POWER_DONT_CHANGE,
    LIGHT_POWER_OFF,
    LIGHT_POWER_ON,
)
from .state import StateManager


@dataclass
class MoodConfig:
    """Configuration for a mood."""

    mood_id: str
    name: str
    lights: list[str]
    light_config: dict


class MoodManager:
    """Manages all moods and their operations."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the mood manager."""
        self._hass = hass
        self._moods: dict[str, MoodConfig] = {}
        self._state_manager = StateManager(hass)

    async def load_moods(self, config: dict) -> None:
        """Load moods from config."""
        moods_data = config.get("moods", [])
        
        for idx, mood_data in enumerate(moods_data):
            mood_id = f"mood_{idx}"
            mood_config = MoodConfig(
                mood_id=mood_id,
                name=mood_data.get(CONF_MOOD_NAME, f"Mood {idx + 1}"),
                lights=mood_data.get(CONF_LIGHTS, []),
                light_config=mood_data.get(CONF_LIGHT_CONFIG, {}),
            )
            self._moods[mood_id] = mood_config

    async def activate_mood(self, mood_id: str) -> bool:
        """Activate a mood."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        # Save current state before activating
        self._state_manager.save_current_state(mood_id, mood_config.lights)

        # Apply the mood
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
                
                tasks.append(
                    self._hass.services.async_call("light", "turn_on", service_data)
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def async_unload(self) -> None:
        """Unload the manager."""
        self._state_manager.clear_all_states()
        self._moods.clear()
