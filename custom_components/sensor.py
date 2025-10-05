"""Sensor platform for Balena Docker containers."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN


async def async_setup_platform(
    hass: HomeAssistant,
    config,
    async_add_entities: AddEntitiesCallback,
    discovery_info=None,
):
    """Set up the Balena Docker sensors (legacy YAML, not used)."""
    pass


# Entities are created in __init__.py via async_setup
