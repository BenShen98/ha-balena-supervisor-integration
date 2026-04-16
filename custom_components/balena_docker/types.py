"""Type definitions for the Balena Docker integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

if TYPE_CHECKING:
    from .coordinator import BalenaSupervisorApiClient, BalenaSupervisorStateCoordinator


class BalenaServiceState(TypedDict):
    """State of a service/container in Balena application."""

    status: str
    releaseId: int
    downloadProgress: str


class BalenaAppState(TypedDict):
    """State of a Balena application."""

    appId: int
    appName: str
    commit: str
    services: dict[str, BalenaServiceState]


class ConfigEntryData(TypedDict):
    """Data to be stored in the ConfigEntry.data."""

    connection_type: str  # "same_device_no_proxy" only for now
    disable_self_control: bool
    auto_load_js_modules: bool


@callback
def create_config_entry_data_schema(default_data: ConfigEntryData | dict) -> vol.Schema:
    """Create the schema for the config flow and options flow."""
    return vol.Schema(
        {
            vol.Required(
                "connection_type",
                default=default_data.get("connection_type", "same_device_no_proxy"),
            ): vol.In(["same_device_no_proxy"]),
            vol.Required(
                "disable_self_control",
                default=default_data.get("disable_self_control", True),
            ): bool,
            vol.Required(
                "auto_load_js_modules",
                default=default_data.get("auto_load_js_modules", True),
            ): bool,
        }
    )


@dataclass
class ConfigEntryRuntimeData:
    """Non-persistent runtime data to be stored in ConfigEntry.runtime_data."""

    state_coordinator: BalenaSupervisorStateCoordinator
    api_client: BalenaSupervisorApiClient
    js_modules: list[str] = field(default_factory=list)


type BalenaDockerConfigEntry = ConfigEntry[ConfigEntryRuntimeData]


@dataclass
class HassData:
    """Data stored in Home Assistant's hass.data under the DOMAIN key."""

    config_entries: dict[str, BalenaDockerConfigEntry] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)  # key is entity_id

    def add_entities(self, new_entities: list[Entity]) -> None:
        """Add entities to the internal dict."""
        for entity in new_entities:
            self.entities[entity.entity_id] = entity

    def add_config_entry(self, config_entry: ConfigEntry) -> None:
        """Add a config entry to the internal dict."""
        self.config_entries[config_entry.entry_id] = config_entry

    def get_entity(self, entity_id: str) -> Entity | None:
        """Get an entity by its entity_id."""
        return self.entities.get(entity_id)
