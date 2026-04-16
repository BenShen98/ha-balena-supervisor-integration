"""Integration for Balena Docker containers."""

import os
import logging
import aiohttp
import voluptuous as vol
from typing import Any

from homeassistant.helpers.typing import ConfigType

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import config_validation as cv
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform


from .const import DOMAIN, DATA_BALENA
from .coordinator import BalenaSupervisorApiClient, BalenaSupervisorStateCoordinator
from .types import (
    BalenaDockerConfigEntry,
    ConfigEntryRuntimeData,
    ConfigEntryData,
    HassData,
)
from .frontend import load_js_modules, unload_js_modules

_LOGGER = logging.getLogger(__name__)

# TODO: use helper.update_coordinator to merge async_get_clientsession requests
# TODO: what is the request timeout?


@websocket_api.require_admin
@websocket_api.async_response
@websocket_api.websocket_command(
    {
        vol.Required("type"): "balena_docker/control_container",
        vol.Required("entity_id"): cv.strict_entity_id,
        vol.Required("action"): vol.In(
            ["start-service", "stop-service", "restart-service"]
        ),
    }
)
async def handle_container_service(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle start/stop/restart service for a container."""
    entity_id = msg["entity_id"]
    action = msg["action"]

    entity = hass.data[DATA_BALENA].get_entity(entity_id)

    await entity.async_control_service(action)

    connection.send_result(msg["id"], {"result": "ok"})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Balena Docker integration."""

    return True


async def async_setup_entry(
    hass: HomeAssistant, config_entry: BalenaDockerConfigEntry
) -> bool:
    """Set up Balena Docker from a config entry."""

    if config_entry.data["connection_type"] != "same_device_no_proxy":
        _LOGGER.info("Only 'same_device_no_proxy' connection type is supported")
        return False

    # setup the coordinator
    url = os.getenv("BALENA_SUPERVISOR_ADDRESS", "http://localhost:8080")
    _LOGGER.info("Using Balena Supervisor API URL: %s", url)
    client = BalenaSupervisorApiClient(
        async_get_clientsession(hass),
        url=url,
        api_key=os.getenv("BALENA_SUPERVISOR_API_KEY", "testkey"),
    )
    coordinator = BalenaSupervisorStateCoordinator(hass, config_entry, client)
    await coordinator.async_refresh()
    coordinator.start_burst_refresh()

    # abort if cannot fetch initial data from API
    if coordinator.last_update_success is False:
        _LOGGER.info("Failed to fetch data from Balena Supervisor API")
        return False

    # setup runtime data
    config_entry.runtime_data = ConfigEntryRuntimeData(
        state_coordinator=coordinator,
        api_client=client,
    )

    # setup hass.data
    if DATA_BALENA not in hass.data:
        hass.data[DATA_BALENA] = HassData()
    hass.data[DATA_BALENA].add_config_entry(config_entry)

    # invoking async_setup_entry from sensor.py
    await hass.config_entries.async_forward_entry_setups(
        config_entry, [Platform.SENSOR]
    )

    # register websocket command for frontend
    websocket_api.async_register_command(hass, handle_container_service)

    # register frontend modules
    if config_entry.data["auto_load_js_modules"]:
        config_entry.runtime_data.js_modules = await load_js_modules(hass)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: BalenaDockerConfigEntry
) -> bool:
    """Unload a config entry."""

    # unload platforms that were set up in async_setup_entry
    if not await hass.config_entries.async_unload_platforms(
        config_entry, [Platform.SENSOR]
    ):
        return False

    # unload lovelace JS modules that were loaded in async_setup_entry, given the config may have been updated, use the runtime data instead of config data
    if config_entry.runtime_data.js_modules:
        await unload_js_modules(hass, config_entry.runtime_data.js_modules)

    return True


async def async_remove_entry(
    hass: HomeAssistant, config_entry: BalenaDockerConfigEntry
) -> None:
    """Remove a config entry.

    Called when user click on "Delete" in the UI.
    """
    return True
