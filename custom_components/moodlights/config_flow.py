"""Config flow for MoodLights."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.area_registry import AreaRegistry, async_get as async_get_area_registry
from homeassistant.helpers.entity_registry import EntityRegistry, async_get as async_get_entity_registry

from .const import (
    CONF_AREA,
    CONF_EXCLUSION_HELPERS,
    CONF_LIGHT_BRIGHTNESS,
    CONF_LIGHT_COLOR_TEMP_KELVIN,
    CONF_LIGHT_CONFIG,
    CONF_LIGHT_EFFECT,
    CONF_LIGHT_POWER,
    CONF_LIGHT_RGB_COLOR,
    CONF_SAVE_STATES,
    DOMAIN,
    LIGHT_POWER_DONT_CHANGE,
    LIGHT_POWER_OFF,
    LIGHT_POWER_ON,
    MAX_COLOR_TEMP_KELVIN,
    MIN_COLOR_TEMP_KELVIN,
)


class MoodLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoodLights."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.area_id: str | None = None
        self.area_name: str | None = None
        self.light_config: dict = {}
        self.exclusion_helpers: list[str] = []
        self.save_states: bool = True
        self.all_lights: list[dict] = []
        self.current_light_index: int = 0
        self._area_registry: AreaRegistry | None = None
        self._entity_registry: EntityRegistry | None = None
        self._area_to_entities: dict[str, list[str]] = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step - select area."""
        if user_input is not None:
            self.area_id = user_input.get(CONF_AREA)
            self._area_registry = async_get_area_registry(self.hass)
            self._entity_registry = async_get_entity_registry(self.hass)
            
            area = self._area_registry.async_get_area(self.area_id)
            self.area_name = area.name if area else self.area_id
            
            self._build_area_to_entities_map()
            self.all_lights = self._get_lights_in_area(self.area_id)
            
            if not self.all_lights:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_area_schema(),
                    errors={"base": "no_lights_in_area"},
                )
            
            self.current_light_index = 0
            self.light_config = {}
            return await self.async_step_configure_light()

        return self.async_show_form(step_id="user", data_schema=self._get_area_schema())

    def _build_area_to_entities_map(self) -> None:
        """Build a map of area_id to entity_ids using entity registry."""
        self._area_to_entities = {}
        
        if not self._entity_registry:
            return
            
        for entry in self._entity_registry.entities.values():
            if entry.area_id and entry.domain == "light":
                if entry.area_id not in self._area_to_entities:
                    self._area_to_entities[entry.area_id] = []
                self._area_to_entities[entry.area_id].append(entry.entity_id)

    def _get_area_schema(self) -> vol.Schema:
        """Get area selection schema."""
        areas = self._get_available_areas()
        
        if not areas:
            return vol.Schema(
                {
                    vol.Required(CONF_AREA): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": "", "label": "No areas found - create areas in HA first"}],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
        
        return vol.Schema(
            {
                vol.Required(CONF_AREA): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": area["id"], "label": area["name"]}
                            for area in areas
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

    def _get_available_areas(self) -> list[dict]:
        """Get list of all areas from HA."""
        area_registry = async_get_area_registry(self.hass)
        areas = []
        
        for area in area_registry.areas.values():
            areas.append({
                "id": area.id,
                "name": area.name
            })
        
        return sorted(areas, key=lambda x: x["name"])

    def _get_lights_in_area(self, area_id: str) -> list[dict]:
        """Get all lights in an area with their capabilities."""
        lights = []
        
        entity_ids_in_area = self._area_to_entities.get(area_id, [])
        
        for state in self.hass.states.async_all("light"):
            if state.entity_id in entity_ids_in_area:
                supported_modes = state.attributes.get("supported_color_modes", [])
                effect_list = state.attributes.get("effect_list", []) or []
                
                light_info = {
                    "entity_id": state.entity_id,
                    "name": state.name,
                    "friendly_name": state.attributes.get("friendly_name", state.entity_id),
                    "supported_color_modes": supported_modes,
                    "effect_list": effect_list,
                    "has_brightness": "brightness" in supported_modes or "br" in supported_modes,
                    "has_color_temp": "color_temp" in supported_modes,
                    "has_rgb": "rgb" in supported_modes or "hs" in supported_modes or "xy" in supported_modes,
                    "has_effect": bool(effect_list),
                    "is_on_off_only": supported_modes == ["on_off"] or supported_modes == ["onoff"] or not supported_modes,
                }
                lights.append(light_info)
        
        return sorted(lights, key=lambda x: x["name"])

    async def async_step_configure_light(self, user_input: dict | None = None) -> FlowResult:
        """Configure individual light settings."""
        if user_input is not None:
            light = self.all_lights[self.current_light_index]
            entity_id = light["entity_id"]
            
            config = {}
            if light["is_on_off_only"]:
                config[CONF_LIGHT_POWER] = user_input.get(CONF_LIGHT_POWER, LIGHT_POWER_DONT_CHANGE)
            else:
                if user_input.get(CONF_LIGHT_BRIGHTNESS):
                    config[CONF_LIGHT_BRIGHTNESS] = user_input[CONF_LIGHT_BRIGHTNESS]
                
                if user_input.get(CONF_LIGHT_COLOR_TEMP_KELVIN):
                    config[CONF_LIGHT_COLOR_TEMP_KELVIN] = user_input[CONF_LIGHT_COLOR_TEMP_KELVIN]
                
                if user_input.get(CONF_LIGHT_RGB_COLOR):
                    config[CONF_LIGHT_RGB_COLOR] = list(user_input[CONF_LIGHT_RGB_COLOR])
                
                if user_input.get(CONF_LIGHT_EFFECT):
                    config[CONF_LIGHT_EFFECT] = user_input[CONF_LIGHT_EFFECT]
                
                config[CONF_LIGHT_POWER] = user_input.get(CONF_LIGHT_POWER, LIGHT_POWER_DONT_CHANGE)
            
            self.light_config[entity_id] = config
            
            self.current_light_index += 1
            if self.current_light_index < len(self.all_lights):
                return await self.async_step_configure_light()
            else:
                return await self.async_step_exclusions()

        light = self.all_lights[self.current_light_index]
        return self.async_show_form(
            step_id="configure_light",
            data_schema=self._get_light_config_schema(light),
            description_placeholders={"light_name": light.get("friendly_name", light["name"]), "progress": f"{self.current_light_index + 1}/{len(self.all_lights)}"},
        )

    def _get_light_config_schema(self, light: dict) -> vol.Schema:
        """Get schema for configuring a single light."""
        schema_dict = {}
        
        if light["is_on_off_only"]:
            schema_dict[vol.Required(CONF_LIGHT_POWER, default=LIGHT_POWER_DONT_CHANGE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": LIGHT_POWER_ON, "label": "Turn On"},
                        {"value": LIGHT_POWER_OFF, "label": "Turn Off"},
                        {"value": LIGHT_POWER_DONT_CHANGE, "label": "Don't Change"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        else:
            if light["has_brightness"]:
                schema_dict[vol.Optional(CONF_LIGHT_BRIGHTNESS)] = vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=100)
                )
            
            if light["has_color_temp"]:
                schema_dict[vol.Optional(CONF_LIGHT_COLOR_TEMP_KELVIN)] = selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_COLOR_TEMP_KELVIN,
                        max=MAX_COLOR_TEMP_KELVIN,
                        step=100,
                        unit_of_measurement="K",
                    )
                )
            
            if light["has_rgb"]:
                schema_dict[vol.Optional(CONF_LIGHT_RGB_COLOR)] = selector.ColorRGBSelector()
            
            if light["has_effect"]:
                effect_options = [{"value": "", "label": "Don't Change"}]
                effect_options.extend([{"value": e, "label": e} for e in light["effect_list"]])
                schema_dict[vol.Optional(CONF_LIGHT_EFFECT)] = selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=effect_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            
            schema_dict[vol.Required(CONF_LIGHT_POWER, default=LIGHT_POWER_DONT_CHANGE)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": LIGHT_POWER_ON, "label": "Turn On"},
                        {"value": LIGHT_POWER_OFF, "label": "Turn Off"},
                        {"value": LIGHT_POWER_DONT_CHANGE, "label": "Don't Change"},
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        
        return vol.Schema(schema_dict)

    async def async_step_exclusions(self, user_input: dict | None = None) -> FlowResult:
        """Configure exclusion helpers."""
        if user_input is not None:
            self.exclusion_helpers = user_input.get(CONF_EXCLUSION_HELPERS, [])
            return await self.async_step_save()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_EXCLUSION_HELPERS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(domain="input_boolean"),
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="exclusions", 
            data_schema=data_schema,
            description_placeholders={"helper_desc": "When these input_booleans are ON, mood activation will be blocked"},
        )

    async def async_step_save(self, user_input: dict | None = None) -> FlowResult:
        """Final step - save mood."""
        if user_input is not None:
            self.save_states = user_input.get(CONF_SAVE_STATES, True)

        mood_data = {
            "name": f"{self.area_name} Mood",
            "area_id": self.area_id,
            "light_config": self.light_config,
            "exclusion_helpers": self.exclusion_helpers,
            "save_states": self.save_states,
        }

        return self.async_create_entry(
            title=f"{self.area_name} Mood",
            data={"moods": [mood_data]},
        )

    async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
        """Handle reconfiguration."""
        return await self.async_step_user(user_input)
