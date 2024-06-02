"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.number import (
    SwitchEntity,
    SwitchEntityDescription,
)


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: Final[tuple[SwitchEntityDescription, ...]] = (
    SwitchEntityDescription(
        key="night_display_brightness",
        name="Night Auto Display Brightness",
    ),
    SwitchEntityDescription(
        key="day_display_brightness",
        name="Day Auto Display Brightness",
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
            if getattr(player.config, description.key, None) is not None:
                entities.append(YotoSwitch(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoSwitch(SwitchEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: SwitchEntityDescription, player: YotoPlayer
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._key}"
        self._attr_icon = self._description.icon
        self._attr_name = f"{player.name} {self._description.name}"

    @property
    def is_on(self) -> bool | None:
        """Return the entity value to represent the entity state."""
        if getattr(self.player.config, self._key) == "auto":
            return True
        else:
            return False
    
    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity off."""
        await self.coordinator.async_set_brightness(
                self.player.id, self._key, "auto"
            )
        self.async_write_ha_state()
