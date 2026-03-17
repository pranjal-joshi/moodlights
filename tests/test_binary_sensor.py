"""Tests for MoodActiveBinarySensor."""
from unittest.mock import MagicMock, patch

import pytest

from custom_components.moodlights.binary_sensor import MoodActiveBinarySensor, _brightness_pct_to_raw
from custom_components.moodlights.manager import MoodConfig


ENTRY_ID = "test_entry_id"


def _make_mood(light_config: dict) -> MoodConfig:
    """Helper to build a MoodConfig with the given light_config."""
    return MoodConfig(
        mood_id="mood_0",
        name="Movie Night",
        lights=list(light_config.keys()),
        light_config=light_config,
    )


def _make_sensor(light_config: dict) -> MoodActiveBinarySensor:
    """Helper to build a sensor instance (not added to hass)."""
    mood = _make_mood(light_config)
    sensor = MoodActiveBinarySensor(mood, ENTRY_ID)
    return sensor


def _attach_hass(sensor: MoodActiveBinarySensor, states: dict) -> MagicMock:
    """Attach a mock hass with the given entity_id -> state dict."""
    hass = MagicMock()
    hass.states.get.side_effect = lambda eid: states.get(eid)
    sensor.hass = hass
    return hass


def _mock_state(state: str, **attributes) -> MagicMock:
    mock = MagicMock()
    mock.state = state
    mock.attributes = attributes
    return mock


# ---------------------------------------------------------------------------
# _brightness_pct_to_raw helper
# ---------------------------------------------------------------------------


class TestBrightnessPctToRaw:
    def test_100_pct_is_255(self):
        assert _brightness_pct_to_raw(100) == 255

    def test_50_pct_is_128(self):
        assert _brightness_pct_to_raw(50) == 128

    def test_1_pct_is_3(self):
        assert _brightness_pct_to_raw(1) == 3


# ---------------------------------------------------------------------------
# _is_light_matching
# ---------------------------------------------------------------------------


class TestIsLightMatching:
    def test_matching_power_on(self):
        sensor = _make_sensor({"light.test": {"power": True}})
        _attach_hass(sensor, {"light.test": _mock_state("on")})

        assert sensor._is_light_matching("light.test", {"power": True}) is True

    def test_mismatching_power_on(self):
        sensor = _make_sensor({"light.test": {"power": True}})
        _attach_hass(sensor, {"light.test": _mock_state("off")})

        assert sensor._is_light_matching("light.test", {"power": True}) is False

    def test_matching_power_off(self):
        sensor = _make_sensor({"light.test": {"power": False}})
        _attach_hass(sensor, {"light.test": _mock_state("off")})

        assert sensor._is_light_matching("light.test", {"power": False}) is True

    def test_unavailable_light_is_not_matching(self):
        sensor = _make_sensor({"light.test": {"power": True}})
        _attach_hass(sensor, {"light.test": _mock_state("unavailable")})

        assert sensor._is_light_matching("light.test", {"power": True}) is False

    def test_missing_light_is_not_matching(self):
        sensor = _make_sensor({"light.test": {"power": True}})
        _attach_hass(sensor, {})  # light.test returns None

        assert sensor._is_light_matching("light.test", {"power": True}) is False

    def test_matching_brightness(self):
        raw = _brightness_pct_to_raw(80)
        sensor = _make_sensor({"light.test": {"power": True, "brightness": 80}})
        _attach_hass(sensor, {"light.test": _mock_state("on", brightness=raw)})

        assert sensor._is_light_matching("light.test", {"power": True, "brightness": 80}) is True

    def test_mismatching_brightness(self):
        sensor = _make_sensor({"light.test": {"power": True, "brightness": 80}})
        _attach_hass(sensor, {"light.test": _mock_state("on", brightness=100)})

        assert sensor._is_light_matching("light.test", {"power": True, "brightness": 80}) is False

    def test_missing_brightness_attribute_is_not_matching(self):
        sensor = _make_sensor({"light.test": {"power": True, "brightness": 80}})
        # Light is on but has no brightness attribute
        _attach_hass(sensor, {"light.test": _mock_state("on")})

        assert sensor._is_light_matching("light.test", {"power": True, "brightness": 80}) is False

    def test_matching_color_temp_kelvin(self):
        sensor = _make_sensor({"light.test": {"power": True, "color_temp_kelvin": 4000}})
        _attach_hass(sensor, {"light.test": _mock_state("on", color_temp_kelvin=4000)})

        assert sensor._is_light_matching("light.test", {"power": True, "color_temp_kelvin": 4000}) is True

    def test_mismatching_color_temp_kelvin(self):
        sensor = _make_sensor({"light.test": {"power": True, "color_temp_kelvin": 4000}})
        _attach_hass(sensor, {"light.test": _mock_state("on", color_temp_kelvin=3000)})

        assert sensor._is_light_matching("light.test", {"power": True, "color_temp_kelvin": 4000}) is False

    def test_matching_rgb_color(self):
        sensor = _make_sensor({"light.test": {"power": True, "rgb_color": [255, 0, 128]}})
        _attach_hass(sensor, {"light.test": _mock_state("on", rgb_color=(255, 0, 128))})

        assert sensor._is_light_matching("light.test", {"power": True, "rgb_color": [255, 0, 128]}) is True

    def test_mismatching_rgb_color(self):
        sensor = _make_sensor({"light.test": {"power": True, "rgb_color": [255, 0, 128]}})
        _attach_hass(sensor, {"light.test": _mock_state("on", rgb_color=(0, 255, 0))})

        assert sensor._is_light_matching("light.test", {"power": True, "rgb_color": [255, 0, 128]}) is False

    def test_color_temp_takes_priority_over_rgb(self):
        """When both color_temp_kelvin and rgb_color are configured, rgb is not checked."""
        sensor = _make_sensor({"light.test": {"power": True, "color_temp_kelvin": 4000, "rgb_color": [255, 0, 0]}})
        # rgb_color doesn't match, but color_temp_kelvin does — should still match
        _attach_hass(
            sensor,
            {"light.test": _mock_state("on", color_temp_kelvin=4000, rgb_color=(0, 0, 255))},
        )

        assert sensor._is_light_matching(
            "light.test",
            {"power": True, "color_temp_kelvin": 4000, "rgb_color": [255, 0, 0]},
        ) is True

    def test_matching_effect(self):
        sensor = _make_sensor({"light.test": {"power": True, "effect": "Rainbow"}})
        _attach_hass(sensor, {"light.test": _mock_state("on", effect="Rainbow")})

        assert sensor._is_light_matching("light.test", {"power": True, "effect": "Rainbow"}) is True

    def test_mismatching_effect(self):
        sensor = _make_sensor({"light.test": {"power": True, "effect": "Rainbow"}})
        _attach_hass(sensor, {"light.test": _mock_state("on", effect="Strobe")})

        assert sensor._is_light_matching("light.test", {"power": True, "effect": "Rainbow"}) is False

    def test_unconfigured_attribute_ignored(self):
        """A light with only brightness configured should not be affected by a colour change."""
        raw = _brightness_pct_to_raw(50)
        sensor = _make_sensor({"light.test": {"power": True, "brightness": 50}})
        # rgb_color changed by user — not in mood config, should be ignored
        _attach_hass(
            sensor,
            {"light.test": _mock_state("on", brightness=raw, rgb_color=(255, 0, 0))},
        )

        assert sensor._is_light_matching("light.test", {"power": True, "brightness": 50}) is True


