"""Light for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.light import (
    LightEntity,
    LightEntityDescription,
    ColorMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)

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
        entities.append(YotoSensor(coordinator, player))
    async_add_entities(entities)
    return True


class YotoSensor(LightEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: LightEntityDescription, player: YotoPlayer
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
        self._attr_entity_category = self._description.entity_category

    @property
    def color_mode(self):
        """Return the color modes the sensor supports."""
        return ColorMode.RGBW

    @property
    def supported_color_modes(self):
        """Return the unit the value was reported in by the sensor"""

        return self._description.native_unit_of_measurement
