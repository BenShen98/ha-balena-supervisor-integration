"""Loading JS resource by sniffing the LovelaceResourceStorageCollection.

Should use API in future development of the component.
"""

import asyncio
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant, callback
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url

from .const import JS_MODULES, DOMAIN, JS_URL_PATH

_LOGGER = logging.getLogger(__name__)


@callback
def get_js_modules() -> list[str]:
    """Return the list of JS modules."""


async def load_js_modules(hass: HomeAssistant) -> list[str]:
    """Load JS modules for the frontend."""
    modules = [f"{JS_URL_PATH}/{module}" for module in JS_MODULES]

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path="/balena_docker",
                path=str(Path(__file__).parent / "js"),
                cache_headers=False,
            )
        ]
    )

    for module in modules:
        add_extra_js_url(hass, module)

    return modules


async def unload_js_modules(hass: HomeAssistant, modules: list[str]) -> None:
    """Unload JS modules for the frontend."""
    for module in modules:
        remove_extra_js_url(hass, module)