# ---------------------------------------------------------------------------
# _compute_mismatched / is_on
# ---------------------------------------------------------------------------


class TestComputeMismatched:
    def test_all_lights_match_returns_empty(self):
        raw = _brightness_pct_to_raw(100)
        sensor = _make_sensor({
            "light.a": {"power": True, "brightness": 100},
            "light.b": {"power": True, "brightness": 100},
        })
        _attach_hass(sensor, {
            "light.a": _mock_state("on", brightness=raw),
            "light.b": _mock_state("on", brightness=raw),
        })

        assert sensor._compute_mismatched() == []

    def test_one_light_mismatches(self):
        raw = _brightness_pct_to_raw(100)
        sensor = _make_sensor({
            "light.a": {"power": True, "brightness": 100},
            "light.b": {"power": True, "brightness": 100},
        })
        _attach_hass(sensor, {
            "light.a": _mock_state("on", brightness=raw),
            "light.b": _mock_state("on", brightness=50),  # wrong brightness
        })

        mismatched = sensor._compute_mismatched()
        assert mismatched == ["light.b"]

    def test_is_on_true_when_all_match(self):
        raw = _brightness_pct_to_raw(100)
        sensor = _make_sensor({"light.a": {"power": True, "brightness": 100}})
        _attach_hass(sensor, {"light.a": _mock_state("on", brightness=raw)})
        sensor._mismatched = sensor._compute_mismatched()

        assert sensor.is_on is True

    def test_is_on_false_when_mismatch(self):
        sensor = _make_sensor({"light.a": {"power": True, "brightness": 100}})
        _attach_hass(sensor, {"light.a": _mock_state("on", brightness=50)})
        sensor._mismatched = sensor._compute_mismatched()

        assert sensor.is_on is False


# ---------------------------------------------------------------------------
# extra_state_attributes
# ---------------------------------------------------------------------------


class TestExtraStateAttributes:
    def test_attributes_present(self):
        sensor = _make_sensor({"light.a": {"power": True}, "light.b": {"power": False}})
        sensor._mismatched = ["light.b"]

        attrs = sensor.extra_state_attributes
        assert attrs["mood_name"] == "Movie Night"
        assert set(attrs["configured_lights"]) == {"light.a", "light.b"}
        assert attrs["mismatched_lights"] == ["light.b"]


# ---------------------------------------------------------------------------
# async_will_remove_from_hass — listener cleanup
# ---------------------------------------------------------------------------


class TestListenerCleanup:
    def test_unsub_called_on_removal(self):
        sensor = _make_sensor({"light.a": {"power": True}})
        sensor.hass = MagicMock()

        unsub = MagicMock()
        sensor._unsub_listeners = [unsub]

        import asyncio
        asyncio.get_event_loop().run_until_complete(sensor.async_will_remove_from_hass())

        unsub.assert_called_once()
        assert sensor._unsub_listeners == []
