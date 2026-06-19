"""Switch platform for MoodLights — auto-revert timer toggle per mood."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .manager import MoodConfig, MoodManager

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry

SIGNAL_REVERT_TIMER_CHANGED = "moodlights_revert_timer_{}"


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    entry: MoodLightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights switch entities."""
    manager: MoodManager = entry.runtime_data
    entry_id = entry.entry_id

    entities: list[SwitchEntity] = []
    for _mood_id, mood_config in manager.get_all_moods().items():
        entities.append(MoodAutoRevertSwitch(mood_config, manager, entry_id))

    async_add_entities(entities)


class MoodAutoRevertSwitch(SwitchEntity, RestoreEntity):
    """Switch to enable/disable auto-revert timer for a mood."""

    _attr_has_entity_name = True
    _attr_name = "Revert Timer"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self, mood_config: MoodConfig, manager: MoodManager, entry_id: str
    ) -> None:
        """Initialize the auto-revert switch."""
        self._config = mood_config
        self._manager = manager
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_revert_timer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{mood_config.mood_id}")},
            name=mood_config.name,
            manufacturer="Mood Lights",
            model="Mood",
        )
        self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return True if auto-revert is enabled."""
        return self._is_on

    async def async_added_to_hass(self) -> None:
        """Restore previous state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._is_on = last_state.state == "on"
        # Sync with manager
        self._manager.set_auto_revert_enabled(self._config.mood_id, self._is_on)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable auto-revert for this mood."""
        self._is_on = True
        self._manager.set_auto_revert_enabled(self._config.mood_id, True)
        self.async_write_ha_state()
        # Notify dependent entities (e.g. number entity becomes available)
        async_dispatcher_send(
            self.hass, SIGNAL_REVERT_TIMER_CHANGED.format(self._config.mood_id)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable auto-revert for this mood (also cancels active timer)."""
        self._is_on = False
        self._manager.set_auto_revert_enabled(self._config.mood_id, False)
        self.async_write_ha_state()
        # Notify dependent entities (e.g. number entity becomes unavailable)
        async_dispatcher_send(
            self.hass, SIGNAL_REVERT_TIMER_CHANGED.format(self._config.mood_id)
        )
