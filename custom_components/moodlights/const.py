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
