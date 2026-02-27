"""Tests for exclusion engine."""
import pytest
from unittest.mock import MagicMock

from custom_components.moodlights.exclusion import ExclusionEngine


class TestExclusionEngine:
    """Test ExclusionEngine class."""

    def test_initialization(self, hass):
        """Test exclusion engine initialization."""
        engine = ExclusionEngine(hass)
        assert engine._hass is hass

    def test_check_exclusions_no_exclusions(self, hass):
        """Test check with no exclusions configured."""
        engine = ExclusionEngine(hass)
        hass.states.get.return_value = None
        
        blocked, reason = engine.check_exclusions([], [])
        
        assert blocked is False
        assert reason == ""

    def test_check_exclusions_helper_on(self, hass):
        """Test exclusion when helper is on."""
        engine = ExclusionEngine(hass)
        
        mock_helper = MagicMock()
        mock_helper.state = "on"
        hass.states.get.return_value = mock_helper
        
        blocked, reason = engine.check_exclusions(["input_boolean.do_not_disturb"], [])
        
        assert blocked is True
        assert "do_not_disturb" in reason

    def test_check_exclusions_media_player_playing(self, hass):
        """Test exclusion when media player is playing."""
        engine = ExclusionEngine(hass)
        
        mock_player = MagicMock()
        mock_player.state = "playing"
        hass.states.get.return_value = mock_player
        
        blocked, reason = engine.check_exclusions([], ["media_player.tv"])
        
        assert blocked is True
        assert "playing" in reason

    def test_check_exclusions_person_home(self, hass):
        """Test exclusion when person is home."""
        engine = ExclusionEngine(hass)
        
        mock_person = MagicMock()
        mock_person.state = "home"
        hass.states.get.return_value = mock_person
        
        blocked, reason = engine.check_exclusions([], ["person.partner"])
        
        assert blocked is True
        assert "home" in reason

    def test_check_exclusions_binary_sensor_on(self, hass):
        """Test exclusion when binary sensor is on."""
        engine = ExclusionEngine(hass)
        
        mock_sensor = MagicMock()
        mock_sensor.state = "on"
        hass.states.get.return_value = mock_sensor
        
        blocked, reason = engine.check_exclusions([], ["binary_sensor.motion"])
        
        assert blocked is True

    def test_get_active_exclusions(self, hass):
        """Test getting active exclusions."""
        engine = ExclusionEngine(hass)
        
        mock_helper = MagicMock()
        mock_helper.state = "on"
        
        mock_player = MagicMock()
        mock_player.state = "playing"
        
        def get_state(entity_id):
            if entity_id == "input_boolean.test":
                return mock_helper
            if entity_id == "media_player.tv":
                return mock_player
            return None
        
        hass.states.get.side_effect = get_state
        
        active = engine.get_active_exclusions(
            ["input_boolean.test"],
            ["media_player.tv"]
        )
        
        assert len(active) == 2
