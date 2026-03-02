"""Config flow for MoodLights."""
from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_CONFIG,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    CONF_LIGHTS,
    CONF_MOOD_NAME,
    DOMAIN,
    LIGHT_POWER_DONT_CHANGE,
    LIGHT_POWER_OFF,
    LIGHT_POWER_ON,
    MAX_BRIGHTNESS,
    MAX_COLOR_TEMP_KELVIN,
    MIN_BRIGHTNESS,
    MIN_COLOR_TEMP_KELVIN,
)

if TYPE_CHECKING:
    from .manager import MoodManager

    MoodLightsConfigEntry = config_entries.ConfigEntry[MoodManager]

CONF_MAX_STATES = "max_states"
CONF_DEFAULT_BRIGHTNESS = "default_brightness"


class MoodLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoodLights."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.moods: list[dict] = []
        self.current_mood_name: str = ""
        self.selected_lights: list[str] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return MoodLightsOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step - enter mood name."""
        if user_input is not None:
            self.current_mood_name = user_input.get(CONF_MOOD_NAME, "New Mood")
            return await self.async_step_select_lights()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_MOOD_NAME,
                    default=(user_input or {}).get(CONF_MOOD_NAME, vol.UNDEFINED),
                ): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }),
            last_step=False,
        )

    async def async_step_import(self, _import_info: dict | None) -> config_entries.ConfigFlowResult:
        """Handle import from YAML."""
        return await self.async_step_user(None)

    async def async_step_select_lights(self, user_input: dict | None = None) -> config_entries.ConfigFlowResult:
        """Select light entities for this mood."""
        if user_input is not None:
            self.selected_lights = user_input.get(CONF_LIGHTS, [])

            if not self.selected_lights:
                return self.async_show_form(
                    step_id="select_lights",
                    data_schema=self._get_lights_schema(),
                    errors={"base": "no_lights_selected"},
                    last_step=False,
                )

            return await self.async_step_configure_lights()

        return self.async_show_form(
            step_id="select_lights",
            data_schema=self._get_lights_schema(default_lights=self.selected_lights),
            last_step=False,
        )

    def _get_lights_schema(self, default_lights: list[str] | None = None) -> vol.Schema:
        """Get schema for selecting lights."""
        lights_key = (
            vol.Required(CONF_LIGHTS, default=default_lights)
            if default_lights
            else vol.Required(CONF_LIGHTS)
        )
        return vol.Schema({
            lights_key: selector.EntitySelector(
                selector.EntitySelectorConfig(
                    multiple=True,
                    filter=selector.EntityFilterSelectorConfig(domain="light"),
                )
            ),
        })

    async def async_step_configure_lights(self, user_input: dict | None = None) -> config_entries.ConfigFlowResult:
        """Configure all lights — optional fields are left blank if not applied."""
        if user_input is not None:
            light_configs = {}

            for entity_id in self.selected_lights:
                config = {}

                light_state = self.hass.states.get(entity_id)
                light_name = light_state.name if light_state else entity_id
                safe_name = self._get_safe_name(light_name)

                # Power (always present)
                power_key = f"{safe_name}_power"
                config[CONF_LIGHT_POWER] = user_input.get(power_key, LIGHT_POWER_DONT_CHANGE)

                # Brightness — only save if user provided a value
                brightness_value = user_input.get(f"{safe_name}_brightness")
                if brightness_value is not None:
                    config[CONF_LIGHT_BRIGHTNESS] = int(brightness_value)

                # Colour Temperature — only save if user provided a value
                colortemp_value = user_input.get(f"{safe_name}_colortemp")
                if colortemp_value is not None:
                    config[CONF_LIGHT_COLOR_TEMP_KELVIN] = int(colortemp_value)

                # RGB Color — only save if user provided a value
                rgb_value = user_input.get(f"{safe_name}_rgb")
                if rgb_value is not None:
                    config[CONF_LIGHT_RGB_COLOR] = list(rgb_value)

                light_configs[entity_id] = config

            mood_data = {
                CONF_MOOD_NAME: self.current_mood_name,
                CONF_LIGHTS: self.selected_lights,
                CONF_LIGHT_CONFIG: light_configs,
            }

            self.moods.append(mood_data)

            # In reconfigure: update + reload the existing entry
            if self.source == SOURCE_RECONFIGURE:
                config_entry = self._get_reconfigure_entry()
                return self.async_update_reload_and_abort(
                    config_entry,
                    title=self.current_mood_name,
                    unique_id=self._get_safe_name(self.current_mood_name),
                    data={"moods": self.moods},
                )

            # Normal setup: set unique_id and create a new entry
            await self.async_set_unique_id(self._get_safe_name(self.current_mood_name))
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self.current_mood_name,
                data={"moods": self.moods},
            )

        # Load existing light_config for pre-filling during reconfigure
        existing_light_config: dict = {}
        if self.source == SOURCE_RECONFIGURE:
            reconfigure_entry = self._get_reconfigure_entry()
            moods = reconfigure_entry.data.get("moods", [])
            if moods:
                existing_light_config = moods[0].get(CONF_LIGHT_CONFIG, {})

        # Build schema — optional fields have no default (renders blank); pre-fill from existing data on reconfigure
        schema = {}

        for entity_id in self.selected_lights:
            light_state = self.hass.states.get(entity_id)
            light_name = light_state.name if light_state else entity_id
            safe_name = self._get_safe_name(light_name)
            supported_modes = light_state.attributes.get("supported_color_modes", []) if light_state else []
            stored = existing_light_config.get(entity_id, {})

            # Detect capabilities
            has_brightness = bool(supported_modes) and not (
                len(supported_modes) == 1 and supported_modes[0] == "onoff"
            )
            has_color_temp = "color_temp" in supported_modes
            has_rgb = any(mode in supported_modes for mode in ("rgb", "rgbw", "rgbww", "hs", "xy"))

            # Get min/max kelvin from light attributes
            min_kelvin = light_state.attributes.get("min_color_temp_kelvin", MIN_COLOR_TEMP_KELVIN) if light_state else MIN_COLOR_TEMP_KELVIN
            max_kelvin = light_state.attributes.get("max_color_temp_kelvin", MAX_COLOR_TEMP_KELVIN) if light_state else MAX_COLOR_TEMP_KELVIN

            # Power selector (always visible) — pre-fill from stored config
            stored_power = stored.get(CONF_LIGHT_POWER, LIGHT_POWER_DONT_CHANGE)
            schema[vol.Required(f"{safe_name}_power", default=stored_power)] = (
                selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": LIGHT_POWER_ON, "label": "Turn On"},
                            {"value": LIGHT_POWER_OFF, "label": "Turn Off"},
                            {"value": LIGHT_POWER_DONT_CHANGE, "label": "Don't Change"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            )

            # Brightness — plain optional, no default; pre-fill if stored
            if has_brightness:
                stored_brightness = stored.get(CONF_LIGHT_BRIGHTNESS)
                brightness_key = (
                    vol.Optional(f"{safe_name}_brightness", default=stored_brightness)
                    if stored_brightness is not None
                    else vol.Optional(f"{safe_name}_brightness")
                )
                schema[brightness_key] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_BRIGHTNESS,
                        max=MAX_BRIGHTNESS,
                        step=1,
                        unit_of_measurement="%",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                )

            # Colour Temperature — plain optional, no default; pre-fill if stored
            if has_color_temp:
                stored_colortemp = stored.get(CONF_LIGHT_COLOR_TEMP_KELVIN)
                colortemp_key = (
                    vol.Optional(f"{safe_name}_colortemp", default=stored_colortemp)
                    if stored_colortemp is not None
                    else vol.Optional(f"{safe_name}_colortemp")
                )
                schema[colortemp_key] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=min_kelvin,
                        max=max_kelvin,
                        step=100,
                        unit_of_measurement="K",
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                )

            # RGB Color — plain optional, no default; pre-fill if stored
            if has_rgb:
                stored_rgb = stored.get(CONF_LIGHT_RGB_COLOR)
                rgb_key = (
                    vol.Optional(f"{safe_name}_rgb", default=stored_rgb)
                    if stored_rgb is not None
                    else vol.Optional(f"{safe_name}_rgb")
                )
                schema[rgb_key] = selector.ColorRGBSelector()

        return self.async_show_form(
            step_id="configure_lights",
            data_schema=vol.Schema(schema),
            last_step=True,
        )

    def _get_safe_name(self, name: str) -> str:
        """Convert a name to a safe key format."""
        return name.replace(" ", "_").replace(".", "_").replace("-", "_").lower()

    async def async_step_reconfigure(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Seed existing data and start the full reconfigure flow from step 1."""
        config_entry = self._get_reconfigure_entry()
        moods = config_entry.data.get("moods", [])
        current_mood = moods[0] if moods else {}

        # Pre-fill instance state from current entry
        self.current_mood_name = current_mood.get(CONF_MOOD_NAME, "")
        self.selected_lights = current_mood.get(CONF_LIGHTS, [])
        self.moods = []

        # Show mood name form pre-filled with existing name
        if user_input is not None:
            self.current_mood_name = user_input.get(CONF_MOOD_NAME, self.current_mood_name)
            return await self.async_step_select_lights()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(CONF_MOOD_NAME, default=self.current_mood_name): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }),
            last_step=False,
        )

class MoodLightsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles the options flow for MoodLights."""

    async def async_step_init(self, user_input: dict | None = None) -> config_entries.ConfigFlowResult:
        """Handle options flow - show menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["general_options", "about"],
        )

    async def async_step_general_options(self, user_input: dict | None = None) -> config_entries.ConfigFlowResult:
        """Handle general options step."""
        options = dict(self.config_entry.options)

        if user_input is not None:
            options.update(user_input)
            return self.async_create_entry(title="", data=options)

        data_schema = vol.Schema({
            vol.Optional(
                CONF_MAX_STATES,
                default=options.get(CONF_MAX_STATES, 3),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=10,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_DEFAULT_BRIGHTNESS,
                default=options.get(CONF_DEFAULT_BRIGHTNESS, 100),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=100,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
        })

        return self.async_show_form(
            step_id="general_options",
            data_schema=data_schema,
            last_step=True,
        )

    async def async_step_about(self, user_input: dict | None = None) -> config_entries.ConfigFlowResult:
        """Handle about step."""
        return self.async_show_form(
            step_id="about",
            data_schema=vol.Schema({}),
            last_step=True,
        )
