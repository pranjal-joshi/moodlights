"""State management for MoodLights."""
from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

DEFAULT_MAX_STATES = 3


@dataclass
class LightState:
    """Represents a saved light state."""

    entity_id: str
    state: str
    brightness: int | None
    color_temp: int | None
    color_temp_kelvin: int | None
    rgb_color: tuple[int, int, int] | None
    xy_color: tuple[float, float] | None
    effect: str | None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MoodState:
    """Represents a saved mood state."""

    mood_id: str
    preset_name: str = ""
    light_states: list[LightState] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class StateManager:
    """Manages saved states for mood restoration."""

    def __init__(self, hass: HomeAssistant, max_states: int = DEFAULT_MAX_STATES) -> None:
        """Initialize the state manager."""
        self._hass = hass
        self._max_states = max_states
        # Per mood_id: a deque of MoodState (most recent last)
        self._states: dict[str, deque[MoodState]] = {}

    def save_current_state(
        self,
        mood_id: str,
        preset_name: str = "",
        light_entities: list[str] | None = None,
    ) -> MoodState | None:
        """Save current state of lights before applying a mood."""
        if light_entities is None:
            light_entities = []

        light_states: list[LightState] = []

        for entity_id in light_entities:
            state = self._hass.states.get(entity_id)
            if state is None:
                continue

            light_state = LightState(
                entity_id=entity_id,
                state=state.state,
                brightness=state.attributes.get("brightness"),
                color_temp=state.attributes.get("color_temp"),
                color_temp_kelvin=state.attributes.get("color_temp_kelvin"),
                rgb_color=state.attributes.get("rgb_color"),
                xy_color=state.attributes.get("xy_color"),
                effect=state.attributes.get("effect"),
            )
            light_states.append(light_state)

        if not light_states:
            return None

        mood_state = MoodState(
            mood_id=mood_id,
            preset_name=preset_name,
            light_states=light_states,
        )

        if mood_id not in self._states:
            self._states[mood_id] = deque(maxlen=self._max_states)

        self._states[mood_id].append(mood_state)
        return mood_state

    def can_restore(self, mood_id: str) -> bool:
        """Check if a state can be restored."""
        return mood_id in self._states and len(self._states[mood_id]) > 0

    def get_state_count(self, mood_id: str) -> int:
        """Return number of saved states for a mood."""
        if mood_id not in self._states:
            return 0
        return len(self._states[mood_id])

    def get_previous_state(self, mood_id: str) -> MoodState | None:
        """Return the most recently saved state for a mood."""
        if not self.can_restore(mood_id):
            return None
        return self._states[mood_id][-1]

    async def restore_previous(self, mood_id: str) -> bool:
        """Restore the most recently saved state for a mood."""
        previous_state = self.get_previous_state(mood_id)
        if not previous_state:
            return False

        return await self._restore_state(previous_state)

    async def _restore_state(self, mood_state: MoodState) -> bool:
        """Restore a specific mood state."""
        tasks = []

        for light_state in mood_state.light_states:
            service_data: dict[str, Any] = {"entity_id": light_state.entity_id}

            if light_state.state == "off":
                service = "turn_off"
            else:
                service = "turn_on"
                if light_state.brightness is not None:
                    service_data["brightness"] = light_state.brightness
                if light_state.color_temp is not None:
                    service_data["color_temp"] = light_state.color_temp
                if light_state.color_temp_kelvin is not None:
                    service_data["color_temp_kelvin"] = light_state.color_temp_kelvin
                if light_state.rgb_color is not None:
                    service_data["rgb_color"] = light_state.rgb_color
                if light_state.xy_color is not None:
                    service_data["xy_color"] = light_state.xy_color
                if light_state.effect is not None:
                    service_data["effect"] = light_state.effect

            tasks.append(self._hass.services.async_call("light", service, service_data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            return True

        return False

    def clear_states(self, mood_id: str) -> None:
        """Clear saved states for a mood."""
        if mood_id in self._states:
            del self._states[mood_id]

    def clear_all_states(self) -> None:
        """Clear all saved states."""
        self._states = {}
