"""Number platform for MoodLights — auto-revert duration setting per mood."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DEFAULT_REVERT_DURATION_MIN,
    DOMAIN,
    MAX_REVERT_DURATION_MIN,
    MIN_REVERT_DURATION_MIN,
)
from .manager import MoodConfig, MoodManager
from .switch import SIGNAL_REVERT_TIMER_CHANGED

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MoodLightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights number entities."""
    manager: MoodManager = entry.runtime_data
    entry_id = entry.entry_id

    entities: list[NumberEntity] = []
    for _mood_id, mood_config in manager.get_all_moods().items():
        entities.append(MoodRevertAfterNumber(mood_config, manager, entry_id))

    async_add_entities(entities)


class MoodRevertAfterNumber(NumberEntity, RestoreEntity):
    """Number entity to set auto-revert duration in minutes for a mood.

    Greyed out (unavailable) when the mood's Revert Timer switch is OFF.
    """

    _attr_has_entity_name = True
    _attr_name = "Revert After"
    _attr_icon = "mdi:clock-edit-outline"
    _attr_native_min_value = MIN_REVERT_DURATION_MIN
    _attr_native_max_value = MAX_REVERT_DURATION_MIN
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the revert after number."""
        self._config = mood_config
        self._manager = manager
        self._entry_id = entry_id
        self._attr_unique_id = (
            f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_revert_after"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{mood_config.mood_id}")},
            name=mood_config.name,
            manufacturer="Mood Lights",
            model="Mood",
        )
        self._value = DEFAULT_REVERT_DURATION_MIN

    @property
    def available(self) -> bool:
        """Only available when the Revert Timer switch is ON."""
        return self._manager.is_auto_revert_enabled(self._config.mood_id)

    @property
    def native_value(self) -> float:
        """Return the current duration value in minutes."""
        return self._value

    async def async_added_to_hass(self) -> None:
        """Restore previous value on startup and listen for switch changes."""
        await super().async_added_to_hass()

        # Restore persisted value
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            "unknown",
            "unavailable",
            None,
        ):
            try:
                self._value = int(float(last_state.state))
            except (ValueError, TypeError):
                self._value = DEFAULT_REVERT_DURATION_MIN

        # Sync with manager
        self._manager.set_auto_revert_duration(self._config.mood_id, self._value)

        # Listen for switch state changes to update availability
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_REVERT_TIMER_CHANGED.format(self._config.mood_id),
                self._handle_switch_changed,
            )
        )

    @callback
    def _handle_switch_changed(self) -> None:
        """Re-render when the Revert Timer switch changes."""
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set the duration value."""
        self._value = int(value)
        self._manager.set_auto_revert_duration(self._config.mood_id, self._value)
        self.async_write_ha_state()
