"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)

from homeassistant.const import PERCENTAGE


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import DOMAIN
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS: Final[tuple[NumberEntityDescription, ...]] = (
    NumberEntityDescription(
        key="night_max_volume_limit",
        name="Night Max Volume",
        native_min_value=0,
        native_max_value=16,
        native_step=1,
    ),
    NumberEntityDescription(
        key="day_max_volume_limit",
        name="Day Max Volume",
        native_min_value=0,
        native_max_value=16,
        native_step=1,
    ),
    NumberEntityDescription(
        key="day_display_brightness",
        name="Day Display Brightness",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
    ),
    NumberEntityDescription(
        key="night_display_brightness",
        name="Day Display Brightness",
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
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
                entities.append(YotoNumber(coordinator, description, player))
    async_add_entities(entities)
    return True


class YotoNumber(NumberEntity, YotoEntity):
    """Yoto sensor class."""

    def __init__(
        self, coordinator, description: NumberEntityDescription, player: YotoPlayer
    ):
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._key = self._description.key
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._key}"
        self._attr_icon = self._description.icon
        self._attr_name = f"{player.name} {self._description.name}"
        self._attr_mode = NumberMode.SLIDER
        self._attr_device_class = self._description.device_class

    @property
    def native_value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        return getattr(self.player.config, self._key)

    @property
    def native_min_value(self):
        """Return native_min_value as reported in by the sensor"""
        return self._description.native_min_value

    @property
    def native_max_value(self):
        """Returnnative_max_value as reported in by the sensor"""
        return self._description.native_max_value

    @property
    def native_step(self):
        """Return step value as reported in by the sensor"""
        return self._description.native_step

    @property
    def native_unit_of_measurement(self):
        """Return the unit the value was reported in by the sensor"""

        return self._description.native_unit_of_measurement

    async def async_set_native_value(self, value: float) -> None:
        if self._key == "day_max_volume_limit" or self._key == "day_max_volume_limit":
            await self.coordinator.async_set_max_volume(self.player.id, self._key, value)
        if self._key == "day_display_brightness" or self._key == "night_display_brightness":
            await self.coordinator.async_set_brightness(self.player.id, self._key, value)
        self.async_write_ha_state()
