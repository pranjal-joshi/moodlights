"""Constants for MoodLights."""

DOMAIN = "moodlights"

VERSION = "0.1.0"

ATTRIBUTION = "MoodLights - Easy mood-based light management"

CONF_AREA = "area"
CONF_AREA_ID = "area_id"
CONF_LIGHT_CONFIG = "light_config"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_EXCLUSION_HELPERS = "exclusion_helpers"
CONF_SAVE_STATES = "save_states"
CONF_NAME = "name"

CONF_LIGHT_BRIGHTNESS = "brightness"
CONF_LIGHT_COLOR_TEMP = "color_temp"
CONF_LIGHT_COLOR_TEMP_KELVIN = "color_temp_kelvin"
CONF_LIGHT_RGB_COLOR = "rgb_color"
CONF_LIGHT_EFFECT = "effect"
CONF_LIGHT_POWER = "power"

LIGHT_POWER_ON = "on"
LIGHT_POWER_OFF = "off"
LIGHT_POWER_DONT_CHANGE = "dont_change"

POWER_OPTIONS = [LIGHT_POWER_ON, LIGHT_POWER_OFF, LIGHT_POWER_DONT_CHANGE]

DEFAULT_COLOR_TEMP_KELVIN = 4000
MIN_COLOR_TEMP_KELVIN = 2700
MAX_COLOR_TEMP_KELVIN = 65000

ICON_MOOD = "mdi:lightbulb-group"
ICON_MOOD_ACTIVE = "mdi:lightbulb-group-outline"
