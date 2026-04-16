import voluptuous as vol
from typing import Any

from homeassistant import config_entries

from .const import DOMAIN, JS_MODULES
from .types import ConfigEntryData, create_config_entry_data_schema


class BalenaDockerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Balena Docker config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: ConfigEntryData | None = None):
        """Handle the initial step, when user adds the integration manually."""
        if user_input is not None:
            return self.async_create_entry(title="Balena Docker", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=create_config_entry_data_schema({}),
        )

    async def async_step_reconfigure(self, user_input: ConfigEntryData | None = None):
        """Handle reconfiguring an existing config entry."""
        # If editing an existing entry, use its data as defaults
        defaults: dict[str, Any] = {}
        if self._async_current_entries():
            entry = self._async_current_entries()[0]
            defaults = dict(entry.data)

        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=create_config_entry_data_schema(defaults),
        )
