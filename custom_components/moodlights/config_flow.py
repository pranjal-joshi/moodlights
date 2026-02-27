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
        self.light_configs: dict = {}
        self.current_light_index: int = 0

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step - enter mood name."""
        if user_input is not None:
            self.current_mood_name = user_input.get(CONF_MOOD_NAME, "New Mood")
            return await self.async_step_select_lights()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MOOD_NAME, description={"suggested_value": "Living Room Evening"}): selector.TextSelector(
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
            
            self.light_configs = {}
            self.current_light_index = 0
            return await self.async_step_configure_light()

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

    async def async_step_configure_light(self, user_input: dict | None = None) -> FlowResult:
        """Configure individual light settings."""
        if user_input is not None:
            entity_id = self.selected_lights[self.current_light_index]
            
            config = {}
            
            # Power setting
            power = user_input.get(CONF_LIGHT_POWER, LIGHT_POWER_DONT_CHANGE)
            config[CONF_LIGHT_POWER] = power
            
            # Only show other options if turning ON
            if power == LIGHT_POWER_ON:
                # Brightness
                if user_input.get(CONF_LIGHT_BRIGHTNESS):
                    config[CONF_LIGHT_BRIGHTNESS] = user_input[CONF_LIGHT_BRIGHTNESS]
                
                # Color temperature in Kelvin
                if user_input.get(CONF_LIGHT_COLOR_TEMP_KELVIN):
                    config[CONF_LIGHT_COLOR_TEMP_KELVIN] = user_input[CONF_LIGHT_COLOR_TEMP_KELVIN]
                
                # RGB Color
                if user_input.get(CONF_LIGHT_RGB_COLOR):
                    config[CONF_LIGHT_RGB_COLOR] = list(user_input[CONF_LIGHT_RGB_COLOR])
            
            self.light_configs[entity_id] = config
            
            self.current_light_index += 1
            if self.current_light_index < len(self.selected_lights):
                return await self.async_step_configure_light()
            else:
                return await self.async_step_save()

        entity_id = self.selected_lights[self.current_light_index]
        light_state = self.hass.states.get(entity_id)
        light_name = light_state.name if light_state else entity_id
        supported_modes = light_state.attributes.get("supported_color_modes", []) if light_state else []
        
        return self.async_show_form(
            step_id="configure_light",
            data_schema=self._get_light_config_schema(entity_id, supported_modes),
            description_placeholders={
                "light_name": light_name,
                "progress": f"{self.current_light_index + 1}/{len(self.selected_lights)}",
                "step_desc": "Configure how this light should behave when the mood is activated"
            }
        )

    def _get_light_config_schema(self, entity_id: str, supported_modes: list) -> vol.Schema:
        """Get schema for configuring a single light."""
        schema = {}
        
        # Power - always show
        schema[vol.Required(CONF_LIGHT_POWER, default=LIGHT_POWER_DONT_CHANGE)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    {"value": LIGHT_POWER_ON, "label": "Turn On"},
                    {"value": LIGHT_POWER_OFF, "label": "Turn Off"},
                    {"value": LIGHT_POWER_DONT_CHANGE, "label": "Don't Change"},
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )
        
        # Check capabilities
        has_brightness = "brightness" in supported_modes or "br" in supported_modes
        has_color_temp = "color_temp" in supported_modes
        has_rgb = "rgb" in supported_modes or "hs" in supported_modes or "xy" in supported_modes
        
        # Get light state for min/max kelvin
        light_state = self.hass.states.get(entity_id)
        
        # Brightness slider
        if has_brightness:
            schema[vol.Optional(CONF_LIGHT_BRIGHTNESS)] = vol.All(
                vol.Coerce(int), vol.Range(min=MIN_BRIGHTNESS, max=MAX_BRIGHTNESS)
            )
        
        # Color temperature in Kelvin
        if has_color_temp and light_state:
            min_kelvin = light_state.attributes.get("min_color_temp_kelvin", MIN_COLOR_TEMP_KELVIN)
            max_kelvin = light_state.attributes.get("max_color_temp_kelvin", MAX_COLOR_TEMP_KELVIN)
            
            schema[vol.Optional(CONF_LIGHT_COLOR_TEMP_KELVIN)] = selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=min_kelvin,
                    max=max_kelvin,
                    step=100,
                    unit_of_measurement="K",
                )
            )
        
        # RGB Color
        if has_rgb:
            schema[vol.Optional(CONF_LIGHT_RGB_COLOR)] = selector.ColorRGBSelector()
        
        return vol.Schema(schema)

    async def async_step_save(self, user_input: dict | None = None) -> FlowResult:
        """Save the mood."""
        mood_data = {
            CONF_MOOD_NAME: self.current_mood_name,
            CONF_LIGHTS: self.selected_lights,
            CONF_LIGHT_CONFIG: self.light_configs,
        }
        
        self.moods.append(mood_data)
        
        return self.async_create_entry(
            title="MoodLights",
            data={"moods": self.moods},
        )
