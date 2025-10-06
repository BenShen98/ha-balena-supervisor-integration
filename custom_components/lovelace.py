"""Loading JS resource by sniffing the LovelaceResourceStorageCollection.

Should use API in future development of the component.
"""

import asyncio
import logging

from homeassistant.components.lovelace import LovelaceData, LOVELACE_DATA
from homeassistant.components.lovelace.resources import (
    ResourceStorageCollection as LovelaceResourceStorageCollection,
)
from homeassistant.core import HomeAssistant, callback

from .const import JS_MODULES, DOMAIN

_LOGGER = logging.getLogger(__name__)


@callback
def get_js_modules() -> list[dict[str, str]]:
    """Return the list of JS modules."""
    return [
        {
            "url": f"/local/{DOMAIN.lower()}/{module}",
            "res_type": "module",
        }
        for module in JS_MODULES
    ]


async def load_js_modules(hass: HomeAssistant) -> list[str]:
    """Load JS modules for the frontend."""
    js_storage: LovelaceResourceStorageCollection = hass.data[LOVELACE_DATA].resources

    # Add all JS modules using gather for concurrency
    results = await asyncio.gather(
        *[js_storage.async_create_item(module) for module in get_js_modules()],
    )
    _LOGGER.info(results)

    return [item["id"] for item in results]


async def unload_js_modules(hass: HomeAssistant, js_modules_id: list[str]) -> None:
    """Unload JS modules for the frontend."""
    js_storage: LovelaceResourceStorageCollection = hass.data[LOVELACE_DATA].resources

    # Remove all JS modules using gather for concurrency
    await asyncio.gather(
        *[js_storage.async_delete_item(item_id) for item_id in js_modules_id],
    )
