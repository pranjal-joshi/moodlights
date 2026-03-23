"""Constants for MoodLights."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "moodlights"

CONF_MOOD_NAME = "name"
CONF_LIGHT_CONFIG = "light_config"
CONF_LIGHTS = "lights"

CONF_LIGHT_POWER = "power"
CONF_LIGHT_BRIGHTNESS = "brightness"
CONF_LIGHT_COLOR_TEMP_KELVIN = "color_temp_kelvin"
CONF_LIGHT_RGB_COLOR = "rgb_color"
CONF_LIGHT_EFFECT = "effect"

LIGHT_POWER_ON = True
LIGHT_POWER_OFF = False

MIN_BRIGHTNESS = 1
MAX_BRIGHTNESS = 100
MIN_COLOR_TEMP_KELVIN = 2700
MAX_COLOR_TEMP_KELVIN = 65000

ATTR_MISMATCHED_LIGHTS = "mismatched_lights"
ATTR_CONFIGURED_LIGHTS = "configured_lights"
ATTR_MOOD_NAME = "mood_name"

# Cover config keys
CONF_COVERS = "covers"
CONF_COVER_CONFIG = "cover_config"
CONF_COVER_POSITION = "position"
CONF_COVER_TILT_POSITION = "tilt_position"

# Cover feature flag bit values (from homeassistant.components.cover.CoverEntityFeature)
COVER_SUPPORT_SET_POSITION = 4
COVER_SUPPORT_SET_TILT_POSITION = 128

# Cover-related extra state attribute keys
ATTR_CONFIGURED_COVERS = "configured_covers"
ATTR_MISMATCHED_COVERS = "mismatched_covers"
