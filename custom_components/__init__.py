"""Integration for Balena Docker containers."""

import os
import logging
import aiohttp
import voluptuous as vol
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers import config_validation as cv
from homeassistant.components import websocket_api

_LOGGER = logging.getLogger(__name__)
DOMAIN = "balena_docker"
DATA_COMPONENT = f"{DOMAIN}_component"

ADDR = f"http://{os.getenv('BALENA_SUPERVISOR_ADDRESS', 'localhost')}:{os.getenv('BALENA_SUPERVISOR_PORT', '8080')}"
APP_ID = os.getenv("BALENA_APP_ID", "123")
APP_NAME = os.getenv("BALENA_APP_NAME", "tst")
KEY = os.getenv("BALENA_SUPERVISOR_API_KEY", "testkey")
CURRENT_SERVICE_NAME = os.getenv("BALENA_SERVICE_NAME")

# TODO: use helper.update_coordinator to merge async_get_clientsession requests
# TODO: what is the request timeout?


class BalenaContainerEntity(Entity):
    """Entity representing a Balena Docker container."""

    def __init__(self, service_name: str) -> None:
        """Initialize a Balena Docker container entity."""
        # self._attr_release_id = release_id
        # self._attr_service_name = service_name
        # self._attr_download_progress = download_progress
        # self._attr_state = status
        self.service_name = service_name
        self.entity_id = f"{DOMAIN}.{service_name}"
        self._attr_unique_id = f"{DOMAIN}_{service_name}"

    @callback
    def set_state(self, state: dict) -> None:
        """Recevies an dict of the service's state, update the attributes of the class."""
        self._attr_state = state.pop("status")
        self._attr_extra_state_attributes = {
            **state,
            "custom_ui_more_info": "more-info-balena_docker",
            "icon": "mdi:play-circle-outline"
            if self._attr_state == "Running"
            else "mdi:stop-circle-outline",
        }

    async def async_update(self) -> None:
        """Update entity state from the Balena Supervisor API."""
        url = f"{ADDR}/v2/applications/state"
        params = {"apikey": KEY}
        session = async_get_clientsession(self.hass)
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            self.set_state(data[APP_NAME]["services"][self.service_name])


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

    url = f"{ADDR}/v2/applications/{APP_ID}/{action}"

    component = hass.data[DATA_COMPONENT]
    entity = component.get_entity(entity_id)

    params = {"apikey": KEY}
    headers = {"Content-Type": "application/json"}
    payload = {"serviceName": entity.service_name}
    session = async_get_clientsession(hass)

    # TODO: proxy this to entity
    async with session.post(url, headers=headers, params=params, json=payload) as resp:
        resp_text = await resp.text()
        _LOGGER.info(resp_text)

    await entity.async_update()

    connection.send_result(msg["id"], {"result": "ok"})


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up Balena Docker integration."""
    component = hass.data[DATA_COMPONENT] = EntityComponent(_LOGGER, DOMAIN, hass)
    await component.async_setup(config)

    url = f"{ADDR}/v2/applications/state"
    params = {"apikey": KEY}
    entities = []

    # query
    session = async_get_clientsession(hass)
    async with session.get(url, params=params) as resp:
        data = await resp.json()
        for service_name, service_data in data[APP_NAME]["services"].items():
            entity = BalenaContainerEntity(service_name)
            entity.set_state(service_data)
            entities.append(entity)

    await component.async_add_entities(entities)

    websocket_api.async_register_command(hass, handle_container_service)

    return True
