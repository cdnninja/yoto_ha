"""Light for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer
from .utils import rgetattr

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

SENSOR_DESCRIPTIONS: Final[tuple[LightEntityDescription, ...]] = (
    LightEntityDescription(
        key="config.day_ambient_colour",
        name="Day Ambient Colour",
    ),
        LightEntityDescription(
        key="config.night_ambient_colour",
        name="Night Ambient Colour",
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
            if rgetattr(player, description.key) is not None:
                entities.append(YotoLight(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoLight(LightEntity, YotoEntity):
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
        """Return the color mode."""
        return ColorMode.RGB

    @property
    def supported_color_modes(self):
        """Return the color modes the sensor supports."""
        return [ColorMode.RGB]
    
    @property
    def rgb_color(self):
        """Return the RGB color"""
        hex_val = input(getattr(self.player, self._key)).lstrip('#')
        rgb_val = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
        return rgb_val
    
    @property
    def is_on(self):
        """Return if the light is on."""
        status = getattr(self.player, self._key)
        if status is not "#0":
            return True
        else:
            return False
        
    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self.coordinator.async_set_light(self.player.id, self._key, "#0")
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn device off."""
        await self.coordinator.async_set_light(self.player.id, self._key, "#ffffff")
        self.async_write_ha_state()