"""Config flow for MoodLights."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.entity_registry import async_get

from .const import (
    CONF_AUTO_ACTIVATE,
    CONF_AUTO_ACTIVATE_DAYS,
    CONF_AUTO_ACTIVATE_TIME,
    CONF_CONFIRMATION_MODE,
    CONF_EXCLUSION_ENTITIES,
    CONF_EXCLUSION_HELPERS,
    CONF_EXCLUSION_STATES,
    CONF_LIGHT_ENTITIES,
    CONF_LIGHT_PATTERN,
    CONF_MAX_SAVED_STATES,
    CONF_MOODS,
    CONF_NAME,
    CONF_PRESETS,
    CONF_PRESET_BRIGHTNESS,
    CONF_PRESET_COLOR_TEMP,
    CONF_PRESET_NAME,
    CONF_PRESET_RGB_COLOR,
    CONF_PRESET_TRANSITION,
    CONF_SAVE_STATES,
    DEFAULT_CONFIRMATION,
    DEFAULT_MAX_SAVED_STATES,
    DEFAULT_SAVE_STATES,
    DEFAULT_TRANSITION,
    DOMAIN,
)


class MoodLightsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MoodLights."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.moods: list[dict] = []
        self.current_mood: dict | None = None

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return await self.async_step_create_mood()

        return self.async_show_form(step_id="user")

    async def async_step_create_mood(self, user_input: dict | None = None) -> FlowResult:
        """Handle creating a new mood."""
        if user_input is not None:
            self.current_mood = {
                CONF_NAME: user_input.get(CONF_NAME, "New Mood"),
                CONF_PRESETS: [],
                CONF_LIGHT_ENTITIES: [],
                CONF_EXCLUSION_HELPERS: [],
                CONF_EXCLUSION_STATES: [],
                CONF_CONFIRMATION_MODE: DEFAULT_CONFIRMATION,
                CONF_SAVE_STATES: DEFAULT_SAVE_STATES,
                CONF_MAX_SAVED_STATES: DEFAULT_MAX_SAVED_STATES,
            }
            return await self.async_step_select_lights()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }
        )

        return self.async_show_form(step_id="create_mood", data_schema=data_schema)

    async def async_step_select_lights(self, user_input: dict | None = None) -> FlowResult:
        """Handle selecting lights for the mood."""
        if user_input is not None:
            if self.current_mood:
                self.current_mood[CONF_LIGHT_ENTITIES] = user_input.get(CONF_LIGHT_ENTITIES, [])
                self.current_mood[CONF_LIGHT_PATTERN] = user_input.get(CONF_LIGHT_PATTERN, "")
            return await self.async_step_add_preset()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_LIGHT_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(domain="light"),
                    )
                ),
                vol.Optional(CONF_LIGHT_PATTERN): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
            }
        )

        return self.async_show_form(
            step_id="select_lights", data_schema=data_schema, last_step=False
        )

    async def async_step_add_preset(self, user_input: dict | None = None) -> FlowResult:
        """Handle adding a preset to the mood."""
        if user_input is not None:
            if self.current_mood and user_input.get(CONF_PRESET_NAME):
                preset = {
                    CONF_PRESET_NAME: user_input[CONF_PRESET_NAME],
                    CONF_PRESET_BRIGHTNESS: user_input.get(CONF_PRESET_BRIGHTNESS, 100),
                    CONF_PRESET_COLOR_TEMP: user_input.get(CONF_PRESET_COLOR_TEMP),
                    CONF_PRESET_RGB_COLOR: user_input.get(CONF_PRESET_RGB_COLOR),
                    CONF_PRESET_TRANSITION: user_input.get(CONF_PRESET_TRANSITION, DEFAULT_TRANSITION),
                }
                self.current_mood[CONF_PRESETS].append(preset)

            return await self.async_step_preset_confirm()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_PRESET_NAME): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                ),
                vol.Optional(CONF_PRESET_BRIGHTNESS, default=100): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=100)
                ),
                vol.Optional(CONF_PRESET_COLOR_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=153, max=500, step=1, unit_of_measurement="mired"
                    )
                ),
                vol.Optional(CONF_PRESET_RGB_COLOR): selector.ColorRGBSelector(),
                vol.Optional(CONF_PRESET_TRANSITION, default=DEFAULT_TRANSITION): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=30)
                ),
            }
        )

        return self.async_show_form(step_id="add_preset", data_schema=data_schema)

    async def async_step_preset_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Confirm preset addition and ask if user wants to add more."""
        if user_input is not None:
            if user_input.get("add_another"):
                return await self.async_step_add_preset()
            return await self.async_step_exclusion_rules()

        data_schema = vol.Schema(
            {
                vol.Required("add_another", default=False): bool,
            }
        )

        return self.async_show_form(step_id="preset_confirm", data_schema=data_schema)

    async def async_step_exclusion_rules(self, user_input: dict | None = None) -> FlowResult:
        """Handle exclusion rules configuration."""
        if user_input is not None and self.current_mood:
            self.current_mood[CONF_EXCLUSION_HELPERS] = user_input.get(CONF_EXCLUSION_HELPERS, [])
            self.current_mood[CONF_EXCLUSION_STATES] = user_input.get(CONF_EXCLUSION_STATES, [])
            return await self.async_step_confirmation()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_EXCLUSION_HELPERS): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(
                            domain=["input_boolean", "switch", "binary_sensor"]
                        ),
                    )
                ),
                vol.Optional(CONF_EXCLUSION_STATES): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        filter=selector.EntityFilterSelectorConfig(
                            domain=["media_player", "person", "sensor"]
                        ),
                    )
                ),
            }
        )

        return self.async_show_form(step_id="exclusion_rules", data_schema=data_schema)

    async def async_step_confirmation(self, user_input: dict | None = None) -> FlowResult:
        """Handle confirmation mode configuration."""
        if user_input is not None and self.current_mood:
            self.current_mood[CONF_CONFIRMATION_MODE] = user_input.get(
                CONF_CONFIRMATION_MODE, DEFAULT_CONFIRMATION
            )
            return await self.async_step_state_settings()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_CONFIRMATION_MODE, default=DEFAULT_CONFIRMATION): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": "none", "label": "No confirmation"},
                            {"value": "notify", "label": "Notify only"},
                            {"value": "approve", "label": "Require approval"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="confirmation", data_schema=data_schema)

    async def async_step_state_settings(self, user_input: dict | None = None) -> FlowResult:
        """Handle state settings configuration."""
        if user_input is not None and self.current_mood:
            self.current_mood[CONF_SAVE_STATES] = user_input.get(CONF_SAVE_STATES, DEFAULT_SAVE_STATES)
            self.current_mood[CONF_MAX_SAVED_STATES] = user_input.get(
                CONF_MAX_SAVED_STATES, DEFAULT_MAX_SAVED_STATES
            )

            if self.current_mood:
                self.moods.append(self.current_mood)

            return await self.async_step_mood_confirm()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SAVE_STATES, default=DEFAULT_SAVE_STATES): bool,
                vol.Optional(CONF_MAX_SAVED_STATES, default=DEFAULT_MAX_SAVED_STATES): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=10)
                ),
            }
        )

        return self.async_show_form(step_id="state_settings", data_schema=data_schema)

    async def async_step_mood_confirm(self, user_input: dict | None = None) -> FlowResult:
        """Confirm mood creation and ask if user wants to add more moods."""
        if user_input is not None:
            if user_input.get("add_another"):
                self.current_mood = None
                return await self.async_step_create_mood()

            return self.async_create_entry(
                title="MoodLights",
                data={CONF_MOODS: self.moods},
            )

        mood_names = [m.get(CONF_NAME, "Unnamed") for m in self.moods]
        preview = ", ".join(mood_names) if mood_names else "No moods created"

        data_schema = vol.Schema(
            {
                vol.Required("add_another", default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="mood_confirm",
            data_schema=data_schema,
            description_placeholders={"moods": preview},
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid auth."""
