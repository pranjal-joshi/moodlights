"""Constants for MoodLights."""

DOMAIN = "moodlights"

VERSION = "0.1.0"

ATTRIBUTION = "MoodLights - Easy mood-based light management"

CONF_MOOD_NAME = "name"
CONF_LIGHT_CONFIG = "light_config"
CONF_LIGHTS = "lights"

CONF_LIGHT_POWER = "power"
CONF_LIGHT_BRIGHTNESS = "brightness"
CONF_LIGHT_COLOR_TEMP = "color_temp"
CONF_LIGHT_COLOR_TEMP_KELVIN = "color_temp_kelvin"
CONF_LIGHT_RGB_COLOR = "rgb_color"

LIGHT_POWER_ON = "on"
LIGHT_POWER_OFF = "off"
LIGHT_POWER_DONT_CHANGE = "dont_change"

MIN_BRIGHTNESS = 1
MAX_BRIGHTNESS = 100
MIN_COLOR_TEMP_KELVIN = 2700
MAX_COLOR_TEMP_KELVIN = 65000

ICON_MOOD = "mdi:lightbulb-group"
