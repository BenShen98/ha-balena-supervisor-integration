""" "Constants for the balena_docker integration."""

from typing import TYPE_CHECKING, Any
from homeassistant.util.hass_dict import HassKey

from .types import HassData

DOMAIN = "balena_docker"
DATA_BALENA: HassKey[HassData] = HassKey(DOMAIN)
JS_MODULES = ["more-info-balena_docker.js"]
