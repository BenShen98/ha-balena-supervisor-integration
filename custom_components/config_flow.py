import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from .const import DOMAIN

from .types import ConfigEntryData, ConfigEntryDataSchema


class ExampleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input: ConfigEntryData | None = None):
        if user_input is not None:
            return self.async_create_entry(title="Example", data=user_input)

        return self.async_show_form(step_id="user", data_schema=ConfigEntryDataSchema)

    async def async_step_reconfigure(self, user_input: ConfigEntryData | None = None):
        if user_input is not None:
            return self.async_update_reload_and_abort(
                self._get_reconfigure_entry(),
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=ConfigEntryDataSchema,
        )
