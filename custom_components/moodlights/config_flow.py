"""Config flow for MoodLights."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
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


class MoodLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoodLights."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.moods: list[dict] = []
        self.current_mood_name: str = ""
        self.selected_lights: list[str] = []

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step - enter mood name."""
        if user_input is not None:
            self.current_mood_name = user_input.get(CONF_MOOD_NAME, "New Mood")
            return await self.async_step_select_lights()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MOOD_NAME, description={"suggested_value": "Movie Night"}): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }),
        )

    async def async_step_select_lights(self, user_input: dict | None = None) -> FlowResult:
        """Select light entities for this mood."""
        if user_input is not None:
            self.selected_lights = user_input.get(CONF_LIGHTS, [])

            if not self.selected_lights:
                return self.async_show_form(
                    step_id="select_lights",
                    data_schema=self._get_lights_schema(),
                    errors={"base": "no_lights_selected"},
                )

            return await self.async_step_configure_lights()

        return self.async_show_form(
            step_id="select_lights",
            data_schema=self._get_lights_schema(),
        )

    def _get_lights_schema(self) -> vol.Schema:
        """Get schema for selecting lights."""
        return vol.Schema({
            vol.Required(CONF_LIGHTS): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    multiple=True,
                    filter=selector.EntityFilterSelectorConfig(domain="light"),
                )
            ),
        })

    async def async_step_configure_lights(self, user_input: dict | None = None) -> FlowResult:
        """Configure all lights with toggle pattern for optional settings."""
        if user_input is not None:
            light_configs = {}

            for entity_id in self.selected_lights:
                config = {}

                light_state = self.hass.states.get(entity_id)
                light_name = light_state.name if light_state else entity_id
                safe_name = self._get_safe_name(light_name)

                # Power (always visible)
                power_key = f"{safe_name}_power"
                config[CONF_LIGHT_POWER] = user_input.get(power_key, LIGHT_POWER_DONT_CHANGE)

                # Brightness setting
                brightness_enabled_key = f"{safe_name}_brightness_enabled"
                brightness_key = f"{safe_name}_brightness"
                if user_input.get(brightness_enabled_key):
                    brightness_value = user_input.get(brightness_key)
                    if brightness_value is not None:
                        config[CONF_LIGHT_BRIGHTNESS] = int(brightness_value)

                # Colour Temperature setting
                colortemp_enabled_key = f"{safe_name}_colortemp_enabled"
                colortemp_key = f"{safe_name}_colortemp"
                if user_input.get(colortemp_enabled_key):
                    colortemp_value = user_input.get(colortemp_key)
                    if colortemp_value is not None:
                        config[CONF_LIGHT_COLOR_TEMP_KELVIN] = int(colortemp_value)

                # RGB Color setting
                rgb_enabled_key = f"{safe_name}_rgb_enabled"
                rgb_key = f"{safe_name}_rgb"
                if user_input.get(rgb_enabled_key):
                    rgb_value = user_input.get(rgb_key)
                    if rgb_value is not None:
                        config[CONF_LIGHT_RGB_COLOR] = list(rgb_value)

                light_configs[entity_id] = config

            mood_data = {
                CONF_MOOD_NAME: self.current_mood_name,
                CONF_LIGHTS: self.selected_lights,
                CONF_LIGHT_CONFIG: light_configs,
            }

            self.moods.append(mood_data)

            return self.async_create_entry(
                title=self.current_mood_name,
                data={"moods": self.moods},
            )

        # Build schema with toggle pattern for each light
        schema = {}

        for entity_id in self.selected_lights:
            light_state = self.hass.states.get(entity_id)
            light_name = light_state.name if light_state else entity_id
            safe_name = self._get_safe_name(light_name)
            supported_modes = light_state.attributes.get("supported_color_modes", []) if light_state else []

            # Detect capabilities
            # Any light with color modes (except "onoff") supports brightness
            has_brightness = bool(supported_modes) and not (
                len(supported_modes) == 1 and supported_modes[0] == "onoff"
            )
            has_color_temp = "color_temp" in supported_modes
            has_rgb = any(mode in supported_modes for mode in ("rgb", "rgbw", "rgbww", "hs", "xy"))

            # Get min/max kelvin
            min_kelvin = light_state.attributes.get("min_color_temp_kelvin", MIN_COLOR_TEMP_KELVIN) if light_state else MIN_COLOR_TEMP_KELVIN
            max_kelvin = light_state.attributes.get("max_color_temp_kelvin", MAX_COLOR_TEMP_KELVIN) if light_state else MAX_COLOR_TEMP_KELVIN

            # Power selector (always visible)
            schema[vol.Required(f"{safe_name}_power", default=LIGHT_POWER_DONT_CHANGE)] = (
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

            # Brightness toggle + slider
            if has_brightness:
                schema[vol.Optional(f"{safe_name}_brightness_enabled", default=True)] = (
                    selector.BooleanSelector()
                )
                schema[vol.Optional(f"{safe_name}_brightness", default=100)] = (
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_BRIGHTNESS,
                            max=MAX_BRIGHTNESS,
                            step=1,
                            unit_of_measurement="%",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    )
                )

            # Colour Temperature toggle + picker
            if has_color_temp:
                schema[vol.Optional(f"{safe_name}_colortemp_enabled", default=True)] = (
                    selector.BooleanSelector()
                )
                schema[vol.Optional(f"{safe_name}_colortemp", default=4000)] = (
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=min_kelvin,
                            max=max_kelvin,
                            step=100,
                            unit_of_measurement="K",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    )
                )

            # RGB Colour toggle + picker
            if has_rgb:
                schema[vol.Optional(f"{safe_name}_rgb_enabled", default=False)] = (
                    selector.BooleanSelector()
                )
                schema[vol.Optional(f"{safe_name}_rgb", default=[255, 255, 255])] = (
                    selector.ColorRGBSelector()
                )

        return self.async_show_form(
            step_id="configure_lights",
            data_schema=vol.Schema(schema),
        )

    def _get_safe_name(self, name: str) -> str:
        """Convert a name to a safe key format."""
        return name.replace(" ", "_").replace(".", "_").replace("-", "_").lower()
