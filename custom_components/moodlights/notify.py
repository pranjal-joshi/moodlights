"""Notification handling for MoodLights."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .const import CONFIRMATION_APPROVE


class NotificationHandler:
    """Handles actionable notifications for mood changes."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the notification handler."""
        self._hass = hass

    async def send_confirmation_request(
        self,
        mood_name: str,
        preset_name: str,
        mood_id: str,
    ) -> None:
        """Send a confirmation request for mood change."""
        actions = [
            {"action": f"moodlights_approve_{mood_id}_{preset_name}", "title": "Approve"},
            {"action": f"moodlights_deny_{mood_id}_{preset_name}", "title": "Deny"},
        ]

        await self._hass.services.async_call(
            "notify",
            "mobile_app_iphone",  
            {
                "message": f"Apply mood '{mood_name}' with preset '{preset_name}'?",
                "title": "MoodLights",
                "data": {"actions": actions},
            },
        )

    async def handle_action(self, action: str) -> tuple[str, str] | None:
        """Handle an actionable notification action.
        
        Returns:
            tuple: (mood_id, preset_name) if approved, None if denied
        """
        if action.startswith("moodlights_approve_"):
            parts = action.replace("moodlights_approve_", "").split("_", 1)
            if len(parts) == 2:
                return (parts[0], parts[1])

        return None

    async def send_notification(
        self,
        mood_name: str,
        preset_name: str,
    ) -> None:
        """Send a notification about mood change (no confirmation needed)."""
        await self._hass.services.async_call(
            "notify",
            "persistent_notification",
            {
                "message": f"Mood '{mood_name}' activated with preset '{preset_name}'",
                "title": "MoodLights",
            },
        )
