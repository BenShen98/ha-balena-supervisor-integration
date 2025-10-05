"""Sensor platform for Balena Docker containers."""

from collections.abc import Callable, Coroutine, Iterable, Mapping
import os
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
    AddEntitiesCallback,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import DOMAIN, DATA_BALENA
from .coordinator import BalenaSupervisorStateCoordinator
from .types import BalenaDockerConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: BalenaDockerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> bool:
    """Set up the sensors defined below."""
    coordinator = config_entry.runtime_data.state_coordinator
    self_service_name = os.getenv("BALENA_SERVICE_NAME", None)

    entities = []
    for service_name in coordinator.data["services"]:
        allow_control_service = True
        if (
            config_entry.data.get("disable_self_control")
            and self_service_name == service_name
        ):
            allow_control_service = False
        entity = BalenaContainerEntity(service_name, coordinator, allow_control_service)
        entities.append(entity)
    async_add_entities(entities)

    hass.data[DATA_BALENA].add_entities(entities)

    return True


class BalenaBaseEntity(SensorEntity):
    """Base entity for Balena Docker containers."""

    _attr_has_entity_name = True
    coordinator: BalenaSupervisorStateCoordinator = None

    def __init__(self) -> None:
        """Initialize a Balena Docker base entity."""
        self._attr_should_poll = False
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = [
            "Running",
            "Stopping",
            "Exited",
            "Installing",
        ]

    @property
    def balena_app_id(self) -> int | None:
        """Return the Balena application ID."""
        return self.coordinator.app_id

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        Copied from homeassistant.helpers.update_coordinator.CoordinatorEntity
        to avoid mutiple inheritance (a bit more readable).
        """
        # Ignore manual update requests if the entity is disabled
        if not self.enabled:
            return

        await self.coordinator.async_request_refresh()


class BalenaContainerEntity(BalenaBaseEntity):
    """Entity representing a Balena Docker container."""

    def __init__(
        self,
        service_name: str,
        state_coordinator: BalenaSupervisorStateCoordinator,
        allow_control_service: bool,
    ) -> None:
        """Initialize a Balena Docker container entity."""
        super().__init__()
        self.service_name = service_name
        self.entity_id = f"{DOMAIN}.{service_name}"
        self._attr_unique_id = f"{DOMAIN}_{service_name}"
        self.coordinator = state_coordinator
        self._allow_control_service = allow_control_service

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.get_service_data(self.service_name)
        )

    @property
    def native_value(self) -> str | None:
        """Return the state of the container."""
        service_data = self.coordinator.get_service_data(self.service_name)
        return service_data["status"] if service_data else None

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        if service_data := self.coordinator.get_service_data(self.service_name):
            return {
                "release_id": service_data["releaseId"],
                "download_progress": service_data["downloadProgress"],
                "custom_ui_more_info": "more-info-balena_docker",
                "icon": "mdi:play-circle-outline"
                if service_data["status"] == "Running"
                else "mdi:stop-circle-outline",
            }

        return None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        # For HA to display the state immediately after update, async_write_ha_state need to be called
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_control_service(self, action: str) -> None:
        """Control the container service (start, stop, restart)."""

        if not self._allow_control_service:
            raise PermissionError(f"{self.service_name} can not be controlled")

        await self.coordinator.client.post_container_service(
            app_id=self.balena_app_id, service_name=self.service_name, action=action
        )
        await self.coordinator.async_refresh()  # Refresh state after command


class BelaneDeviceEntity(BalenaBaseEntity):
    """Entity representing the Balena device itself."""

    def __init__(self, state_coordinator: BalenaSupervisorStateCoordinator) -> None:
        """Initialize a Balena Docker device entity."""
        self.entity_id = f"{DOMAIN}.device"
        self._attr_unique_id = f"{DOMAIN}_device"
        self.coordinator = state_coordinator

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str | None:
        """Return the state of the device."""
        return "online" if self.coordinator.last_update_success else "offline"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return the state attributes."""
        if self.coordinator.data:
            return {
                "app_id": self.coordinator.data["appId"],
                "app_name": self.coordinator.data["appName"],
                "commit": self.coordinator.data["commit"],
                "custom_ui_more_info": "more-info-balena_docker-device",
                "icon": "mdi:chip",
            }

        return None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        # For HA to display the state immediately after update, async_write_ha_state need to be called
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
