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
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from yoto_api import DayMode, YotoPlayer, caps_for

from .const import DOMAIN
from .coordinator import YotoConfigEntry, YotoDataUpdateCoordinator
from .entity import YotoEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class YotoBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes custom binary sensor entities."""

    value: Callable[[YotoPlayer], bool | None] | None = None
    requires_ambient_light: bool = False


def _day_mode_on(player: YotoPlayer) -> bool | None:
    day_mode = player.status.day_mode
    if day_mode is None or day_mode == DayMode.UNKNOWN:
        return None
    return day_mode == DayMode.DAY


def _night_light_on(player: YotoPlayer) -> bool | None:
    mode = player.status.nightlight_mode
    return None if mode is None else mode != "off"


SENSOR_DESCRIPTIONS: Final[tuple[YotoBinarySensorEntityDescription, ...]] = (
    YotoBinarySensorEntityDescription(
        key="online",
        translation_key="online",
        value=lambda player: player.status.is_online,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="day_mode_on",
        translation_key="day_mode_on",
        value=_day_mode_on,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="bluetooth_audio_connected",
        translation_key="bluetooth_audio_connected",
        value=lambda player: player.status.is_bluetooth_audio_connected,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        value=lambda player: player.status.is_charging,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="audio_device_connected",
        translation_key="audio_device_connected",
        value=lambda player: player.status.is_audio_device_connected,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="sleep_timer_active",
        translation_key="sleep_timer_active",
        value=lambda player: bool(player.last_event.sleep_timer_active),
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    YotoBinarySensorEntityDescription(
        key="night_light_mode",
        translation_key="night_light_mode",
        value=_night_light_on,
        requires_ambient_light=True,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: YotoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary_sensor platform."""
    coordinator = config_entry.runtime_data
    entities: list[YotoBinarySensor] = []
    for player_id in coordinator.yoto_client.players.keys():
        player: YotoPlayer = coordinator.yoto_client.players[player_id]
        caps = caps_for(player.device)
        for description in SENSOR_DESCRIPTIONS:
            if description.requires_ambient_light and not caps.has_ambient_light:
                continue
            if description.value is not None and description.value(player) is not None:
                entities.append(YotoBinarySensor(coordinator, description, player))
    async_add_entities(entities)


class YotoBinarySensor(BinarySensorEntity, YotoEntity):
    """Yoto binary sensor class."""

    entity_description: YotoBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: YotoDataUpdateCoordinator,
        description: YotoBinarySensorEntityDescription,
        player: YotoPlayer,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, player)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{player.id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        value = self.entity_description.value
        return value(self.player) if value is not None else None
