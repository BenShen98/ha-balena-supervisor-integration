"""Support for ADS binary sensors."""

from __future__ import annotations
import voluptuous as vol
import logging

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES_SCHEMA,
    PLATFORM_SCHEMA as BINARY_SENSOR_PLATFORM_SCHEMA,
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    _LOGGER.info("ran setup_platform")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry[ConfigEntryRuntimeData],
    async_add_entities,
) -> bool:
    _LOGGER.info(
        "ran async_setup_entry because of await component.async_setup_entry(config_entry) in __init__.py"
    )
    return True
