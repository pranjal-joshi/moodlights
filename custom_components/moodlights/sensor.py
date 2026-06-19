"""Sensor platform for MoodLights — auto-revert countdown per mood."""
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .manager import MoodConfig, MoodManager

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry

# Update interval for countdown display
_UPDATE_INTERVAL = timedelta(seconds=5)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MoodLightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights sensor entities."""
    manager: MoodManager = entry.runtime_data
    entry_id = entry.entry_id

    entities: list[SensorEntity] = []
    for _mood_id, mood_config in manager.get_all_moods().items():
        entities.append(MoodRevertCountdownSensor(mood_config, manager, entry_id))

    async_add_entities(entities)


class MoodRevertCountdownSensor(SensorEntity):
    """Sensor showing remaining time until auto-revert.

    Uses device_class: duration so HA automatically displays the value
    in the most appropriate unit (seconds, minutes, hours, days).
    """

    _attr_has_entity_name = True
    _attr_name = "Revert Countdown"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "s"
    _attr_suggested_display_precision = 0

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the countdown sensor."""
        self._config = mood_config
        self._manager = manager
        self._entry_id = entry_id
        self._attr_unique_id = (
            f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_revert_countdown"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{mood_config.mood_id}")},
            name=mood_config.name,
            manufacturer="Mood Lights",
            model="Mood",
        )
        self._unsub_interval = None

    @property
    def native_value(self) -> float | None:
        """Return remaining seconds or None when no timer is active."""
        remaining = self._manager.get_auto_revert_remaining(self._config.mood_id)
        if remaining is None or remaining <= 0:
            return None
        return round(remaining)

    @property
    def icon(self) -> str:
        """Dynamic icon based on timer state."""
        if self._manager.is_timer_active(self._config.mood_id):
            return "mdi:timer-sand"
        return "mdi:timer-sand-empty"

    async def async_added_to_hass(self) -> None:
        """Start periodic updates when entity is added."""
        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._update_state,
            _UPDATE_INTERVAL,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Stop periodic updates when entity is removed."""
        if self._unsub_interval is not None:
            self._unsub_interval()
            self._unsub_interval = None

    @callback
    def _update_state(self, _now=None) -> None:
        """Periodically refresh the countdown value."""
        self.async_write_ha_state()
