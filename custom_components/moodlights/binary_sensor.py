"""Binary sensor platform for MoodLights."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ATTR_CONFIGURED_COVERS,
    ATTR_CONFIGURED_LIGHTS,
    ATTR_MISMATCHED_COVERS,
    ATTR_MISMATCHED_LIGHTS,
    ATTR_MOOD_NAME,
    CONF_COVER_POSITION,
    CONF_COVER_TILT_POSITION,
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_EFFECT,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    DOMAIN,
)
from .manager import MoodConfig, MoodManager

if TYPE_CHECKING:
    from .config_flow import MoodLightsConfigEntry

# Tolerance for cover position matching (motor imprecision)
_COVER_POSITION_TOLERANCE = 2


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MoodLightsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MoodLights binary sensor entities."""
    manager: MoodManager = entry.runtime_data
    entry_id = entry.entry_id

    entities: list[BinarySensorEntity] = []
    for _mood_id, mood_config in manager.get_all_moods().items():
        entities.append(MoodActiveBinarySensor(mood_config, entry_id))

    async_add_entities(entities)


def _brightness_pct_to_raw(pct: int) -> int:
    """Convert brightness percentage (1-100) to raw HA value (0-255)."""
    return round(pct / 100 * 255)


class MoodActiveBinarySensor(BinarySensorEntity):
    """Binary sensor that is ON when all lights and covers match the mood's configured target."""

    _attr_has_entity_name = True
    _attr_name = "Active"
    _attr_icon = "mdi:lightbulb-group"

    def __init__(self, mood_config: MoodConfig, entry_id: str) -> None:
        """Initialize the binary sensor."""
        self._config = mood_config
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{mood_config.mood_id}_active"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry_id}_{mood_config.mood_id}")},
            name=mood_config.name,
            manufacturer="Mood Lights",
            model="Mood",
        )
        self._unsub_listeners: list = []
        self._mismatched_lights: list[str] = []
        self._mismatched_covers: list[str] = []

    @property
    def is_on(self) -> bool:
        """Return True when all configured lights and covers match their target state."""
        return len(self._mismatched_lights) == 0 and len(self._mismatched_covers) == 0

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            ATTR_MOOD_NAME: self._config.name,
            ATTR_CONFIGURED_LIGHTS: list(self._config.light_config.keys()),
            ATTR_MISMATCHED_LIGHTS: list(self._mismatched_lights),
            ATTR_CONFIGURED_COVERS: list(self._config.cover_config.keys()),
            ATTR_MISMATCHED_COVERS: list(self._mismatched_covers),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to state change events when entity is added."""
        light_entities = list(self._config.light_config.keys())
        cover_entities = list(self._config.cover_config.keys())

        if light_entities:
            unsub = async_track_state_change_event(
                self.hass,
                light_entities,
                self._handle_state_change,
            )
            self._unsub_listeners.append(unsub)

        if cover_entities:
            unsub = async_track_state_change_event(
                self.hass,
                cover_entities,
                self._handle_state_change,
            )
            self._unsub_listeners.append(unsub)

        # Compute initial state
        self._mismatched_lights, self._mismatched_covers = self._compute_mismatched()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe all listeners when entity is removed."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    @callback
    def _handle_state_change(self, event: Event) -> None:  # noqa: ARG002
        """Handle a state change event for any light or cover in this mood."""
        self._mismatched_lights, self._mismatched_covers = self._compute_mismatched()
        self.async_write_ha_state()

    def _compute_mismatched(self) -> tuple[list[str], list[str]]:
        """Return (mismatched_lights, mismatched_covers) entity_id lists."""
        mismatched_lights: list[str] = []
        mismatched_covers: list[str] = []

        for entity_id, config in self._config.light_config.items():
            if not self._is_light_matching(entity_id, config):
                mismatched_lights.append(entity_id)

        for entity_id, config in self._config.cover_config.items():
            if not self._is_cover_matching(entity_id, config):
                mismatched_covers.append(entity_id)

        return mismatched_lights, mismatched_covers

    def _is_light_matching(self, entity_id: str, config: dict) -> bool:
        """Return True if the light's current state matches the mood config exactly.

        Only attributes that are present in the mood config are checked.
        Attributes not configured by the mood are ignored.
        """
        state = self.hass.states.get(entity_id)

        # Unavailable or unknown lights are never considered matching
        if state is None or state.state in ("unavailable", "unknown"):
            return False

        # --- Power ---
        power = config.get(CONF_LIGHT_POWER)
        if power is not None:
            expected_state = "on" if power else "off"
            if state.state != expected_state:
                return False

        # If the light is off and power is configured as off, it matches — skip attr checks
        if state.state == "off":
            return True

        attrs = state.attributes

        # --- Brightness ---
        brightness_pct = config.get(CONF_LIGHT_BRIGHTNESS)
        if brightness_pct is not None:
            current_brightness = attrs.get("brightness")
            if current_brightness is None:
                return False
            if current_brightness != _brightness_pct_to_raw(brightness_pct):
                return False

        # --- Effect ---
        effect = config.get(CONF_LIGHT_EFFECT)
        if effect is not None:
            if attrs.get("effect") != effect:
                return False
            # When an effect is configured, skip colour checks (matches manager logic)
            return True

        # --- Color temperature (Kelvin) ---
        color_temp_kelvin = config.get(CONF_LIGHT_COLOR_TEMP_KELVIN)
        if color_temp_kelvin is not None:
            if attrs.get("color_temp_kelvin") != color_temp_kelvin:
                return False
        else:
            # --- RGB color (only checked if color_temp_kelvin not configured) ---
            rgb_color = config.get(CONF_LIGHT_RGB_COLOR)
            if rgb_color is not None:
                current_rgb = attrs.get("rgb_color")
                if current_rgb is None:
                    return False
                if tuple(current_rgb) != tuple(rgb_color):
                    return False

        return True

    def _is_cover_matching(self, entity_id: str, config: dict) -> bool:
        """Return True if the cover's current state matches the mood config.

        Position and tilt are compared with a tolerance of ±2% to account for
        motor imprecision. Only attributes present in the config are checked.
        """
        state = self.hass.states.get(entity_id)

        if state is None or state.state in ("unavailable", "unknown"):
            return False

        attrs = state.attributes

        # --- Position ---
        target_position = config.get(CONF_COVER_POSITION)
        if target_position is not None:
            current_position = attrs.get("current_position")
            if current_position is None:
                return False
            if abs(current_position - target_position) > _COVER_POSITION_TOLERANCE:
                return False

        # --- Tilt position ---
        target_tilt = config.get(CONF_COVER_TILT_POSITION)
        if target_tilt is not None:
            current_tilt = attrs.get("current_tilt_position")
            if current_tilt is None:
                return False
            if abs(current_tilt - target_tilt) > _COVER_POSITION_TOLERANCE:
                return False

        return True
