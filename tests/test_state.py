"""Tests for state management."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from custom_components.moodlights.state import StateManager, LightState, MoodState


class TestStateManager:
    """Test StateManager class."""

    def test_initialization(self, hass):
        """Test state manager initialization."""
        manager = StateManager(hass, max_states=5)
        assert manager._max_states == 5
        assert manager._states == {}

    def test_save_current_state(self, hass):
        """Test saving current light state."""
        manager = StateManager(hass)
        
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {
            "brightness": 255,
            "color_temp": 370,
            "rgb_color": (255, 128, 0),
            "xy_color": (0.5, 0.4),
            "supported_color_modes": ["brightness", "color_temp", "rgb"],
        }
        
        hass.states.get.return_value = mock_state
        
        result = manager.save_current_state(
            "mood_0", "Bright", ["light.living_room"]
        )
        
        assert result is not None
        assert result.mood_id == "mood_0"
        assert result.preset_name == "Bright"
        assert len(result.light_states) == 1
        assert result.light_states[0].entity_id == "light.living_room"
        assert result.light_states[0].brightness == 255

    def test_save_multiple_states(self, hass):
        """Test saving multiple states."""
        manager = StateManager(hass, max_states=3)
        
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"brightness": 255}
        hass.states.get.return_value = mock_state
        
        manager.save_current_state("mood_0", "Preset1", ["light.test"])
        manager.save_current_state("mood_0", "Preset2", ["light.test"])
        manager.save_current_state("mood_0", "Preset3", ["light.test"])
        manager.save_current_state("mood_0", "Preset4", ["light.test"])
        
        assert manager.get_state_count("mood_0") == 3

    def test_can_restore(self, hass):
        """Test can_restore method."""
        manager = StateManager(hass)
        
        assert not manager.can_restore("mood_0")
        
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"brightness": 255}
        hass.states.get.return_value = mock_state
        
        manager.save_current_state("mood_0", "Preset1", ["light.test"])
        manager.save_current_state("mood_0", "Preset2", ["light.test"])
        
        assert manager.can_restore("mood_0")

    def test_get_previous_state(self, hass):
        """Test getting previous state."""
        manager = StateManager(hass)
        
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"brightness": 255}
        hass.states.get.return_value = mock_state
        
        manager.save_current_state("mood_0", "Current", ["light.test"])
        manager.save_current_state("mood_0", "Previous", ["light.test"])
        
        prev = manager.get_previous_state("mood_0")
        assert prev is not None
        assert prev.preset_name == "Previous"

    def test_clear_states(self, hass):
        """Test clearing states."""
        manager = StateManager(hass)
        
        mock_state = MagicMock()
        mock_state.state = "on"
        mock_state.attributes = {"brightness": 255}
        hass.states.get.return_value = mock_state
        
        manager.save_current_state("mood_0", "Test", ["light.test"])
        assert manager.get_state_count("mood_0") == 1
        
        manager.clear_states("mood_0")
        assert manager.get_state_count("mood_0") == 0
