"""Mood management for MoodLights."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_AUTO_ACTIVATE,
    CONF_AUTO_ACTIVATE_DAYS,
    CONF_AUTO_ACTIVATE_TIME,
    CONF_CONFIRMATION_MODE,
    CONF_EXCLUSION_HELPERS,
    CONF_EXCLUSION_STATES,
    CONF_LIGHT_ENTITIES,
    CONF_MAX_SAVED_STATES,
    CONF_MOODS,
    CONF_NAME,
    CONF_PRESET_BRIGHTNESS,
    CONF_PRESET_COLOR_TEMP,
    CONF_PRESET_NAME,
    CONF_PRESET_RGB_COLOR,
    CONF_PRESET_TRANSITION,
    CONF_PRESETS,
    CONF_SAVE_STATES,
    CONFIRMATION_APPROVE,
    CONFIRMATION_NONE,
    CONFIRMATION_NOTIFY,
    DOMAIN,
)
from .exclusion import ExclusionEngine
from .state import StateManager


@dataclass
class MoodConfig:
    """Configuration for a mood."""

    mood_id: str
    name: str
    light_entities: list[str]
    presets: list[dict]
    exclusion_helpers: list[str] = field(default_factory=list)
    exclusion_states: list[str] = field(default_factory=list)
    confirmation_mode: str = CONFIRMATION_NONE
    save_states: bool = True
    max_saved_states: int = 3
    auto_activate_time: str | None = None
    auto_activate_days: list[str] | None = None


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
        moods_data = config.get(CONF_MOODS, [])
        
        for idx, mood_data in enumerate(moods_data):
            mood_id = f"mood_{idx}"
            mood_config = MoodConfig(
                mood_id=mood_id,
                name=mood_data.get(CONF_NAME, f"Mood {idx + 1}"),
                light_entities=mood_data.get(CONF_LIGHT_ENTITIES, []),
                presets=mood_data.get(CONF_PRESETS, []),
                exclusion_helpers=mood_data.get(CONF_EXCLUSION_HELPERS, []),
                exclusion_states=mood_data.get(CONF_EXCLUSION_STATES, []),
                confirmation_mode=mood_data.get(CONF_CONFIRMATION_MODE, CONFIRMATION_NONE),
                save_states=mood_data.get(CONF_SAVE_STATES, True),
                max_saved_states=mood_data.get(CONF_MAX_SAVED_STATES, 3),
                auto_activate_time=mood_data.get(CONF_AUTO_ACTIVATE_TIME),
                auto_activate_days=mood_data.get(CONF_AUTO_ACTIVATE_DAYS),
            )
            self._moods[mood_id] = mood_config

    async def activate_mood(
        self, mood_id: str, preset_name: str | None = None, skip_confirmation: bool = False
    ) -> bool:
        """Activate a mood with a specific preset."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        preset = self._get_preset_by_name(mood_config, preset_name)
        if not preset:
            preset = mood_config.presets[0] if mood_config.presets else {}

        if not skip_confirmation:
            if mood_config.confirmation_mode == CONFIRMATION_APPROVE:
                return False
            elif mood_config.confirmation_mode == CONFIRMATION_NOTIFY:
                await self._send_notification(mood_config, preset)
                return False

        if mood_config.save_states:
            self._state_manager.save_current_state(
                mood_id,
                preset.get(CONF_PRESET_NAME, "default"),
                mood_config.light_entities,
            )

        await self._apply_preset(mood_config, preset)

        return True

    async def restore_previous(self, mood_id: str) -> bool:
        """Restore the previous state for a mood."""
        return await self._state_manager.restore_previous(mood_id)

    async def save_state(self, mood_id: str, preset_name: str | None = None) -> bool:
        """Manually save the current state."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        preset = self._get_preset_by_name(mood_config, preset_name)
        preset_name = preset.get(CONF_PRESET_NAME, "manual") if preset else "manual"

        self._state_manager.save_current_state(mood_id, preset_name, mood_config.light_entities)
        return True

    def get_mood_options(self, mood_id: str) -> list[str]:
        """Get available presets for a mood."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return []
        return [p.get(CONF_PRESET_NAME, "default") for p in mood_config.presets]

    def can_restore(self, mood_id: str) -> bool:
        """Check if a mood can be restored."""
        return self._state_manager.can_restore(mood_id)

    def get_all_moods(self) -> dict[str, MoodConfig]:
        """Get all mood configurations."""
        return self._moods.copy()

    async def _apply_preset(self, mood_config: MoodConfig, preset: dict) -> None:
        """Apply a preset to all lights in a mood."""
        tasks = []

        for entity_id in mood_config.light_entities:
            service_data: dict[str, Any] = {"entity_id": entity_id}

            brightness = preset.get(CONF_PRESET_BRIGHTNESS)
            if brightness is not None:
                service_data["brightness_pct"] = brightness

            color_temp = preset.get(CONF_PRESET_COLOR_TEMP)
            if color_temp is not None:
                service_data["color_temp"] = color_temp

            rgb_color = preset.get(CONF_PRESET_RGB_COLOR)
            if rgb_color is not None:
                service_data["rgb_color"] = rgb_color

            transition = preset.get(CONF_PRESET_TRANSITION, 1.0)
            service_data["transition"] = transition

            tasks.append(
                self._hass.services.async_call("light", "turn_on", service_data)
            )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _get_preset_by_name(self, mood_config: MoodConfig, name: str | None) -> dict | None:
        """Get a preset by name."""
        if not name:
            return None
        for preset in mood_config.presets:
            if preset.get(CONF_PRESET_NAME) == name:
                return preset
        return None

    async def _send_notification(self, mood_config: MoodConfig, preset: dict) -> None:
        """Send a notification about mood change."""
        preset_name = preset.get(CONF_PRESET_NAME, "default")
        message = f"Changing mood to {mood_config.name} - {preset_name}"

        await self._hass.services.async_call(
            "notify",
            "persistent_notification",
            {"message": message, "title": "MoodLights"},
        )

    async def check_exclusions(self, mood_id: str) -> tuple[bool, str]:
        """Check if mood should be blocked by exclusions."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False, ""

        return await self._exclusion_engine.check_exclusions(
            mood_config.exclusion_helpers,
            mood_config.exclusion_states,
        )

    async def async_unload(self) -> None:
        """Unload the manager."""
        self._state_manager.clear_all_states()
        self._moods.clear()
