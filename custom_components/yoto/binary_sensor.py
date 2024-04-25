"""Sensor for Yoto integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Final

from yoto_api import YotoPlayer

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from .const import DOMAIN
from .coordinator import YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class YotoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes custom binary sensor entities."""

    is_on: Callable[[YotoPlayer], bool] | None = None
    on_icon: str | None = None
    off_icon: str | None = None


SENSOR_DESCRIPTIONS: Final[tuple[YotoBinarySensorEntityDescription, ...]] = (
    YotoBinarySensorEntityDescription(
        key="online",
        name="Online",
        is_on=lambda player: player.online,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="day_mode_on",
        name="Day Mode",
        is_on=lambda player: player.day_mode_on,
    ),
    YotoBinarySensorEntityDescription(
        key="bluetooth_audio_connected",
        name="Bluetooth Audio Connected",
        is_on=lambda player: player.bluetooth_audio_connected,
        on_icon="mdi:headphones-bluetooth",
        off_icon="mdi:bluetooth-off",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="charging",
        name="Charging",
        is_on=lambda player: player.charging,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    YotoBinarySensorEntityDescription(
        key="audio_device_connected",
        name="Audio Device Connected",
        is_on=lambda player: player.audio_device_connected,
        on_icon="mdi:headphones",
        off_icon="mdi:headphones-off",
        entity_category=EntityCategory.DIAGNOSTIC,
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
    return True


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
        self._attr_name = f"{player.name} {self._description.name}"
        self._attr_entity_category = self._description.entity_category

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self._description.is_on is not None:
            return self._description.is_on(self.player)
        return None

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if (self._description.on_icon == self._description.off_icon) is None:
            return BinarySensorEntity.icon
        return self._description.on_icon if self.is_on else self._description.off_icon
