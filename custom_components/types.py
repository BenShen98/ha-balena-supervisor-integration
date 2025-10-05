from typing import TypedDict
from dataclasses import dataclass
from homeassistant.helpers.entity_component import EntityComponent
import voluptuous as vol


import homeassistant.helpers.config_validation as cv


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


ConfigEntryDataSchema = vol.Schema(
    {
        vol.Required("connection_type"): vol.In(["same_device_no_proxy"]),
        vol.Required("disable_self_control", default=True): bool,
    }
)


@dataclass
class ConfigEntryRuntimeData:
    """Non-persistent runtime data to be stored in ConfigEntry.runtime_data."""

    entity_component: EntityComponent
    state_coordinator: "BalenaSupervisorStateCoordinator"
    api_client: "BalenaSupervisorApiClient"
