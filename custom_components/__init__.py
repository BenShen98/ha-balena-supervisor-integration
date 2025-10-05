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

from .const import DOMAIN, DATA_COMPONENT
from .coordinator import BalenaSupervisorApiClient, BalenaSupervisorStateCoordinator
from .entity import BalenaContainerEntity

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

    component = hass.data[DATA_COMPONENT]
    entity = component.get_entity(entity_id)

    await entity.async_control_service(action)

    connection.send_result(msg["id"], {"result": "ok"})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Balena Docker integration."""

    # setup the coordinator
    client = BalenaSupervisorApiClient(
        async_get_clientsession(hass),
        url=f"http://{os.getenv('BALENA_SUPERVISOR_ADDRESS', 'localhost')}:{os.getenv('BALENA_SUPERVISOR_PORT', '8080')}",
        api_key=os.getenv("BALENA_SUPERVISOR_API_KEY", "testkey"),
    )
    coordinator = BalenaSupervisorStateCoordinator(hass, None, client)
    await coordinator.async_refresh()

    if coordinator.last_update_success is False:
        _LOGGER.info("Failed to fetch data from Balena Supervisor API")
        return False

    # setup the entity_component
    # TODO: the config_entry should have cooridinator as runtime data
    component = hass.data[DATA_COMPONENT] = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup(config)

    # setup entities
    entities = []
    for service_name in coordinator.data["services"]:
        entity = BalenaContainerEntity(service_name, coordinator)
        entities.append(entity)
    await component.async_add_entities(entities)

    # register websocket command for frontend
    websocket_api.async_register_command(hass, handle_container_service)

    return True
