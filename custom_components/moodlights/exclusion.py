"""Exclusion engine for MoodLights."""
from __future__ import annotations

from homeassistant.core import HomeAssistant


class ExclusionEngine:
    """Handles exclusion rules for mood activation."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the exclusion engine."""
        self._hass = hass

    async def check_exclusions(
        self,
        exclusion_helpers: list[str],
        exclusion_states: list[str],
    ) -> tuple[bool, str]:
        """Check if mood should be blocked by exclusions.
        
        Returns:
            tuple: (is_blocked, reason)
        """
        for helper in exclusion_helpers:
            state = self._hass.states.get(helper)
            if state and state.state == "on":
                return True, f"Helper {helper} is active"

        for entity_id in exclusion_states:
            state = self._hass.states.get(entity_id)
            if state is None:
                continue

            domain = entity_id.split(".")[0]

            if domain == "media_player":
                if state.state in ["playing", "paused"]:
                    return True, f"Media player {entity_id} is {state.state}"

            elif domain == "person":
                if state.state == "home":
                    return True, f"Person {entity_id} is at home"

            elif domain == "sensor":
                sensor_state = state.state
                if isinstance(sensor_state, str) and "occupied" in sensor_state.lower():
                    return True, f"Sensor {entity_id} shows occupied"

            elif domain == "binary_sensor":
                if state.state == "on":
                    return True, f"Binary sensor {entity_id} is on"

        return False, ""

    def get_active_exclusions(
        self,
        exclusion_helpers: list[str],
        exclusion_states: list[str],
    ) -> list[str]:
        """Get list of currently active exclusions."""
        active = []

        for helper in exclusion_helpers:
            state = self._hass.states.get(helper)
            if state and state.state == "on":
                active.append(helper)

        for entity_id in exclusion_states:
            state = self._hass.states.get(entity_id)
            if state is None:
                continue

            domain = entity_id.split(".")[0]

            if domain == "media_player":
                if state.state in ["playing", "paused"]:
                    active.append(f"{entity_id} (playing)")

            elif domain == "person":
                if state.state == "home":
                    active.append(f"{entity_id} (home)")

            elif domain == "binary_sensor":
                if state.state == "on":
                    active.append(entity_id)

        return active
