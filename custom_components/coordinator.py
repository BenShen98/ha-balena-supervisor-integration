from datetime import timedelta
import logging
import aiohttp

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry

from .types import BalenaAppState, BalenaServiceState

_LOGGER = logging.getLogger(__name__)


class BalenaSupervisorApiClient:
    """Client to interact with Balena Supervisor API."""

    def __init__(self, session: aiohttp.ClientSession, url: str, api_key: str) -> None:
        """Initialize the client."""
        self.session = session
        self._url = url
        self._api_key = api_key

    async def get_state(self) -> BalenaAppState:
        """Fetch the app state, using https://docs.balena.io/reference/supervisor/supervisor-api/#get-v2applicationsstate endpoint."""
        async with self.session.get(
            f"{self._url}/v2/applications/state", params={"apiKey": self._api_key}
        ) as resp:
            resp_json = await resp.json()

            if len(resp_json) != 1:
                raise UpdateFailed("Expect exactly one application in response")

            app_name, content = next(iter(resp_json.items()))
            return BalenaAppState(name=app_name, **content)

    async def post_container_service(
        self, app_id: int, service_name: str, action: str
    ) -> None:
        """Control a container service, using https://docs.balena.io/reference/supervisor/supervisor-api/ endpoint."""
        if action not in ("start-service", "stop-service", "restart-service"):
            raise ServiceValidationError("Invalid action to control container service")

        async with self.session.post(
            f"{self._url}/v2/applications/{app_id}/{action}",
            headers={"Content-Type": "application/json"},
            params={"apikey": self._api_key},
            json={"serviceName": service_name},
        ) as resp:
            resp_text = await resp.text()
            if "OK" not in resp_text:
                raise UpdateFailed(f"Error communicating with API: {resp_text}")


class BalenaSupervisorStateCoordinator(DataUpdateCoordinator[BalenaAppState]):
    """Class to buffer current state in type of BalenaAppState."""

    _DEFAULT_UPDATE_INTERVAL = timedelta(minutes=5)
    _BURST_UPDATE_INTERVAL = timedelta(seconds=10)
    _BURST_DURATION = timedelta(seconds=90)

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: BalenaSupervisorApiClient,
    ) -> None:
        """Initialize State Coordinator."""
        super().__init__(
            hass,
            logger=_LOGGER,
            name="balena_supervisor",
            update_interval=self._DEFAULT_UPDATE_INTERVAL,
            config_entry=config_entry,
            update_method=self._async_update_data,
        )
        self.client = client
        self.app_id: int | None = None  # type: int | None
        self._burst_unsub: callable | None = None

    async def _async_update_data(self) -> BalenaAppState:
        try:
            data = await self.client.get_state()
            self.app_id = data["appId"]
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        else:
            return data

    async def post_container_service(
        self, app_id: int, service_name: str, action: str
    ) -> None:
        """Call post_container_service and burst refresh interval for _BURST_DURATION seconds."""
        await self.client.post_container_service(app_id, service_name, action)
        self.start_burst_refresh()

    @callback
    def start_burst_refresh(
        self,
        interval: timedelta = _BURST_UPDATE_INTERVAL,
        duration: timedelta = _BURST_DURATION,
    ) -> None:
        """Temporarily increase refresh rate to every interval for duration."""
        if self._burst_unsub is not None:
            self._burst_unsub()
            self._burst_unsub = None

        self.update_interval = interval
        self.async_update_listeners()  # Notify listeners of interval change

        @callback
        def _restore_interval(now):
            self.update_interval = self._DEFAULT_UPDATE_INTERVAL
            self._burst_unsub = None

        self._burst_unsub = async_call_later(self.hass, duration, _restore_interval)

    @callback
    def get_service_data(self, service_name: str) -> BalenaServiceState | None:
        return self.data["services"].get(service_name, None)
