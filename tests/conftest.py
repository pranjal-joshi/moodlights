"""Test fixtures for MoodLights."""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock


@pytest.fixture
def hass():
    """Create a mock Home Assistant instance."""
    mock_hass = MagicMock()
    mock_hass.data = {}
    mock_hass.states = MagicMock()
    mock_hass.services = MagicMock()
    return mock_hass


@pytest.fixture
def mock_state():
    """Create a mock state."""
    state = MagicMock()
    state.state = "on"
    state.attributes = {
        "brightness": 255,
        "color_temp": 370,
        "rgb_color": (255, 128, 0),
    }
    return state


@pytest.fixture
def mock_light_entity():
    """Create a mock light entity."""
    entity = MagicMock()
    entity.entity_id = "light.living_room"
    entity.state = "on"
    entity.attributes = {
        "brightness": 255,
        "color_temp": 370,
        "supported_color_modes": ["brightness", "color_temp", "rgb"],
    }
    return entity
