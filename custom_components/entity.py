"""Base entity for Balena Docker containers."""

from homeassistant.helpers.entity import Entity


class BalenaDockerBaseEntity(Entity):
    """Base entity for Balena Docker containers."""

    _attr_has_entity_name = True
