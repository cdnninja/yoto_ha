"""Sensor for Yoto integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import YotoPlayer

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class YotoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes custom binary sensor entities."""

    is_on: Callable[[YotoPlayer], bool] | None = None


SENSOR_DESCRIPTIONS: Final[tuple[YotoBinarySensorEntityDescription, ...]] = (
    YotoBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        is_on=lambda player: player.online,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="day_mode_on",
        translation_key="day_mode_on",
        is_on=lambda player: player.day_mode_on,
    ),
    YotoBinarySensorEntityDescription(
        key="bluetooth_audio_connected",
        translation_key="bluetooth_audio_connected",
        is_on=lambda player: player.bluetooth_audio_connected,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        is_on=lambda player: player.charging,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    YotoBinarySensorEntityDescription(
        key="audio_device_connected",
        translation_key="audio_device_connected",
        is_on=lambda player: player.audio_device_connected,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="sleep_timer_active",
        translation_key="sleep_timer_active",
        is_on=lambda player: player.sleep_timer_active,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    YotoBinarySensorEntityDescription(
        key="night_light_mode",
        translation_key="night_light_mode",
        is_on=lambda player: player.night_light_mode != "off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary_sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.unique_id]
    entities: list[YotoBinarySensor] = []
    for player_id in coordinator.yoto_manager.players.keys():
        player: YotoPlayer = coordinator.yoto_manager.players[player_id]
        for description in SENSOR_DESCRIPTIONS:
            if getattr(player, description.key, None) is not None:
                entities.append(YotoBinarySensor(coordinator, description, player))
    async_add_entities(entities)


class YotoBinarySensor(BinarySensorEntity, YotoEntity):
    """Yoto binary sensor class."""

    def __init__(
        self,
        coordinator: YotoDataUpdateCoordinator,
        description: YotoBinarySensorEntityDescription,
        player: YotoPlayer,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self._description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{self._description.key}"
        self._attr_device_class = self._description.device_class
        self._attr_entity_category = self._description.entity_category
        self._attr_translation_key = self._description.translation_key

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self._description.is_on is not None:
            return self._description.is_on(self.player)
        return None
