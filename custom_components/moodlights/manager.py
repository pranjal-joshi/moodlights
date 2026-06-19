"""Mood management for MoodLights."""
from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

from .const import (
    CONF_COVER_CONFIG,
    CONF_COVER_POSITION,
    CONF_COVER_TILT_POSITION,
    CONF_COVERS,
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_CONFIG,
    CONF_LIGHT_EFFECT,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    CONF_LIGHTS,
    CONF_MOOD_NAME,
    DEFAULT_REVERT_DURATION_MIN,
    LOGGER,
)
from .state import DEFAULT_MAX_STATES, StateManager


@dataclass
class MoodConfig:
    """Configuration for a mood."""

    mood_id: str
    name: str
    lights: list[str]
    light_config: dict
    covers: list[str] = field(default_factory=list)
    cover_config: dict = field(default_factory=dict)


class MoodManager:
    """Manages all moods and their operations."""

    def __init__(
        self, hass: HomeAssistant, options: dict | None = None
    ) -> None:
        """Initialize the mood manager."""
        self._hass = hass
        self._moods: dict[str, MoodConfig] = {}

        opts = options or {}
        max_states = opts.get("max_states") if opts else DEFAULT_MAX_STATES
        self._state_manager = StateManager(
            hass, max_states=max_states or DEFAULT_MAX_STATES
        )

        # Auto-revert timer state (per mood_id)
        self._auto_revert_enabled: dict[str, bool] = {}
        self._auto_revert_duration: dict[str, int] = {}  # minutes
        self._revert_timers: dict[str, Callable[[], None]] = {}  # cancel callbacks
        self._revert_deadlines: dict[str, float] = {}  # monotonic deadline

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
                covers=mood_data.get(CONF_COVERS, []),
                cover_config=mood_data.get(CONF_COVER_CONFIG, {}),
            )
            self._moods[mood_id] = mood_config

    async def activate_mood(self, mood_id: str, preset_name: str = "", duration: int | None = None) -> bool:
        """Activate a mood, saving current light and cover states first.

        Args:
            mood_id: The mood identifier.
            preset_name: Optional label for the saved state snapshot.
            duration: Optional override duration in minutes to auto-revert.
                      If None, uses the mood's configured duration (if enabled).
        """
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        # Save current state before activating (lights + covers atomically)
        self._state_manager.save_current_state(
            mood_id,
            preset_name=preset_name or mood_config.name,
            light_entities=mood_config.lights,
            cover_entities=mood_config.covers,
        )

        # Apply the mood
        await self._apply_light_config(mood_config.light_config)
        await self._apply_cover_config(mood_config.cover_config)

        # Start auto-revert timer if applicable
        self._schedule_auto_revert(mood_id, duration)

        return True

    async def restore_previous(self, mood_id: str) -> bool:
        """Restore the previous state for a mood."""
        # Cancel any active auto-revert timer (avoid double revert)
        self.cancel_auto_revert(mood_id)
        return await self._state_manager.restore_previous(mood_id)

    async def save_state(self, mood_id: str, preset_name: str = "") -> bool:
        """Manually save the current state of lights and covers for a mood."""
        mood_config = self._moods.get(mood_id)
        if not mood_config:
            return False

        result = self._state_manager.save_current_state(
            mood_id,
            preset_name=preset_name,
            light_entities=mood_config.lights,
            cover_entities=mood_config.covers,
        )
        return result is not None

    def can_restore(self, mood_id: str) -> bool:
        """Check if a mood can be restored."""
        return self._state_manager.can_restore(mood_id)

    def get_all_moods(self) -> dict[str, MoodConfig]:
        """Get all mood configurations."""
        return self._moods.copy()

    def get_mood_by_name(self, name: str) -> MoodConfig | None:
        """Get a mood config by its display name (case-insensitive)."""
        name_lower = name.lower()
        for mood in self._moods.values():
            if mood.name.lower() == name_lower:
                return mood
        return None

    async def _apply_light_config(self, light_config: dict) -> None:
        """Apply light configuration to all lights in parallel."""
        tasks = []

        for entity_id, config in light_config.items():
            power = config.get(CONF_LIGHT_POWER, True)

            if power is False:
                tasks.append(
                    self._hass.services.async_call(
                        "light", "turn_off", {"entity_id": entity_id}
                    )
                )
            else:
                service_data: dict[str, Any] = {"entity_id": entity_id}

                brightness = config.get(CONF_LIGHT_BRIGHTNESS)
                if brightness is not None:
                    service_data["brightness_pct"] = brightness

                effect = config.get(CONF_LIGHT_EFFECT)
                if effect is not None:
                    # Effect takes priority — apply it and skip colour settings
                    service_data["effect"] = effect
                else:
                    # Colour temperature takes priority over RGB
                    color_temp_kelvin = config.get(CONF_LIGHT_COLOR_TEMP_KELVIN)
                    rgb_color = config.get(CONF_LIGHT_RGB_COLOR)

                    if color_temp_kelvin is not None:
                        service_data["color_temp_kelvin"] = color_temp_kelvin
                    elif rgb_color is not None:
                        service_data["rgb_color"] = rgb_color

                tasks.append(
                    self._hass.services.async_call("light", "turn_on", service_data)
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _apply_cover_config(self, cover_config: dict) -> None:
        """Apply cover configuration to all covers in parallel."""
        if not cover_config:
            return

        tasks = []

        for entity_id, config in cover_config.items():
            position = config.get(CONF_COVER_POSITION)
            tilt_position = config.get(CONF_COVER_TILT_POSITION)

            if position is not None:
                tasks.append(
                    self._hass.services.async_call(
                        "cover",
                        "set_cover_position",
                        {"entity_id": entity_id, "position": position},
                    )
                )

            if tilt_position is not None:
                tasks.append(
                    self._hass.services.async_call(
                        "cover",
                        "set_cover_tilt_position",
                        {"entity_id": entity_id, "tilt_position": tilt_position},
                    )
                )

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ------------------------------------------------------------------
    # Auto-revert timer management
    # ------------------------------------------------------------------

    def set_auto_revert_enabled(self, mood_id: str, enabled: bool) -> None:
        """Set whether auto-revert is enabled for a mood (called by switch entity)."""
        self._auto_revert_enabled[mood_id] = enabled
        if not enabled:
            # Disable: cancel any running timer immediately
            self.cancel_auto_revert(mood_id)
        elif enabled and self._state_manager.can_restore(mood_id):
            # Enable while mood is already active (has saved state) — start timer now
            self._schedule_auto_revert(mood_id)

    def set_auto_revert_duration(self, mood_id: str, duration_min: int) -> None:
        """Set the auto-revert duration for a mood in minutes (called by number entity)."""
        self._auto_revert_duration[mood_id] = duration_min

    def is_auto_revert_enabled(self, mood_id: str) -> bool:
        """Check if auto-revert is enabled for a mood."""
        return self._auto_revert_enabled.get(mood_id, False)

    def get_auto_revert_duration(self, mood_id: str) -> int:
        """Get the configured auto-revert duration in minutes for a mood."""
        return self._auto_revert_duration.get(mood_id, DEFAULT_REVERT_DURATION_MIN)

    def get_auto_revert_remaining(self, mood_id: str) -> float | None:
        """Get remaining seconds until auto-revert, or None if no timer is active."""
        deadline = self._revert_deadlines.get(mood_id)
        if deadline is None:
            return None
        remaining = deadline - time.monotonic()
        return max(0.0, remaining)

    def is_timer_active(self, mood_id: str) -> bool:
        """Check if an auto-revert timer is currently running."""
        return mood_id in self._revert_deadlines

    def cancel_auto_revert(self, mood_id: str) -> bool:
        """Cancel the auto-revert timer for a mood without restoring.

        Returns True if a timer was cancelled, False if none was active.
        """
        cancel_cb = self._revert_timers.pop(mood_id, None)
        self._revert_deadlines.pop(mood_id, None)
        if cancel_cb is not None:
            cancel_cb()
            return True
        return False

    def _schedule_auto_revert(self, mood_id: str, duration_override: int | None = None) -> None:
        """Schedule an auto-revert timer for a mood.

        Args:
            mood_id: The mood identifier.
            duration_override: Override duration in minutes. If None, uses the
                               mood's switch/number entity state.
        """
        from homeassistant.helpers.event import async_call_later

        # Cancel any existing timer for this mood
        self.cancel_auto_revert(mood_id)

        # Determine duration
        if duration_override is not None:
            duration_min = duration_override
        elif self._auto_revert_enabled.get(mood_id, False):
            duration_min = self._auto_revert_duration.get(mood_id, DEFAULT_REVERT_DURATION_MIN)
        else:
            # Auto-revert not enabled and no override — do nothing
            return

        delay_seconds = duration_min * 60

        # Schedule the callback
        cancel = async_call_later(
            self._hass, delay_seconds, self._make_revert_callback(mood_id)
        )

        self._revert_timers[mood_id] = cancel
        self._revert_deadlines[mood_id] = time.monotonic() + delay_seconds
        LOGGER.debug(
            "Auto-revert timer scheduled for mood '%s' in %d minutes",
            mood_id,
            duration_min,
        )

    def _make_revert_callback(self, mood_id: str):
        """Create a callback for async_call_later that reverts a mood."""

        async def _revert_callback(_now) -> None:
            """Revert the mood when the timer fires."""
            # Clean up timer tracking
            self._revert_timers.pop(mood_id, None)
            self._revert_deadlines.pop(mood_id, None)

            # Restore the previous state
            success = await self._state_manager.restore_previous(mood_id)
            if success:
                LOGGER.info("Auto-reverted mood '%s'", mood_id)
            else:
                LOGGER.warning(
                    "Auto-revert for mood '%s' failed: no saved state", mood_id
                )

        return _revert_callback

    # ------------------------------------------------------------------

    async def async_unload(self) -> None:
        """Unload the manager."""
        # Cancel all active auto-revert timers
        for mood_id in list(self._revert_timers):
            self.cancel_auto_revert(mood_id)
        self._state_manager.clear_all_states()
        self._moods.clear()
