"""Config flow for MoodLights."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
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
            description_placeholders={
                "step_desc": "Enter a name for your mood (e.g., 'Movie Night', 'Relaxing', 'Party')"
            }
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
                    description_placeholders={"step_desc": "Select the lights you want to control with this mood"}
                )
            
            return await self.async_step_configure_lights()

        return self.async_show_form(
            step_id="select_lights",
            data_schema=self._get_lights_schema(),
            description_placeholders={"step_desc": "Select the lights you want to control with this mood"}
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
        """Configure all lights in a single scrollable dialog."""
        if user_input is not None:
            # Save the configuration
            light_configs = {}
            
            for entity_id in self.selected_lights:
                config = {}
                
                # Get the light name as prefix for fields
                light_state = self.hass.states.get(entity_id)
                light_name = light_state.name if light_state else entity_id
                safe_name = light_name.replace(" ", "_").lower()
                
                # Power
                power_key = f"{safe_name}_power"
                config[CONF_LIGHT_POWER] = user_input.get(power_key, LIGHT_POWER_DONT_CHANGE)
                
                # Brightness
                brightness_key = f"{safe_name}_brightness"
                if user_input.get(brightness_key):
                    config[CONF_LIGHT_BRIGHTNESS] = user_input[brightness_key]
                
                # Colour Temperature (Kelvin)
                colortemp_key = f"{safe_name}_colortemp"
                if user_input.get(colortemp_key):
                    config[CONF_LIGHT_COLOR_TEMP_KELVIN] = user_input[colortemp_key]
                
                # RGB Color - store as tuple
                rgb_key = f"{safe_name}_rgb"
                rgb_value = user_input.get(rgb_key)
                if rgb_value is not None:
                    # Ensure it's stored as a tuple of ints
                    config[CONF_LIGHT_RGB_COLOR] = tuple(rgb_value)
                
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

        # Build the schema for all lights in one dialog
        schema = {}
        
        for entity_id in self.selected_lights:
            light_state = self.hass.states.get(entity_id)
            light_name = light_state.name if light_state else entity_id
            supported_modes = light_state.attributes.get("supported_color_modes", []) if light_state else []
            safe_name = light_name.replace(" ", "_").lower()
            
            has_brightness = "brightness" in supported_modes or "br" in supported_modes
            has_color_temp = "color_temp" in supported_modes
            # Check for RGB, RGBW, RGBWW, HS, or XY color modes
            has_rgb = any(
                mode in supported_modes
                for mode in ("rgb", "rgbw", "rgbww", "hs", "xy")
            )
            
            # Get min/max kelvin for this specific light
            min_kelvin = MIN_COLOR_TEMP_KELVIN
            max_kelvin = MAX_COLOR_TEMP_KELVIN
            if has_color_temp and light_state:
                min_kelvin = light_state.attributes.get("min_color_temp_kelvin", MIN_COLOR_TEMP_KELVIN)
                max_kelvin = light_state.attributes.get("max_color_temp_kelvin", MAX_COLOR_TEMP_KELVIN)
            
            # Power selector
            schema[vol.Required(f"{safe_name}_power", default=LIGHT_POWER_DONT_CHANGE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": LIGHT_POWER_ON, "label": "Turn On"},
                        {"value": LIGHT_POWER_OFF, "label": "Turn Off"},
                        {"value": LIGHT_POWER_DONT_CHANGE, "label": "Don't Change"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
            
            # Brightness slider (1-100%)
            if has_brightness:
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
            
            # Colour Temperature (Kelvin)
            if has_color_temp:
                schema[vol.Optional(f"{safe_name}_colortemp")] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=min_kelvin,
                        max=max_kelvin,
                        step=100,
                        unit_of_measurement="K",
                    )
                )
            
            # RGB Color - add default and make optional
            if has_rgb:
                schema[vol.Optional(f"{safe_name}_rgb", default=[255, 255, 255])] = (
                    selector.ColorRGBSelector()
                )
        
        return self.async_show_form(
            step_id="configure_lights",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "step_desc": f"Configure settings for {len(self.selected_lights)} light(s)"
            }
        )
