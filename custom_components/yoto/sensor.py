"""Sensor for Yoto integration."""
from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: Final[tuple[SensorEntityDescription, ...]] = (
    SensorEntityDescription(
        key="last_updated_at",
        name="Last Updated At",
        icon="mdi:update",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in SENSOR_DESCRIPTIONS:
            if getattr(player, description.key, None) is not None:
                entities.append(
                    YotoSensor(coordinator, description, player)
                )
        entities.append(
            YotoEntity(coordinator, coordinator.yoto_manager.players[player_id])
        )
    async_add_entities(entities)
    return True


class YotoSensor(SensorEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: SensorEntityDescription, player: YotoPlayer
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._key}"
        self._attr_icon = self._description.icon
        self._attr_name = f"{player.name} {self._description.name}"
        self._attr_state_class = self._description.state_class
        self._attr_device_class = self._description.device_class

    @property
    def native_value(self):
        """Return the value reported by the sensor."""
        return getattr(self.player, self._key)
