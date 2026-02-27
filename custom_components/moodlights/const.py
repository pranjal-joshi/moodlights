"""Constants for MoodLights."""

DOMAIN = "moodlights"

VERSION = "1.0.0"

ATTRIBUTION = "MoodLights - Easy mood-based light management"

ATTR_CURRENT_PRESET = "current_preset"
ATTR_PREVIOUS_PRESET = "previous_preset"
ATTR_CAN_RESTORE = "can_restore"
ATTR_LIGHT_ENTITIES = "light_entities"
ATTR_EXCLUSION_HELPERS = "exclusion_helpers"
ATTR_EXCLUSION_STATES = "exclusion_states"
ATTR_CONFIRMATION_MODE = "confirmation_mode"
ATTR_AUTO_ACTIVATE = "auto_activate"
ATTR_TRANSITION = "transition"

CONF_MOODS = "moods"
CONF_NAME = "name"
CONF_ICON = "icon"
CONF_LIGHT_ENTITIES = "light_entities"
CONF_LIGHT_AREA = "light_area"
CONF_LIGHT_PATTERN = "light_pattern"
CONF_PRESETS = "presets"
CONF_PRESET_NAME = "name"
CONF_PRESET_BRIGHTNESS = "brightness"
CONF_PRESET_COLOR_TEMP = "color_temp"
CONF_PRESET_RGB_COLOR = "rgb_color"
CONF_PRESET_TRANSITION = "transition"
CONF_EXCLUSION_HELPERS = "exclusion_helpers"
CONF_EXCLUSION_STATES = "exclusion_states"
CONF_EXCLUSION_ENTITIES = "exclusion_entities"
CONF_CONFIRMATION_MODE = "confirmation_mode"
CONF_AUTO_ACTIVATE = "auto_activate"
CONF_AUTO_ACTIVATE_TIME = "time"
CONF_AUTO_ACTIVATE_DAYS = "days"
CONF_SAVE_STATES = "save_states"
CONF_MAX_SAVED_STATES = "max_saved_states"

CONFIRMATION_NONE = "none"
CONFIRMATION_NOTIFY = "notify"
CONFIRMATION_APPROVE = "approve"

CONFIRMATION_MODES = [CONFIRMATION_NONE, CONFIRMATION_NOTIFY, CONFIRMATION_APPROVE]

DEFAULT_CONFIRMATION = CONFIRMATION_NONE
DEFAULT_SAVE_STATES = True
DEFAULT_MAX_SAVED_STATES = 3
DEFAULT_TRANSITION = 1.0

ICON_MOOD = "mdi:lightbulb-group"
ICON_MOOD_ACTIVE = "mdi:lightbulb-group-outline"

MOODS_KEY = "moods"
